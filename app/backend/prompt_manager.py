import sqlite3

class PromptManager:
    def __init__(self, db_path="db/assistente_prompts.db"):
        self.db_path = db_path
        self._init_database_table()

    def _init_database_table(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prompts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL UNIQUE
                )
            """)
            conn.commit()

    def get_all_prompts(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT text FROM prompts ORDER BY id")
            results = [row[0] for row in cursor.fetchall()]

        if not results:
            default_prompts = [
                "Explique este trecho de código:",
                "Como posso otimizar este código Python?",
                "Escreva um teste unitário para esta função:",
                "Qual é a diferença entre uma lista e uma tupla em Python?"
            ]
            prompts_to_insert = [(p,) for p in default_prompts]
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.executemany("INSERT OR IGNORE INTO prompts (text) VALUES (?)", prompts_to_insert)
                conn.commit()
            return default_prompts
        return results

    def add_prompt(self, prompt_text):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO prompts (text) VALUES (?)", (prompt_text,))
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            print(f"Prompt '{prompt_text}' já existe.")
            return False
        except Exception as e:
            print(f"Erro ao adicionar prompt: {e}")
            return False

    def delete_prompt(self, prompt_text):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM prompts WHERE text = ?", (prompt_text,))
                conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao deletar prompt: {e}")
            return False