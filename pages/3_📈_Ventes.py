import streamlit as st
import plotly.express as px
import pandas as pd

st.set_page_config(page_title="Ventes & Opérations", page_icon="📈", layout="wide")
st.title("📈 Tableau de Bord - Ventes & Opérations")

# KPIs Ventes
c1, c2, c3 = st.columns(3)
c1.metric("Commandes du mois", "1 420", "+12%")
c2.metric("Panier Moyen", "880 MAD", "+45 MAD")
c3.metric("Délai Moyen Livraison", "2.4 jours", "-0.3 j")

st.divider()

# Tendance des ventes
df_ventes = pd.DataFrame({
    "Semaine": [f"S{i}" for i in range(1, 11)],
    "Ventes": [110, 130, 125, 140, 160, 155, 175, 190, 205, 220]
})
fig_ventes = px.line(df_ventes, x="Semaine", y="Ventes", markers=True, title="Évolution du Volume des Ventes")
st.plotly_chart(fig_ventes, use_container_width=True)