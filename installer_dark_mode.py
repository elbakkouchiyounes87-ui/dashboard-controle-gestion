import os
from pathlib import Path

# 1. Création de .streamlit/config.toml
rep_streamlit = Path(".streamlit")
rep_streamlit.mkdir(exist_ok=True)

contenu_config_toml = """[theme]
primaryColor = "#06B6D4"
backgroundColor = "#0B0F19"
secondaryBackgroundColor = "#111827"
textColor = "#F8FAFC"
font = "sans serif"

[client]
showErrorDetails = false

[ui]
hideTopBar = false
"""

with open(rep_streamlit / "config.toml", "w", encoding="utf-8") as f:
  f.write(contenu_config_toml)

print("✅ Fichier .streamlit/config.toml créé avec succès.")

# 2. Création du module universel style.py
contenu_style_py = """import streamlit as st
import plotly.io as pio

def appliquer_theme_cockpit_dark():
    # Définition du thème par défaut pour tous les graphiques Plotly
    pio.templates.default = "plotly_dark"
    
    st.markdown('''
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');
            
            html, body, [class*="css"] {
                font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
            }

            /* Fond général */
            .stApp {
                background-color: #0B0F19 !important;
                color: #F8FAFC !important;
            }

            /* Cartes de Métriques (Style Cockpit Néon / Glassmorphism) */
            [data-testid="stMetric"] {
                background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%) !important;
                border: 1px solid rgba(56, 189, 248, 0.2) !important;
                border-radius: 14px !important;
                padding: 18px 22px !important;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
                backdrop-filter: blur(8px);
                transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
            }
            
            [data-testid="stMetric"]:hover {
                transform: translateY(-2px);
                border-color: rgba(6, 182, 212, 0.6) !important;
                box-shadow: 0 8px 25px rgba(6, 182, 212, 0.15) !important;
            }

            [data-testid="stMetricLabel"] {
                font-size: 0.82rem !important;
                color: #94A3B8 !important;
                font-weight: 600 !important;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }

            [data-testid="stMetricValue"] {
                font-family: 'JetBrains Mono', monospace !important;
                font-size: 1.8rem !important;
                color: #38BDF8 !important;
                font-weight: 700 !important;
                text-shadow: 0 0 12px rgba(56, 189, 248, 0.3);
            }

            /* Onglets Supérieurs (Tabs) */
            .stTabs [data-baseweb="tab-list"] {
                gap: 8px;
                background-color: #111827;
                padding: 6px;
                border-radius: 12px;
                border: 1px solid #1E293B;
            }
            
            .stTabs [data-baseweb="tab"] {
                border-radius: 8px;
                padding: 8px 18px;
                font-weight: 600;
                color: #94A3B8 !important;
                border: none !important;
                background: transparent;
            }
            
            .stTabs [aria-selected="true"] {
                background: #1E293B !important;
                color: #38BDF8 !important;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
                border: 1px solid rgba(56, 189, 248, 0.3) !important;
            }

            /* Barre latérale (Sidebar) */
            [data-testid="stSidebar"] {
                background-color: #0B0F19 !important;
                border-right: 1px solid #1E293B !important;
            }

            /* Boîte de diagnostic stylisée */
            .diag-box, .diagnostic-card {
                background: rgba(15, 23, 42, 0.75) !important;
                border-left: 4px solid #06B6D4 !important;
                border: 1px solid #1E293B;
                padding: 16px 20px;
                border-radius: 8px;
                margin-bottom: 18px;
                color: #CBD5E1 !important;
                line-height: 1.6;
            }

            /* Boutons Streamlit */
            .stButton > button {
                background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%) !important;
                color: #FFFFFF !important;
                border: 1px solid #38BDF8 !important;
                border-radius: 10px;
                font-weight: 600;
                padding: 10px 20px;
                transition: all 0.2s ease;
            }
            
            .stButton > button:hover {
                box-shadow: 0 0 15px rgba(56, 189, 248, 0.4) !important;
                transform: translateY(-1px);
            }

            /* Masquer éléments Streamlit inutiles */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
        </style>
    ''', unsafe_allow_html=True)
"""

with open("style.py", "w", encoding="utf-8") as f:
  f.write(contenu_style_py)

print("✅ Fichier style.py créé avec succès.")

# 3. Injection automatique de l'appel dans app.py et les pages
fichiers_cibles = [
    Path("app.py"),
    Path("pages/1_💰_Finance.py"),
    Path("pages/2_👥_RH.py"),
    Path("pages/3_📈_Ventes.py"),
]

for chemin in fichiers_cibles:
  if chemin.exists():
    with open(chemin, "r", encoding="utf-8") as f:
      code = f.read()

    # Si la fonction n'est pas déjà importée
    if "appliquer_theme_cockpit_dark" not in code:
      # Remplacer st.set_page_config en injectant l'appel immédiatement après
      position_config = code.find("st.set_page_config(")
      if position_config != -1:
        fin_config = code.find(")", position_config) + 1
        code_modifie = (
            "from style import appliquer_theme_cockpit_dark\n"
            + code[:fin_config]
            + "\nappliquer_theme_cockpit_dark()\n"
            + code[fin_config:]
        )
        with open(chemin, "w", encoding="utf-8") as f:
          f.write(code_modifie)
        print(f"✅ Thème Dark appliqué dans {chemin.name}")
      else:
        print(f"⚠️ 'st.set_page_config' non trouvé dans {chemin.name}")
  else:
    print(f"ℹ️ {chemin} non trouvé, ignoré.")

print("\n🚀 Configuration terminée ! Vous pouvez tester ou pousser sur GitHub.")