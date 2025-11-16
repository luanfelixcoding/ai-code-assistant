import json
import os
import uuid
import threading
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from backend.prompt_manager import PromptManager
from backend.agent import code_assistant
from werkzeug.utils import secure_filename

app = Flask(__name__)
prompt_manager = PromptManager()
os.makedirs("db", exist_ok=True)

# Configurações
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024  # 1MB max
ALLOWED_EXTENSIONS = {'py'}

# Função auxiliar
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Armazena streams ativos
STREAMS = {}
STREAMS_LOCK = threading.Lock()


# ==================== ROTAS DE PROMPTS ====================
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


# ==================== INÍCIO DO CHAT (com arquivo) ====================
@app.route('/chat', methods=['POST'])
def chat_start():
    prompt = request.form.get('prompt', '').strip()
    if not prompt:
        return jsonify(error="Prompt vazio"), 400

    file_content = ""
    file_name = ""

    # --- PRIORIDADE 1: file_content (enviado pelo frontend) ---
    if 'file_content' in request.form:
        file_content = request.form.get('file_content', '').strip()
        file_name = request.form.get('file_name', 'arquivo.py')
        if file_content:
            file_name = secure_filename(file_name)
            file_content = f"Aqui está o código do arquivo anexado '{file_name}':\n```python\n{file_content}\n```"

    # --- PRIORIDADE 2: fallback para leitura direta do arquivo binário ---
    elif 'file' in request.files:
        file = request.files['file']
        if file.filename and allowed_file(file.filename):
            try:
                content = file.read().decode('utf-8')
                file_name = secure_filename(file.filename)
                file_content = f"Aqui está o código do arquivo anexado '{file_name}':\n```python\n{content}\n```"
            except UnicodeDecodeError:
                return jsonify(error="Arquivo não é texto válido (deve ser UTF-8)"), 400
            except Exception as e:
                return jsonify(error=f"Erro ao ler arquivo: {str(e)}"), 400
        else:
            return jsonify(error="Arquivo inválido (somente .py permitido)"), 400

    # --- Combina prompt com conteúdo do arquivo (se houver) ---
    full_prompt = f"{file_content}\n\n{prompt}".strip()

    # --- Cria sessão ---
    session_id = str(uuid.uuid4())
    with STREAMS_LOCK:
        STREAMS[session_id] = []

    # --- Executa agente em thread ---
    def run_agent():
        try:
            for chunk in code_assistant.run(full_prompt, stream=True, show_tool_calls=True):
                if hasattr(chunk, 'content') and chunk.content:
                    with STREAMS_LOCK:
                        STREAMS[session_id].append(chunk.content)
        except Exception as e:
            with STREAMS_LOCK:
                STREAMS[session_id].append(f"\n\n**Erro:** {str(e)}")
        finally:
            with STREAMS_LOCK:
                STREAMS[session_id].append("<END>")

    threading.Thread(target=run_agent, daemon=True).start()

    return jsonify(session_id=session_id)


# ==================== STREAMING SSE ====================
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

            for c in chunks:
                if c == "<END>":
                    yield "data: <END>\n\n"
                    with STREAMS_LOCK:
                        STREAMS.pop(session_id, None)
                    return
                buffer += c
                while len(buffer) >= 3:
                    yield f"data: {json.dumps({'content': buffer[:3]})}\n\n"
                    buffer = buffer[3:]

            if "<END>" not in chunks:
                import time
                time.sleep(0.05)

        if buffer:
            yield f"data: {json.dumps({'content': buffer})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')


# ==================== PÁGINA PRINCIPAL ====================
@app.route('/')
def index():
    return render_template('index.html', initial_prompts=prompt_manager.get_all_prompts())


if __name__ == '__main__':
    app.run(debug=True, threaded=True)