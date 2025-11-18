# Assistente de Código Python com IA

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0%2B-green)](https://flask.palletsprojects.com/)
[![Gemini API](https://img.shields.io/badge/Gemini%20API-Integrated-orange)](https://ai.google.dev/)
[![Licença](https://img.shields.io/badge/Licença-MIT-yellow)](LICENSE)

## Visão Geral

Este projeto é um **assistente de chat baseado em IA** especializado em programação Python. Ele permite que usuários façam perguntas sobre código, sintaxe, bibliotecas e otimizações, com suporte para anexar arquivos `.py` para análise direta. A IA é alimentada pela API do Google Gemini, garantindo respostas precisas e atualizadas .

O aplicativo é full-stack:
- **Backend**: Flask para servidor, gerenciamento de sessões, streaming de respostas e banco **SQLite** para prompts salvos.
- **Frontend**: Interface intuitiva em HTML/CSS/JS com upload de arquivos (drag & drop), temas dark/light, renderização de Markdown e código destacado.

Ideal para desenvolvedores Python que precisam de ajuda rápida e contextualizada. O chat é interativo, com respostas streamadas em tempo real para uma experiência fluida.

### Principais Funcionalidades
- **Chat com IA**: Envie prompts sobre Python e receba respostas formatadas, com código em blocos destacados e botão de cópia.
- **Upload de Arquivos**: Anexe arquivos `.py` (máx. 1MB), que são lidos e incluídos no contexto da IA.
- **Prompts Rápidos**: Salve, use e delete prompts favoritos persistidos em banco de dados.
- **Temas**: Alternância entre dark e light mode com persistência via localStorage.
- **Streaming**: Respostas aparecem progressivamente, com animação de "digitando".
- **Validações**: Suporte apenas a `.py`, limite de tamanho e feedback visual para uploads.

## Requisitos
- Python 3.8 ou superior.
- Bibliotecas: `Flask`, `python-dotenv`, `google-generativeai`, `sqlite3`, `werkzeug`.
- Chave API do Google Gemini (gratuita para uso básico).

## Instalação

1. **Clone o Repositório**:
   ```
   git clone https://github.com/seu-usuario/assistente-codigo-python.git
   cd assistente-codigo-python
   ```

2. **Crie um Ambiente Virtual** (recomendado):
   ```
   Sem UV:
   python -m venv .venv
   source venv/bin/activate  # No Windows: .venv\Scripts\activate
   
   Com UV:
   uv sync
   source venv/bin/activate  # No Windows: .venv\Scripts\activate
   ```

3. **Instale Dependências**:
   ```
   Sem UV:
   pip install flask python-dotenv google-generativeai werkzeug
   
   Com UV:
   uv sync
   ```
   *Nota: Se usar a biblioteca `agno` (para agente Gemini), instale-a separadamente se não for built-in.*

4. **Configure Variáveis de Ambiente**:
   Crie um arquivo `.env` na raiz do projeto:
   ```
   GEMINI_API_KEY=sua_chave_api_aqui
   ```
   Obtenha a chave em [ai.google.dev](https://ai.google.dev/).

5. **Inicie o Servidor**:
   ```
   Sem UV:
   python app.py
   
   Com UV:
   uv run app.py
   ```
   O app rodará em `http://127.0.0.1:5000/` (modo debug ativado por padrão).

## Uso

1. **Acesse a Interface**: Abra o navegador em `http://localhost:5000/`.
   
2. **Envie uma Mensagem**:
   - Digite seu prompt no campo de texto (ex: "Explique este código:").
   - Opcionalmente, anexe um arquivo `.py` clicando no ícone de clipe ou arrastando (drag & drop).
   - Clique no avião de papel para enviar.

3. **Respostas da IA**:
   - A resposta aparece streamada, com formatação Markdown.
   - Blocos de código Python são destacados com syntax highlighting e botão "Copiar".

4. **Prompts Rápidos**:
   - Clique em "Prompts Rápidos" para abrir a biblioteca.
   - Adicione novos prompts digitando e clicando "Adicionar".
   - Use ou delete prompts existentes.

5. **Alternar Tema**:
   - Clique no ícone de sol/lua no topo para mudar entre dark e light.

6. **Exemplo de Interação**:
   - Prompt: "Otimize este código:" + anexe `exemplo.py`.
   - IA: Analisa o arquivo e sugere melhorias, com código otimizado.

## Estrutura do Projeto

```
ai-code-assistant/
├── backend/
│   ├── agent.py          # Configuração do agente Gemini com Agno.
│   └── prompt_manager.py # Gerenciamento de prompts com SQLite.
├── static/
│   ├── css/
│   │   └── style.css     # Estilos com temas e animações.
│   └── js/
│       └── main.js       # Lógica frontend (chat, upload, streaming).
├── templates/
│   └── index.html        # Interface HTML principal.
├── app.py                # Servidor Flask com rotas.
├── .env                  # Variáveis de ambiente (não versionado).
├── db/                   # Diretório para banco SQLite (criado automaticamente).
└── README.md             # Arquivo para Documentação.
```

## Contribuições

- Fork o repositório.
- Crie uma branch: `git checkout -b feature/nova-funcionalidade`.
- Commit: `git commit -m "Adiciona nova funcionalidade"`.
- Push: `git push origin feature/nova-funcionalidade`.
- Abra um Pull Request.

Sugestões: Adicionar suporte a mais modelos de IA, autenticação ou integração com GitHub.

## Segurança e Limitações

- **Segurança**: Uploads limitados a 1MB e `.py`; nomes de arquivos sanitizados com `secure_filename`, sem armazenamento persistente de arquivos.
- **Limitações**: Dependente da API Gemini (cotas gratuitas limitadas), sem suporte a outros formatos de arquivo, rodando em debug para dev.
- **Melhores Práticas**: Use em ambiente local, evite expor a chave API.

## Licença

Este projeto está sob a licença MIT.

Desenvolvido com muita dedicação por:
- [Luan](https://github.com/luanfelixcoding)
- [Felipe](https://github.com/mafra013)
- [Graziela](https://github.com/GrazielaAntiorio)