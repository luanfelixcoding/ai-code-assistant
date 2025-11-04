# Python Code Assistant (Assistente de Código Python)

Um assistente de IA com interface gráfica (GUI) construído em Python, utilizando `customtkinter` para o front-end e o poderoso framework `agno` para gerenciar o Agente de IA. O assistente é especializado em codificação Python e pode pesquisar informações atualizadas, além de testar snippets de código antes de fornecer a resposta.

## Funcionalidades

* **Interface Gráfica Moderna:** Desenvolvido com `customtkinter`, oferece um layout de chat escuro e responsivo.
* **Agente de IA Especializado:** Utiliza o modelo **Gemini 2.5 Flash** (via `agno`) configurado como um assistente de codificação.
* **Processamento Assíncrono:** Usa `threading` e `queue` para rodar o Agente em segundo plano, garantindo que a GUI permaneça responsiva durante as chamadas de API.
* **Ferramentas Integradas (Tool-Use):**
    * **`PythonExecutor`:** Uma ferramenta customizada que executa código Python em um ambiente isolado, captura o `stdout` e retorna o resultado para o Agente.
    * **`DuckDuckGoTools`:** Permite que o Agente faça pesquisas na web para obter informações atuais sobre bibliotecas, sintaxe ou fatos recentes.
* **Animação de Digitação:** Simula a digitação da resposta do bot para uma experiência de chat mais natural.

## Tecnologias

* **Python** (3.9+)
* **Frontend:** `customtkinter`
* **Framework de IA:** `agno`
* **Modelo de Linguagem:** Google Gemini 2.5 Flash
* **Gestão de Dependências:** `uv` (com `pyproject.toml` e `uv.lock`)

## Instalação e Configuração

### 1. Pré-requisitos

* Python 3.9+ instalado.
* Recomenda-se o uso de `uv` como gerenciador de pacotes para velocidade e reprodutibilidade (**opcional, mas recomendado**).

### 2. Configuração do Ambiente

Primeiro, você precisa configurar sua chave de API para o Gemini.

1.  Baixe o gerenciador de pacotes `uv` [aqui](https://docs.astral.sh/uv/getting-started/installation/).
2.  Obtenha sua chave de API em [Google AI Studio](https://ai.google.dev/gemini-api/docs/api-key).
3.  Crie um arquivo chamado **`.env`** na raiz do projeto e adicione sua chave:

    ```env
    # .env
    GEMINI_API_KEY="SUA_CHAVE_AQUI"
    GOOGLE_API_KEY="SUA_CHAVE_AQUI"
    ```
OBS: A chave `GOOGLE_API_KEY` será a mesma que `GEMINI_API_KEY` para a utilização da ferramenta `DuckDuckGoTools`

### 3. Instalação das Dependências

Utilizando `uv` (**recomendado** para usar o `uv.lock`):

#### 1. Crie o ambiente virtual e instale as dependências exatamente como no lockfile:
```bash
uv sync
# O comando acima criará o ambiente virtual em .venv/ e instalará tudo.
