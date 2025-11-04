# Importando bibliotecas
import sys
import customtkinter
import threading
import queue
from io import StringIO
from os import getenv
from dotenv import load_dotenv

# Importando Frameworks
from agno.agent import Agent
from agno.tools import Toolkit
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.models.google import Gemini

# Carregando variavéis de ambiente GEMINI_API_KEY e GOOGLE_API_KEY
load_dotenv()


class PythonExecutor(Toolkit):
    """Uma ferramenta para executar código Python e retornar o stdout."""
    name: str = "python_executor"
    description: str = (
        "Use esta ferramenta para executar código Python e testar funções ou snippets. "
        "A entrada é o código Python como uma string. A saída é o resultado do print()."
        "REGRAS: 1. A entrada DEVE ser apenas o código Python dentro de uma string. "
        "2. NUNCA use a ferramenta para código que requer interação do usuário ou GUI."
    )

    def run(self, code: str) -> str:
        """Executa o código Python e captura a saída."""
        # Salva o stdout original para restaurar depois
        old_stdout = sys.stdout
        redirected_output = sys.stdout = StringIO()

        try:
            exec(code)
            output = redirected_output.getvalue()
            
            if not output.strip():
                return "Código executado com sucesso. Nenhuma saída (print) foi gerada."
            
            # Limita a saída para evitar poluir demais a conversa
            max_len = 1000
            if len(output) > max_len:
                 output = output[:max_len] + "\n... (saída truncada)"

            return f"Código executado com sucesso. Saída:\n{output}"
        
        except Exception as e:
            import traceback
            # Pega apenas a última linha do erro para ser mais conciso
            error_message = traceback.format_exc().strip().split('\n')[-1]
            return f"Erro ao executar o código: {error_message}"
        
        finally:
            # Garante que o stdout original seja restaurado
            sys.stdout = old_stdout



if not getenv("GEMINI_API_KEY"):
    print(
        "AVISO: A chave de API GEMINI_API_KEY não foi encontrada. "
        # "Apenas o modelo Ollama estará operacional."
    )

# Inicializando o agente Gemini
code_assistant = Agent(
    name="Code Assistant gemini-2.5-flash",
    model=Gemini(id="gemini-2.5-flash"),
    description="Um assistente de IA especializado em programação python e pesquisa relacionados a programação.",
    instructions=(
        "Você é um assistente de codificação especializado em python e pesquisa relacionados a programação."
        "1. Para perguntas sobre sintaxe, bibliotecas recentes ou informações gerais (que exijam fatos atuais), use a ferramenta `duckduckgo_search` para buscar na web. "
        #"2. **SE O USUÁRIO SOLICITAR UM CÓDIGO OU FUNÇÃO PYTHON, você DEVE usar a ferramenta `python_executor` para testar e validar o código antes de fornecê-lo na resposta final.** "
        "2. Sempre forneça uma resposta completa e bem formatada, justificando o uso da ferramenta, se aplicável."
        "3. Seja conciso em suas respostas, mas completo."
    ),
    tools=[
        PythonExecutor(), 
        DuckDuckGoTools()
    ],
    add_history_to_context=True,
)



