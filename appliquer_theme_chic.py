from pathlib import Path

# 1. Mise à jour de .streamlit/config.toml (Thème Executive Chic)
rep_streamlit = Path(".streamlit")
rep_streamlit.mkdir(exist_ok=True)

contenu_config = """[theme]
primaryColor = "#D4AF37"
backgroundColor = "#090D16"
secondaryBackgroundColor = "#111726"
textColor = "#F1F5F9"
font = "sans serif"

[client]
showErrorDetails = false

[ui]
hideTopBar = false
"""

with open(rep_streamlit / "config.toml", "w", encoding="utf-8") as f:
    f.write(contenu_config)

print("✅ .streamlit/config.toml mis à jour.")

# 2. Refonte complète de style.py (Design Haute Définition & Élégance Discrète)
contenu_style = """import streamlit as st
import plotly.io as pio

def appliquer_theme_cockpit_dark():
    # Thème Plotly sombre avec contraste feutré
    pio.templates.default = "plotly_dark"
    
    st.markdown('''
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Cinzel:wght@600;700&display=swap');
            
            html, body, [class*="css"] {
                font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
                letter-spacing: -0.01em;
            }

            /* Fond d'écran général riche et velouté */
            .stApp {
                background: radial-gradient(circle at top right, #111827 0%, #090D16 60%) !important;
                color: #F8FAFC !important;
            }

            /* Cartes de Métriques : Finition Titane & Reflet Champagne */
            [data-testid="stMetric"] {
                background: linear-gradient(145deg, rgba(23, 32, 51, 0.75) 0%, rgba(13, 19, 33, 0.85) 100%) !important;
                border: 1px solid rgba(212, 175, 55, 0.22) !important;
                border-radius: 16px !important;
                padding: 20px 24px !important;
                box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.08) !important;
                backdrop-filter: blur(12px);
                transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            }
            
            [data-testid="stMetric"]:hover {
                transform: translateY(-3px);
                border-color: rgba(212, 175, 55, 0.65) !important;
                box-shadow: 0 15px 35px -5px rgba(212, 175, 55, 0.12), inset 0 1px 0 rgba(212, 175, 55, 0.3) !important;
            }

            [data-testid="stMetricLabel"] {
                font-size: 0.8rem !important;
                color: #94A3B8 !important;
                font-weight: 600 !important;
                text-transform: uppercase;
                letter-spacing: 0.08em;
            }

            [data-testid="stMetricValue"] {
                font-size: 1.9rem !important;
                color: #F8FAFC !important;
                font-weight: 700 !important;
                letter-spacing: -0.02em;
            }
            
            [data-testid="stMetricDelta"] svg {
                fill: #D4AF37 !important;
            }

            /* Onglets Supérieurs (Tabs) : Style Capsule Horlogère */
            .stTabs [data-baseweb="tab-list"] {
                gap: 10px;
                background-color: rgba(17, 24, 39, 0.7);
                padding: 6px;
                border-radius: 14px;
                border: 1px solid rgba(255, 255, 255, 0.06);
                backdrop-filter: blur(8px);
            }
            
            .stTabs [data-baseweb="tab"] {
                border-radius: 10px;
                padding: 10px 22px;
                font-weight: 600;
                font-size: 0.9rem;
                color: #94A3B8 !important;
                border: none !important;
                background: transparent;
                transition: all 0.25s ease;
            }
            
            .stTabs [aria-selected="true"] {
                background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%) !important;
                color: #F1F5F9 !important;
                border: 1px solid rgba(212, 175, 55, 0.45) !important;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
            }

            /* Barre latérale (Sidebar) */
            [data-testid="stSidebar"] {
                background-color: #070B12 !important;
                border-right: 1px solid rgba(255, 255, 255, 0.07) !important;
            }

            /* Cartes de diagnostic et notes exécutives */
            .diag-box, .diagnostic-card {
                background: linear-gradient(145deg, rgba(23, 32, 51, 0.6) 0%, rgba(15, 23, 42, 0.7) 100%) !important;
                border-left: 3px solid #D4AF37 !important;
                border-top: 1px solid rgba(255, 255, 255, 0.06);
                border-right: 1px solid rgba(255, 255, 255, 0.06);
                border-bottom: 1px solid rgba(255, 255, 255, 0.06);
                padding: 18px 24px;
                border-radius: 12px;
                margin-bottom: 20px;
                color: #CBD5E1 !important;
                line-height: 1.65;
                font-size: 0.95rem;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            }

            /* Boutons Streamlit : Or Brossé Subtil */
            .stButton > button, .stDownloadButton > button {
                background: linear-gradient(135deg, #D4AF37 0%, #AA820A 100%) !important;
                color: #090D16 !important;
                border: none !important;
                border-radius: 10px;
                font-weight: 700;
                padding: 10px 22px;
                box-shadow: 0 4px 15px rgba(212, 175, 55, 0.25);
                transition: all 0.25s ease;
            }
            
            .stButton > button:hover, .stDownloadButton > button:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 22px rgba(212, 175, 55, 0.45) !important;
                color: #000000 !important;
            }

            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
        </style>
    ''', unsafe_allow_html=True)
"""

with open("style.py", "w", encoding="utf-8") as f:
    f.write(contenu_style)

print("✅ style.py transformé en Thème Executive Chic.")
print("🚀 Prêt à exécuter !")