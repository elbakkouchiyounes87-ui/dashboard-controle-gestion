import streamlit as st

st.set_page_config(
    page_title="Portail Entreprise - Tableaux de Bord",
    page_icon="🏢",
    layout="wide"
)
st.markdown("""
    <style>
        /* Masquer le menu Streamlit et le filigrane */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Style moderne des cartes KPI */
        [data-testid="stMetric"] {
            background-color: #F8FAFC;
            border: 1px solid #E2E8F0;
            padding: 15px 20px;
            border-radius: 10px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.85rem !important;
            color: #64748B !important;
            font-weight: 600;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.6rem !important;
            color: #0F172A !important;
            font-weight: 700;
        }
    </style>
""", unsafe_allow_html=True)
st.title("🏢 Portail de Gestion et Tableaux de Bord")
st.markdown("Bienvenue sur la plateforme de suivi décisionnel multi-services.")

st.info("Utilisez le menu à gauche pour naviguer entre les différents départements.")

col1, col2, col3 = st.columns(3)
with col1:
    st.subheader("💰 Finance")
    st.write("Suivi du compte de résultat, trésorerie et marges opérationnelles.")
with col2:
    st.subheader("👥 Ressources Humaines")
    st.write("Effectifs, masse salariale et taux de turnover.")
with col3:
    st.subheader("📈 Ventes & Opérations")
    st.write("Pipeline commercial, volume d'activité et stocks.")