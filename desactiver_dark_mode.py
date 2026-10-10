from pathlib import Path

# 1. Rétablir .streamlit/config.toml en mode clair standard
rep_streamlit = Path(".streamlit")
rep_streamlit.mkdir(exist_ok=True)

contenu_config_clair = """[theme]
base = "light"
primaryColor = "#1E3A8A"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F8FAFC"
textColor = "#0F172A"
font = "sans serif"

[client]
showErrorDetails = false

[ui]
hideTopBar = false
"""

with open(rep_streamlit / "config.toml", "w", encoding="utf-8") as f:
    f.write(contenu_config_clair)

print("✅ .streamlit/config.toml réinitialisé en mode clair.")

# 2. Rétablir style.py avec un design clair, sobre et corporate
contenu_style_clair = """import streamlit as st
import plotly.io as pio

def appliquer_theme_cockpit_dark():
    # Rétablir le template Plotly standard clair
    pio.templates.default = "plotly_white"
    
    st.markdown('''
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
            
            html, body, [class*="css"] {
                font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
            }

            /* Fond clair standard */
            .stApp {
                background-color: #FFFFFF !important;
                color: #0F172A !important;
            }

            /* Cartes de métriques claires et professionnelles */
            [data-testid="stMetric"] {
                background-color: #FFFFFF !important;
                border: 1px solid #E2E8F0 !important;
                border-radius: 12px !important;
                padding: 16px 20px !important;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
            }
            
            [data-testid="stMetricLabel"] {
                font-size: 0.85rem !important;
                color: #64748B !important;
                font-weight: 600 !important;
                text-transform: none !important;
                letter-spacing: normal !important;
            }

            [data-testid="stMetricValue"] {
                font-family: inherit !important;
                font-size: 1.6rem !important;
                color: #0F172A !important;
                font-weight: 700 !important;
                text-shadow: none !important;
            }

            /* Onglets clairs */
            .stTabs [data-baseweb="tab-list"] {
                gap: 8px;
                background-color: #F1F5F9 !important;
                padding: 6px;
                border-radius: 10px;
                border: 1px solid #E2E8F0 !important;
            }
            
            .stTabs [data-baseweb="tab"] {
                border-radius: 8px;
                padding: 8px 18px;
                font-weight: 600;
                color: #475569 !important;
                border: none !important;
                background: transparent !important;
            }
            
            .stTabs [aria-selected="true"] {
                background-color: #FFFFFF !important;
                color: #1E3A8A !important;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08) !important;
                border: 1px solid #CBD5E1 !important;
            }

            /* Barre latérale claire */
            [data-testid="stSidebar"] {
                background-color: #F8FAFC !important;
                border-right: 1px solid #E2E8F0 !important;
            }

            /* Boîtes de diagnostic claires */
            .diag-box, .diagnostic-card {
                background-color: #F8FAFC !important;
                border-left: 4px solid #1E3A8A !important;
                border-top: 1px solid #E2E8F0;
                border-right: 1px solid #E2E8F0;
                border-bottom: 1px solid #E2E8F0;
                padding: 14px 18px;
                border-radius: 8px;
                margin-bottom: 15px;
                color: #334155 !important;
                line-height: 1.5;
            }

            /* Boutons standards */
            .stButton > button, .stDownloadButton > button {
                background: #1E3A8A !important;
                color: #FFFFFF !important;
                border: none !important;
                border-radius: 8px;
                font-weight: 600;
                padding: 8px 18px;
                box-shadow: none !important;
            }
            
            .stButton > button:hover, .stDownloadButton > button:hover {
                background: #1D4ED8 !important;
                color: #FFFFFF !important;
            }

            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
        </style>
    ''', unsafe_allow_html=True)
"""

with open("style.py", "w", encoding="utf-8") as f:
    f.write(contenu_style_clair)

print("✅ style.py réinitialisé en mode clair.")
print("🚀 Prêt !")