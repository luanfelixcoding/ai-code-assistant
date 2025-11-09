from sys import stdout
from agno.tools import Toolkit
from io import StringIO

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
        old_stdout = stdout
        redirected_output = stdout = StringIO()

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
            stdout = old_stdout