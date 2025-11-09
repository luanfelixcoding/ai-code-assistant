# Importando Frameworks
from agno.agent import Agent
from agno.tools.python import PythonTools
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.models.google import Gemini

# Importando bibliotecas
from os import getenv
from dotenv import load_dotenv
from CTkMessagebox import CTkMessagebox

# Carregando variavéis de ambiente
load_dotenv()

# Verificando a existencia da API
if not getenv("GEMINI_API_KEY"):
    print(
        "AVISO: A chave de API GEMINI_API_KEY não foi encontrada."
    )
    CTkMessagebox(
        title="AVISO de Configuração",
        message="A chave de API GEMINI_API_KEY não foi encontrada. O código pode não funcionar corretamente.",
        icon="warning",           
        option_1="OK"
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
        #PythonTools(),
        DuckDuckGoTools()
    ],
    add_history_to_context=True,
)