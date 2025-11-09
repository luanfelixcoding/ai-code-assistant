import customtkinter
import threading
import queue

from customtkinter import CTkInputDialog
from core.agent import code_assistant
from app.prompt_manager import PromptManager

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Assistente de Código Python (IA)")
        self.root.geometry("900x750")

        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("green")

        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1) # Frame do chat
        self.root.grid_rowconfigure(1, weight=0) # Opções
        self.root.grid_rowconfigure(2, weight=0) # Biblioteca de Prompts
        self.root.grid_rowconfigure(3, weight=0) # Entrada

        # Atribui o agente à classe
        self.code_assistant = code_assistant 
        self.prompt_manager = PromptManager()

        # Frame principal do chat
        self.chat_frame = customtkinter.CTkScrollableFrame(root, corner_radius=0)
        self.chat_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 5))
        self.chat_frame.grid_columnconfigure(0, weight=1)

        # Frame de opções/configurações
        self.options_frame = customtkinter.CTkFrame(root, height=40, corner_radius=0)
        self.options_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.options_frame.grid_columnconfigure(1, weight=1) # Coluna do menu expande

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

        # --- Botão de Prompts Rápidos ---
        self.prompt_toggle_button = customtkinter.CTkButton(
            self.options_frame,
            text="🚀 Prompts Rápidos",
            font=("Arial", 13, "bold"),
            width=150,
            command=self.toggle_prompt_library
        )
        self.prompt_toggle_button.grid(row=0, column=2, sticky="e", padx=(10, 10), pady=5)

        # --- Frame da Biblioteca de Prompts (Inicia escondido) ---
        self.prompt_library_visible = False
        self.prompt_library_target_height = 180 # Altura máxima do painel
        
        self.prompt_library_frame = customtkinter.CTkFrame(root, height=0, corner_radius=5)
        self.prompt_library_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=0)
        self.prompt_library_frame.grid_remove() # Começa escondido
        self.prompt_library_frame.grid_propagate(False) # Impede que os widgets controlem o tamanho
        
        self.prompt_library_frame.grid_columnconfigure(0, weight=1)
        self.prompt_library_frame.grid_rowconfigure(0, weight=1)

        # Frame rolável para a lista de prompts
        self.prompts_list_frame = customtkinter.CTkScrollableFrame(self.prompt_library_frame, fg_color="transparent")
        self.prompts_list_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=(5,0))

        # Botão para adicionar novo prompt
        self.add_prompt_button = customtkinter.CTkButton(
            self.prompt_library_frame,
            text="✚ Adicionar Novo Prompt",
            font=("Arial", 13),
            command=self.open_add_prompt_dialog
        )
        self.add_prompt_button.grid(row=1, column=0, sticky="ew", padx=10, pady=10)

        # Listas para guardar os prompts e seus widgets
        self.prompt_list = [] # Será preenchido pelo _load_prompts_from_db
        self.prompt_widgets = []


        # Frame de entrada (Movido para row=3)
        self.input_frame = customtkinter.CTkFrame(root, height=60, corner_radius=0)
        self.input_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=(5, 10))
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

        # Fila para comunicação entre threads
        self.response_queue = queue.Queue()
        
        self.loading_label = None
        self.loading_animation_id = None
        
        # Mensagem de boas-vindas atualizada
        self.add_message_bubble("💻 Assistente", "Olá! Eu sou seu assistente de código Python. Use o botão '🚀 Prompts Rápidos' para salvar e usar seus comandos favoritos.", is_user=False)
        
        # Carrega prompts iniciais (agora vindo do DB)
        self._load_prompts()
        
    # --- Métodos da Biblioteca de Prompts (COM BANCO DE DADOS) ---
    def _load_prompts(self):
        """Carrega prompts usando o PromptManager."""
        self.prompt_list = self.prompt_manager.get_all_prompts()
        self.refresh_prompt_list()
        
    def open_add_prompt_dialog(self):
        """Adiciona um prompt usando o PromptManager."""
        dialog = CTkInputDialog(text="...", title="...")
        prompt_text = dialog.get_input()
        
        if prompt_text and prompt_text.strip():
            prompt_text = prompt_text.strip()
            if self.prompt_manager.add_prompt(prompt_text):
                self.prompt_list.append(prompt_text)
                self.refresh_prompt_list()
            else:
                print("Falha ao adicionar, talvez já exista.")
    
    def delete_prompt(self, prompt_text):
        """Deleta um prompt usando o PromptManager."""
        if prompt_text in self.prompt_list:
            if self.prompt_manager.delete_prompt(prompt_text):
                self.prompt_list.remove(prompt_text)
                self.refresh_prompt_list()
            else:
                print("Falha ao deletar do DB.")

    def toggle_prompt_library(self):
        """Inicia a animação para abrir ou fechar o painel de prompts."""
        self.prompt_toggle_button.configure(state="disabled") # Desabilita durante a animação
        
        if self.prompt_library_visible:
            # Fechar
            self.prompt_toggle_button.configure(text="🚀 Prompts Rápidos")
            self.animate_prompt_library(opening=False)
        else:
            # Abrir
            self.prompt_toggle_button.configure(text="🔼 Fechar Prompts")
            self.prompt_library_frame.grid() # Mostra o frame antes de animar
            self.animate_prompt_library(opening=True)
            
        self.prompt_library_visible = not self.prompt_library_visible

    def animate_prompt_library(self, opening: bool, current_height=None):
        """Executa a animação suave de 'deslizar' (mudança de altura)."""
        animation_speed_ms = 15 # Tempo entre frames
        steps = 15 # Total de passos da animação
        step_height = self.prompt_library_target_height / steps

        if opening:
            if current_height is None:
                current_height = 0
            
            new_height = current_height + step_height
            if new_height >= self.prompt_library_target_height:
                self.prompt_library_frame.configure(height=self.prompt_library_target_height)
                self.prompt_toggle_button.configure(state="normal") # Reabilita o botão
                return
        else:
            if current_height is None:
                current_height = self.prompt_library_target_height
            
            new_height = current_height - step_height
            if new_height <= 0:
                self.prompt_library_frame.configure(height=0)
                self.prompt_library_frame.grid_remove() # Esconde o frame
                self.prompt_toggle_button.configure(state="normal") # Reabilita o botão
                return
        
        self.prompt_library_frame.configure(height=new_height)
        self.root.after(
            animation_speed_ms, 
            lambda: self.animate_prompt_library(opening, new_height)
        )

    def load_initial_prompts(self):
        """Este método foi substituído por _load_prompts_from_db()"""
        # Este método agora é obsoleto, a lógica está em _load_prompts_from_db
        print("Aviso: load_initial_prompts() não é mais usado.")
        pass

    def refresh_prompt_list(self):
        """Limpa e recria a lista de botões de prompt no painel rolável."""
        # Limpa widgets antigos
        for widget in self.prompt_widgets:
            widget.destroy()
        self.prompt_widgets = []

        # Cria novos widgets
        for i, prompt_text in enumerate(self.prompt_list):
            prompt_frame = customtkinter.CTkFrame(self.prompts_list_frame, fg_color=("#dbdbdb", "#2b2b2b"))
            prompt_frame.pack(fill="x", pady=4, padx=5)
            prompt_frame.grid_columnconfigure(0, weight=1)

            # Label com o texto do prompt
            label = customtkinter.CTkLabel(
                prompt_frame,
                text=prompt_text,
                font=("Arial", 13),
                anchor="w",
                justify="left"
            )
            label.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
            
            # Botão "Usar"
            use_button = customtkinter.CTkButton(
                prompt_frame,
                text="Usar",
                width=60,
                font=("Arial", 12, "bold"),
                command=lambda p=prompt_text: self.use_prompt(p)
            )
            use_button.grid(row=0, column=1, sticky="e", padx=(5, 5), pady=5)

            # Botão "Excluir"
            del_button = customtkinter.CTkButton(
                prompt_frame,
                text="X",
                width=30,
                fg_color=("#F08080", "#8B0000"), # Cor de perigo
                hover_color=("#CD5C5C", "#DC143C"),
                command=lambda p=prompt_text: self.delete_prompt(p)
            )
            del_button.grid(row=0, column=2, sticky="e", padx=(0, 5), pady=5)
            
            self.prompt_widgets.append(prompt_frame)
        # ---------------------------------

    def use_prompt(self, prompt_text):
        """Cola o prompt selecionado na caixa de entrada e fecha o painel."""
        self.prompt_entry.delete(0, "end")
        self.prompt_entry.insert(0, prompt_text + " ") # Adiciona espaço
        self.prompt_entry.focus()
        
        if self.prompt_library_visible:
            self.toggle_prompt_library()

    # --- Métodos Originais do Chat (com ajustes de altura) ---

    def send_message_event(self, event=None):
        """Pega o texto da entrada, inicia o processo de envio e limpa a caixa."""
        prompt = self.prompt_entry.get().strip()
        if not prompt:
            return

        self.add_message_bubble("Você", prompt, is_user=True)
        self.prompt_entry.delete(0, "end")

        self.prompt_entry.configure(state="disabled")
        self.send_button.configure(state="disabled")

        self.start_loading_animation()

        threading.Thread(
            target=self.run_agent_in_thread, 
            args=(prompt,), 
            daemon=True
        ).start()

        self.root.after(100, self.check_response_queue)

    def run_agent_in_thread(self, prompt):
        """Função que roda o agente em background e coloca a resposta na fila."""
        try:
            response = self.code_assistant.run(prompt, show_tool_calls=True)
            self.response_queue.put(response.content)
        except Exception as e:
            self.response_queue.put(f"Ocorreu um erro no agente: {e}")

    def check_response_queue(self):
        """Verifica a fila de resposta. Se vazia, agenda nova verificação. Se cheia, processa a resposta."""
        try:
            response_content = self.response_queue.get_nowait()
            
            self.stop_loading_animation()
            self.display_bot_response_animated(response_content)
            
        except queue.Empty:
            self.root.after(100, self.check_response_queue)

    def add_message_bubble(self, user, text, is_user=False):
        """Cria e adiciona uma "bolha" de mensagem ao chat frame."""
        
        if is_user:
            anchor = "e"
            color = "transparent"
            text_color = "#E0E0E0"
            user_color = "#5DADE2"
        else:
            anchor = "w"
            color = "#2B2B2B"
            text_color = "#FFFFFF"
            user_color = "#58D68D"

        bubble_frame = customtkinter.CTkFrame(
            self.chat_frame, 
            fg_color=color,
            border_width=1 if is_user else 0,
            border_color="#444444"
        )
        
        user_label = customtkinter.CTkLabel(
            bubble_frame, 
            text=user, 
            font=("Arial", 13, "bold"),
            text_color=user_color
        )
        user_label.pack(anchor="w", padx=10, pady=(5, 0))

        message_box = customtkinter.CTkTextbox(
            bubble_frame,
            font=("Arial", 14),
            wrap="word",
            # activate_scrollbars=False, # <-- REMOVIDA LINHA COM ERRO
            fg_color="transparent",
            text_color=text_color
        )
        message_box.insert("1.0", text)
        message_box.configure(state="disabled")
        
        message_box.pack(anchor="w", fill="x", padx=10, pady=(0, 10))
        
        self.root.update_idletasks()
        
        # --- Cálculo de altura aprimorado ---
        message_box.update_idletasks()
        lines = int(message_box.index("end-1c").split('.')[0])
        
        # --- CORREÇÃO ---
        # O .cget("font") retorna a tupla/string, não o objeto CTkFont.
        # Precisamos criar um objeto CTkFont para obter as métricas.
        font_data = message_box.cget("font")
        if isinstance(font_data, customtkinter.CTkFont):
            font = font_data
        else:
            # font_data é provavelmente uma tupla como ("Arial", 14)
            font = customtkinter.CTkFont(family=font_data[0], size=font_data[1])

        line_height = font.metrics("linespace") 
        # --- FIM DA CORREÇÃO ---
        
        padding_vertical = 20
        min_height = line_height + padding_vertical
        calculated_height = (lines * line_height) + padding_vertical
        
        max_height = 500 
        final_height = min(max(min_height, calculated_height), max_height)
        
        message_box.configure(height=final_height)
        
        # if calculated_height > max_height:
        #      message_box.configure(activate_scrollbars=True) # <-- REMOVIDA LINHA COM ERRO
        # -------------------------------------

        bubble_frame.pack(fill="x", padx=10, pady=5, anchor=anchor)
        
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
        bubble_frame = customtkinter.CTkFrame(self.chat_frame, fg_color="#2B2B2B")
        
        user_label = customtkinter.CTkLabel(
            bubble_frame, text="🤖 Assistente", 
            font=("Arial", 13, "bold"), text_color="#58D68D"
        )
        user_label.pack(anchor="w", padx=10, pady=(5, 0))

        message_box = customtkinter.CTkTextbox(
            bubble_frame,
            font=("Arial", 14),
            wrap="word",
            # activate_scrollbars=False, # <-- REMOVIDA LINHA COM ERRO
            fg_color="transparent",
            text_color="#FFFFFF",
            height=30 # Altura inicial mínima
        )
        message_box.pack(anchor="w", fill="x", padx=10, pady=(0, 10))
        message_box.configure(state="disabled")

        bubble_frame.pack(fill="x", padx=10, pady=5, anchor="w")

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
        
        chunk_size = 3
        chunk = full_text[index : index + chunk_size]

        if chunk:
            text_widget.configure(state="normal")
            text_widget.insert("end", chunk)
            text_widget.configure(state="disabled")
            
            # Reajusta a altura dinamicamente durante a digitação
            text_widget.update_idletasks()
            lines = int(text_widget.index("end-1c").split('.')[0])
            
            # --- CORREÇÃO ---
            font_data = text_widget.cget("font")
            if isinstance(font_data, customtkinter.CTkFont):
                font = font_data
            else:
                font = customtkinter.CTkFont(family=font_data[0], size=font_data[1])
                
            line_height = font.metrics("linespace")
            # --- FIM DA CORREÇÃO ---

            padding_vertical = 20
            min_height = line_height + padding_vertical
            calculated_height = (lines * line_height) + padding_vertical
            
            max_height = 500
            final_height = min(max(min_height, calculated_height), max_height)
            
            text_widget.configure(height=final_height)
            
            # if calculated_height > max_height:
            #     text_widget.configure(activate_scrollbars=True) # <-- REMOVIDA LINHA COM ERRO

            self._scroll_to_bottom()
            
            self.root.after(
                15, # Velocidade de digitação (15ms)
                self.type_out_chunk, 
                text_widget, 
                frame_widget, 
                full_text, 
                index + chunk_size
            )
        else:
            self.prompt_entry.configure(state="normal")
            self.send_button.configure(state="normal")
            self.prompt_entry.focus()

    def _scroll_to_bottom(self):
        """Força o CTKScrollableFrame a rolar para o final."""
        self.root.update_idletasks() # Garante que a UI está atualizada
        self.chat_frame._parent_canvas.yview_moveto(1.0)