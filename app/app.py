import json
import os
import uuid
import threading
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from app.backend.prompt_manager import PromptManager
from app.backend.agent import code_assistant

app = Flask(__name__)
prompt_manager = PromptManager()
os.makedirs("db", exist_ok=True)

# Armazena streams ativos: {session_id: queue}
STREAMS = {}
STREAMS_LOCK = threading.Lock()

# Rotas de prompts (GET / POST / DELETE)
@app.route('/prompts', methods=['GET', 'POST', 'DELETE'])
def handle_prompts():
    if request.method == 'GET':
        return jsonify(prompt_manager.get_all_prompts())

    if request.method == 'POST':
        data = request.get_json()
        text = data.get('text', '').strip()
        if text and prompt_manager.add_prompt(text):
            return jsonify(success=True)
        return jsonify(success=False), 400

    if request.method == 'DELETE':
        data = request.get_json()
        text = data.get('text', '').strip()
        if prompt_manager.delete_prompt(text):
            return jsonify(success=True)
        return jsonify(success=False), 400

# Recebe o prompt -- cria sessão -- devolve session_id
@app.route('/chat', methods=['POST'])
def chat_start():
    data = request.get_json()
    prompt = data.get('prompt', '').strip()
    if not prompt:
        return jsonify(error="Prompt vazio"), 400

    session_id = str(uuid.uuid4())
    with STREAMS_LOCK:
        STREAMS[session_id] = [] # lista que vai receber os chunks

    # Executa o agente em background
    def run_agent():
        try:
            # CORREÇÃO: usar .run(..., stream=True)
            for chunk in code_assistant.run(prompt, stream=True, show_tool_calls=True):
                if hasattr(chunk, 'content') and chunk.content:
                    with STREAMS_LOCK:
                        STREAMS[session_id].append(chunk.content)
        except Exception as e:
            with STREAMS_LOCK:
                STREAMS[session_id].append(f"\n\n**Erro:** {e}")
        finally:
            with STREAMS_LOCK:
                STREAMS[session_id].append("<END>")

    threading.Thread(target=run_agent, daemon=True).start()

    return jsonify(session_id=session_id)

# SSE – entrega os chunks já gerados
@app.route('/stream/<session_id>')
def stream(session_id):
    def generate():
        buffer = ""
        while True:
            with STREAMS_LOCK:
                if session_id not in STREAMS:
                    yield "data: {\"error\":\"Sessão expirada\"}\n\n"
                    break
                chunks = STREAMS[session_id][:]
                STREAMS[session_id].clear()

            # envia tudo que já chegou
            for c in chunks:
                if c == "<END>":
                    yield "data: <END>\n\n"
                    with STREAMS_LOCK:
                        STREAMS.pop(session_id, None)
                    return
                buffer += c
                # envia em pedaços pequenos para a animação fluir
                while len(buffer) >= 3:
                    yield f"data: {json.dumps({'content': buffer[:3]})}\n\n"
                    buffer = buffer[3:]

            # se ainda não acabou, espera um pouquinho
            if "<END>" not in chunks:
                import time
                time.sleep(0.05)

        # caso saia do loop sem <END>
        if buffer:
            yield f"data: {json.dumps({'content': buffer})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

# Pagina Principal
@app.route('/')
def index():
    return render_template('index.html', initial_prompts=prompt_manager.get_all_prompts())

if __name__ == '__main__':
    app.run(debug=True)