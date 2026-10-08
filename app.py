import streamlit as st

st.set_page_config(
    page_title="Portail Entreprise - Tableaux de Bord",
    page_icon="🏢",
    layout="wide"
)

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