class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Assistente de Código Python (IA)")
        self.root.geometry("900x700")

        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("green")

        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # Atribui o agente à classe
        self.code_assistant = code_assistant 

        # Frame principal do chat
        self.chat_frame = customtkinter.CTkScrollableFrame(root, corner_radius=0)
        self.chat_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 5))
        self.chat_frame.grid_columnconfigure(0, weight=1)

        # Frame de opções/configurações (Nova seção)
        self.options_frame = customtkinter.CTkFrame(root, height=40, corner_radius=0)
        self.options_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.options_frame.grid_columnconfigure(1, weight=1)

        # Label do menu
        self.model_label = customtkinter.CTkLabel(
            self.options_frame, 
            text="Modelo:", 
            font=("Arial", 14, "bold")
        )
        self.model_label.grid(row=0, column=0, sticky="w", padx=(10, 5), pady=5)

        # Menu de seleção de modelo
        self.model_choice = customtkinter.CTkOptionMenu(
            self.options_frame, 
            values=["Gemini"],#, "Local (Ollama)"], futuramente ser adicionado
        )
        self.model_choice.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.model_choice.set("Gemini") # Começa com Gemini

        # Frame de entrada
        self.input_frame = customtkinter.CTkFrame(root, height=60, corner_radius=0)
        self.input_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.input_frame.grid_columnconfigure(0, weight=1)
        self.input_frame.grid_columnconfigure(1, weight=0)

        # Caixa de texto para o prompt
        self.prompt_entry = customtkinter.CTkEntry(
            self.input_frame,
            placeholder_text="Digite sua pergunta sobre Python...",
            height=40,
            font=("Arial", 14)
        )
        self.prompt_entry.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        # Vincular a tecla Enter para enviar a mensagem
        self.prompt_entry.bind("<Return>", self.send_message_event)

        # Botão de enviar
        self.send_button = customtkinter.CTkButton(
            self.input_frame,
            text="Enviar",
            command=self.send_message_event,
            width=100,
            height=40,
            font=("Arial", 14, "bold")
        )
        self.send_button.grid(row=0, column=1, sticky="e", padx=(5, 10), pady=10)

        # Fila para comunicação entre threads (GUI e Agente)
        self.response_queue = queue.Queue()
        
        # Variáveis para animação de loading
        self.loading_label = None
        self.loading_animation_id = None
        
        # Adiciona uma mensagem de boas-vindas
        self.add_message_bubble("💻 Assistente", "Olá! Eu sou seu assistente de código Python. Você pode alternar entre Gemini (nuvem) e Local (Ollama) no menu.", is_user=False)

    def send_message_event(self, event=None):
        """Pega o texto da entrada, inicia o processo de envio e limpa a caixa."""
        prompt = self.prompt_entry.get().strip()
        if not prompt:
            return

        # Adiciona a mensagem do usuário à interface
        self.add_message_bubble("Você", prompt, is_user=True)
        self.prompt_entry.delete(0, "end")

        self.prompt_entry.configure(state="disabled")
        self.send_button.configure(state="disabled")

        # Inicia a animação de loading
        self.start_loading_animation()

        # Inicia o agente em uma thread separada para não travar a GUI
        threading.Thread(
            target=self.run_agent_in_thread, 
            args=(prompt,), 
            daemon=True
        ).start()

        # Começa a verificar a fila por uma resposta
        self.root.after(100, self.check_response_queue)

    def run_agent_in_thread(self, prompt):
        """Função que roda o agente em background e coloca a resposta na fila."""
        try:
            response = self.code_assistant.run(prompt, show_tool_calls=True)
            self.response_queue.put(response.content)
        except Exception as e:
            # Em caso de erro, coloque o erro na fila
            self.response_queue.put(f"Ocorreu um erro no agente: {e}")

    def check_response_queue(self):
        """Verifica a fila de resposta. Se vazia, agenda nova verificação. Se cheia, processa a resposta."""
        try:
            response_content = self.response_queue.get_nowait()
            
            # resposta recebida
            self.stop_loading_animation()
            
            # animação "digitação" da resposta do bot
            self.display_bot_response_animated(response_content)
            
        except queue.Empty:
            # verificar novamente em 100ms caso nenhuma resposta ainda
            self.root.after(100, self.check_response_queue)

    def add_message_bubble(self, user, text, is_user=False):
        """Cria e adiciona uma "bolha" de mensagem ao chat frame."""
        
        # Cor e alinhamento da bolha
        if is_user:
            anchor = "e" # Direita
            color = "transparent"
            text_color = "#E0E0E0"
            user_color = "#5DADE2" # Azul claro
        else:
            anchor = "w" # Esquerda
            color = "#2B2B2B" # Cinza escuro
            text_color = "#FFFFFF"
            user_color = "#58D68D" # Verde

        # Frame para a bolha
        bubble_frame = customtkinter.CTkFrame(
            self.chat_frame, 
            fg_color=color,
            border_width=1 if is_user else 0,
            border_color="#444444"
        )
        
        # Label do usuário
        user_label = customtkinter.CTkLabel(
            bubble_frame, 
            text=user, 
            font=("Arial", 13, "bold"),
            text_color=user_color
        )
        user_label.pack(anchor="w", padx=10, pady=(5, 0))

        # Caixa de texto para a mensagem
        message_box = customtkinter.CTkTextbox(
            bubble_frame,
            font=("Arial", 14),
            wrap="word",
            activate_scrollbars=False,
            fg_color="transparent",
            text_color=text_color
        )
        message_box.insert("1.0", text)
        message_box.configure(state="disabled")
        
        # Ajusta a altura da caixa de texto ao conteúdo
        message_box.pack(anchor="w", fill="x", padx=10, pady=(0, 10))
        
        self.root.update_idletasks() # Força a atualização da UI
        num_lines = message_box.index("end-1c").split('.')[0]
        # Define a altura baseada no número de linhas (aprox. 20 pixels por linha + padding)
        message_box.configure(height=(int(num_lines) * 20) + 15)

        bubble_frame.pack(fill="x", padx=10, pady=5, anchor=anchor)
        
        # Scroll automático para o final
        self._scroll_to_bottom()

    def start_loading_animation(self):
        """Cria um label de "Pensando..." e inicia sua animação."""
        if self.loading_label:
            self.loading_label.destroy()
            
        self.loading_label = customtkinter.CTkLabel(
            self.chat_frame, 
            text="🤖 Pensando...", 
            font=("Arial", 14, "italic"),
            text_color="#58D68D"
        )
        self.loading_label.pack(anchor="w", padx=20, pady=10)
        self._scroll_to_bottom()
        self.animate_loading(0)

    def animate_loading(self, dot_count):
        """Função recursiva para animar os pontos de "Pensando..."""
        dots = "." * (dot_count % 4)
        if self.loading_label:
            self.loading_label.configure(text=f"🤖 Pensando{dots}")
            # Agenda a próxima animação
            self.loading_animation_id = self.root.after(400, self.animate_loading, dot_count + 1)

    def stop_loading_animation(self):
        """Para a animação de loading e remove o label."""
        if self.loading_animation_id:
            self.root.after_cancel(self.loading_animation_id)
            self.loading_animation_id = None
        if self.loading_label:
            self.loading_label.destroy()
            self.loading_label = None

    def display_bot_response_animated(self, full_text):
        """Cria a bolha do bot e inicia a animação de "digitação"."""
        # Frame da bolha
        bubble_frame = customtkinter.CTkFrame(self.chat_frame, fg_color="#2B2B2B")
        
        # Label do usuário
        user_label = customtkinter.CTkLabel(
            bubble_frame, text="🤖 Assistente", 
            font=("Arial", 13, "bold"), text_color="#58D68D"
        )
        user_label.pack(anchor="w", padx=10, pady=(5, 0))

        # Caixa de texto para a resposta (inicia vazia)
        message_box = customtkinter.CTkTextbox(
            bubble_frame,
            font=("Arial", 14),
            wrap="word",
            activate_scrollbars=False,
            fg_color="transparent",
            text_color="#FFFFFF"
        )
        message_box.pack(anchor="w", fill="x", padx=10, pady=(0, 10))
        message_box.configure(state="disabled")

        bubble_frame.pack(fill="x", padx=10, pady=5, anchor="w")

        # Inicia a animação de digitação
        self.root.after(
            50, # Inicia após 50ms
            self.type_out_chunk, 
            message_box, 
            bubble_frame,
            full_text, 
            0
        )

    def type_out_chunk(self, text_widget, frame_widget, full_text, index):
        """Função recursiva que "digita" a resposta caractere por caractere."""
        
        # Define quantos caracteres "digitar" por vez (ajuste para velocidade)
        chunk_size = 3
        chunk = full_text[index : index + chunk_size]

        if chunk:
            text_widget.configure(state="normal") # Habilita para inserir
            text_widget.insert("end", chunk)
            text_widget.configure(state="disabled") # Desabilita novamente
            
            # Reajusta a altura da caixa de texto dinamicamente
            self.root.update_idletasks()
            num_lines = text_widget.index("end-1c").split('.')[0]
            # Define a altura baseada no número de linhas (aprox. 20 pixels por linha + padding)
            text_widget.configure(height=(int(num_lines) * 20) + 15)
            
            self._scroll_to_bottom()
            
            # Agenda o próximo chunk
            self.root.after(
                15, # Velocidade de digitação (15ms)
                self.type_out_chunk, 
                text_widget, 
                frame_widget, 
                full_text, 
                index + chunk_size
            )
        else:
            # A digitação terminou reabilita a entrada do usuário
            self.prompt_entry.configure(state="normal")
            self.send_button.configure(state="normal")
            self.prompt_entry.focus() # Coloca o cursor de volta na caixa de entrada

    def _scroll_to_bottom(self):
        """Força o CTKScrollableFrame a rolar para o final."""
        self.root.update_idletasks() # Garante que a UI está atualizada
        self.chat_frame._parent_canvas.yview_moveto(1.0)


# --- Bloco de Execução Principal ---

if __name__ == "__main__":
    app = customtkinter.CTk()
    chat_app = ChatApp(app)
    app.mainloop()