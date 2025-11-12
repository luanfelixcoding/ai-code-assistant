class ChatApp {
  constructor() {
    this.chatContainer = document.getElementById('chat-container');
    this.promptInput = document.getElementById('prompt-input');
    this.sendBtn = document.getElementById('send-btn');
    this.toggleBtn = document.getElementById('toggle-prompts');
    this.promptLibrary = document.getElementById('prompt-library');
    this.promptList = document.getElementById('prompt-list');
    this.addPromptBtn = document.getElementById('add-prompt-direct');
    this.newPromptInput = document.getElementById('new-prompt-input');
    this.themeToggle = document.getElementById('theme-toggle');
    this.currentTheme = localStorage.getItem('theme') || 'dark';

    this.prompts = [];
    this.isLibraryOpen = false;
    this.currentBotMessage = null; // Agora armazena o elemento de loading ou mensagem

    this.init();
  }

  async init() {
    await this.loadPrompts();
    this.renderWelcome();
    this.bindEvents();
    this.applyTheme();
    this.bindThemeToggle();
  }

  bindEvents() {
    this.sendBtn.addEventListener('click', () => this.sendMessage());

    // Enter = enviar, Shift+Enter = nova linha
    this.promptInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });

    this.promptInput.addEventListener('input', () => this.adjustTextareaHeight());

    this.toggleBtn.addEventListener('click', () => this.togglePromptLibrary());
    this.addPromptBtn.addEventListener('click', () => this.addPromptDirect());
    this.newPromptInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        this.addPromptDirect();
      }
    });

    this.adjustTextareaHeight();
  }

  adjustTextareaHeight() {
    const textarea = this.promptInput;
    textarea.style.height = 'auto';
    textarea.style.height = `${textarea.scrollHeight}px`;
  }

  bindThemeToggle() {
    if (this.themeToggle) {
      this.themeToggle.addEventListener('click', () => {
        this.currentTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', this.currentTheme);
        this.applyTheme();
      });
    }
  }

  applyTheme() {
    document.documentElement.setAttribute('data-theme', this.currentTheme);
  }

  async loadPrompts() {
    try {
      const res = await fetch('/prompts');
      if (res.ok) this.prompts = await res.json();
      this.renderPrompts();
    } catch (err) {
      console.error('Erro ao carregar prompts:', err);
    }
  }

  renderWelcome() {
    this.addMessage("Assistente", "Olá! Eu sou seu assistente de código Python. Use o botão 'Prompts Rápidos' para salvar e usar seus comandos favoritos.", false);
  }

  async sendMessage() {
    const prompt = this.promptInput.value.trim();
    if (!prompt) return;

    this.addMessage("Você", prompt, true);
    this.promptInput.value = '';
    this.adjustTextareaHeight();
    this.setInputState(false);

    this.startBotTyping(); // Mostra os 3 pontinhos

    try {
      const startRes = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt })
      });

      if (!startRes.ok) {
        const err = await startRes.json();
        this.appendToBotMessage(`\n\n**Erro:** ${err.error || 'Falha na API'}`);
        this.stopBotTyping();
        this.setInputState(true);
        return;
      }

      const { session_id } = await startRes.json();
      const evtSource = new EventSource(`/stream/${session_id}`);

      evtSource.onmessage = (e) => {
        if (e.data === '<END>') {
          evtSource.close();
          this.stopBotTyping();
          this.setInputState(true);
          return;
        }
        try {
          const data = JSON.parse(e.data);
          if (data.content) {
            this.appendToBotMessage(data.content);
          }
        } catch (_) {}
      };

      evtSource.onerror = () => {
        evtSource.close();
        this.appendToBotMessage("\n\nFalha na conexão com o servidor.");
        this.stopBotTyping();
        this.setInputState(true);
      };

    } catch (err) {
      this.appendToBotMessage("\n\nErro de rede. Verifique sua conexão.");
      this.stopBotTyping();
      this.setInputState(true);
    }
  }

  // Animacao Pensando (3 pontinhos)
  startBotTyping() {
    // Remove loading anterior se existir
    const existingLoading = this.chatContainer.querySelector('.loading-text');
    if (existingLoading) existingLoading.closest('.message').remove();

    const template = document.getElementById('loading-template');
    if (!template) return;

    const loadingNode = template.content.cloneNode(true);
    const message = loadingNode.querySelector('.message');
    this.chatContainer.appendChild(loadingNode);
    this.scrollToBottom();

    this.currentBotMessage = { message, isLoading: true };
  }

  stopBotTyping() {
    if (this.currentBotMessage && this.currentBotMessage.isLoading) {
      const messageEl = this.currentBotMessage.message;
      if (messageEl && messageEl.parentElement) {
        messageEl.remove();
      }
    }
    this.currentBotMessage = { rawText: '', isLoading: false };
  }

  appendToBotMessage(chunk) {
    // Se ainda estiver no loading, cria a mensagem real
    if (this.currentBotMessage.isLoading) {
      this.stopBotTyping();
      const { message, textEl } = this.createBotMessageElement();
      this.currentBotMessage = { message, textEl, rawText: chunk };
      this.chatContainer.appendChild(message);
    } else {
      this.currentBotMessage.rawText += chunk;
      const html = marked.parse(this.currentBotMessage.rawText);
      this.currentBotMessage.textEl.innerHTML = html;

      // Adiciona botão de copiar com ícone
      this.currentBotMessage.textEl.querySelectorAll('pre code').forEach(block => {
        if (!block.parentElement.querySelector('.copy-btn')) {
          this.addCopyButton(block);
        }
        hljs.highlightElement(block);
      });
    }
    this.scrollToBottom();
  }

  addCopyButton(codeBlock) {
  const pre = codeBlock.parentElement;
  if (pre.querySelector('.copy-btn')) return;

  const copyBtn = document.createElement('button');
  copyBtn.className = 'copy-btn';
  copyBtn.innerHTML = `
    <i class="fa-solid fa-copy"></i>
    <i class="fa-solid fa-check"></i>
    <span class="copy-text">Copiar</span>
  `;

  copyBtn.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(codeBlock.textContent);
      copyBtn.classList.add('copied');
      const text = copyBtn.querySelector('.copy-text');
      text.textContent = 'Copiado!';

      setTimeout(() => {
        copyBtn.classList.remove('copied');
        text.textContent = 'Copiar';
      }, 1500);
    } catch (err) {
      console.error('Erro ao copiar:', err);
    }
  });

  pre.insertBefore(copyBtn, pre.firstChild);
}

  createBotMessageElement() {
    const message = document.createElement('div');
    message.className = 'message bot';

    const label = document.createElement('div');
    label.className = 'user-label';
    label.textContent = 'Assistente';
    label.style.color = 'var(--primary)';

    const textEl = document.createElement('div');
    textEl.className = 'text';

    message.append(label, textEl);
    return { message, textEl };
  }

  addMessage(user, text, isUser) {
    const template = document.getElementById('message-template').content.cloneNode(true);
    const message = template.querySelector('.message');
    const label = template.querySelector('.user-label');
    const textEl = template.querySelector('.text');

    label.textContent = isUser ? user : 'Assistente';
    label.style.color = isUser ? 'var(--accent)' : 'var(--primary)';

    if (isUser) {
      textEl.textContent = text;
      message.classList.add('user');
    } else {
      textEl.innerHTML = marked.parse(text);
      textEl.querySelectorAll('pre code').forEach(block => {
        this.addCopyButton(block);
        hljs.highlightElement(block);
      });
      message.classList.add('bot');
    }

    this.chatContainer.appendChild(message);
    this.scrollToBottom();
  }

  scrollToBottom() {
    setTimeout(() => {
      this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
    }, 50);
  }

  setInputState(enabled) {
    this.promptInput.disabled = !enabled;
    this.sendBtn.disabled = !enabled;
    if (enabled) this.promptInput.focus();
  }

  togglePromptLibrary() {
  this.isLibraryOpen = !this.isLibraryOpen;
  this.promptLibrary.classList.toggle('expanded', this.isLibraryOpen);
  
  const toggleBtn = this.toggleBtn;
  const icon = toggleBtn.querySelector('.toggle-icon');
  const text = toggleBtn.querySelector('span') || toggleBtn;

  if (this.isLibraryOpen) {
    toggleBtn.innerHTML = `Fechar Prompts <i class="fa-solid fa-angle-up toggle-icon"></i>`;
    toggleBtn.classList.add('active');
  } else {
    toggleBtn.innerHTML = `Prompts Rápidos <i class="fa-solid fa-angle-up toggle-icon"></i>`;
    toggleBtn.classList.remove('active');
  }

  if (this.isLibraryOpen) this.newPromptInput.focus();
}

  async addPromptDirect() {
    const text = this.newPromptInput.value.trim();
    if (!text) return;

    const res = await fetch('/prompts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });

    if (res.ok) {
      this.prompts.push(text);
      this.renderPrompts();
      this.newPromptInput.value = '';
    }
  }

  async deletePrompt(text) {
    const overlay = document.createElement('div');
    overlay.className = 'confirm-overlay';
    overlay.innerHTML = `
      <div class="confirm-box">
        <p>Tem certeza que deseja deletar o prompt?</p>
        <p class="confirm-text">"${text.substring(0, 50)}${text.length > 50 ? '...' : ''}"</p>
        <div class="confirm-actions">
          <button class="btn-confirm">Sim</button>
          <button class="btn-cancel">Cancelar</button>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);

    const confirmed = await new Promise(resolve => {
      overlay.querySelector('.btn-confirm').onclick = () => resolve(true);
      overlay.querySelector('.btn-cancel').onclick = () => resolve(false);
      overlay.onclick = (e) => e.target === overlay && resolve(false);
    });

    overlay.remove();
    if (!confirmed) return;

    const res = await fetch('/prompts', {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });

    if (res.ok) {
      this.prompts = this.prompts.filter(p => p !== text);
      this.renderPrompts();
    }
  }

  usePrompt(text) {
    this.promptInput.value = text + " ";
    this.adjustTextareaHeight();
    this.promptInput.focus();
    if (this.isLibraryOpen) this.togglePromptLibrary();
  }

  renderPrompts() {
    this.promptList.innerHTML = '';
    this.prompts.forEach(text => {
      const item = document.createElement('div');
      item.className = 'prompt-item';

      const textEl = document.createElement('div');
      textEl.className = 'prompt-text';
      textEl.textContent = text;
      textEl.title = text;

      const useBtn = document.createElement('button');
      useBtn.className = 'prompt-btn use-btn';
      useBtn.textContent = 'Usar';
      useBtn.onclick = () => this.usePrompt(text);

      const delBtn = document.createElement('button');
      delBtn.className = 'prompt-btn delete-btn';
      delBtn.textContent = 'X';
      delBtn.onclick = () => this.deletePrompt(text);

      item.append(textEl, useBtn, delBtn);
      this.promptList.appendChild(item);
    });
  }
}

document.addEventListener('DOMContentLoaded', () => {
  new ChatApp();
});