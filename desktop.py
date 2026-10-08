import threading
import time
import sys
import webview
import streamlit.web.cli as stcli

def demarrer_streamlit():
    # Lance Streamlit sans ouvrir le navigateur classique
    sys.argv = [
        "streamlit",
        "run",
        "app.py",
        "--server.headless=true",
        "--server.port=8501",
        "--global.developmentMode=false"
    ]
    stcli.main()

if __name__ == "__main__":
    # Démarre le serveur Streamlit dans un thread séparé
    t = threading.Thread(target=demarrer_streamlit, daemon=True)
    t.start()

    # Attend 2 secondes que le serveur initialise
    time.sleep(2)

    # Ouvre la fenêtre logicielle de bureau
    webview.create_window(
        title="Portail de Gestion & Contrôle de Gestion",
        url="http://localhost:8501",
        width=1280,
        height=800,
        resizable=True
    )
    webview.start()