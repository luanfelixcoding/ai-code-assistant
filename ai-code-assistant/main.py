# Importando
from customtkinter import CTk
from app.app_gui import ChatApp

    
if __name__ == "__main__":
    app_root = CTk()
    chat_app = ChatApp(app_root)
    app_root.mainloop()