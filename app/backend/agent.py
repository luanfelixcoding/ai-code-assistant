# backend/agent.py

from agno.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.models.google import Gemini
from dotenv import load_dotenv
import os

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise EnvironmentError("GEMINI_API_KEY não encontrada no .env")

code_assistant = Agent(
    name="Code Assistant gemini-2.5-flash",
    model=Gemini(id="gemini-2.5-flash"),
    description="Assistente especializado em Python e pesquisa de programação.",
    instructions=(
        "Você é um assistente de codificação especializado em Python.\n"
        "1. Para perguntas sobre sintaxe, bibliotecas recentes ou fatos atuais, use `duckduckgo_search`.\n"
        "2. Seja conciso, mas completo. Formate código com ```python.\n"
        "3. Sempre justifique o uso de ferramentas."
    ),
    tools=[DuckDuckGoTools()],
    add_history_to_context=True,
)