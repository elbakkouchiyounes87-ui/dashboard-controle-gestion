import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from pathlib import Path

# 1. Configuration de la page
st.set_page_config(
    page_title="Simulation Contrôle de Gestion",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Cas Pratique : Analyse Budgétaire & Contrôle de Gestion")
st.markdown("Simulation basée sur le jeu de données d'entreprise (`donnees_controle_gestion.csv`).")

# 2. Chargement sécurisé du fichier CSV
@st.cache_data
def charger_donnees():
    # Détecte le dossier racine (un niveau au-dessus de pages/)
    chemin_racine = Path(__file__).resolve().parent.parent
    chemin_csv = chemin_racine / "donnees_controle_gestion.csv"
    
    # Sécurité si le fichier CSV est placé directement dans pages/
    if not chemin_csv.exists():
        chemin_csv = Path(__file__).resolve().parent / "donnees_controle_gestion.csv"
        
    if not chemin_csv.exists():
        st.error(f"Fichier introuvable. Veuillez vérifier que 'donnees_controle_gestion.csv' est bien créé dans le dossier du projet.")
        st.stop()
        
    df = pd.read_csv(chemin_csv)
    
    # Calculs des SIG
    df["marge_brute_realisee"] = df["ca_realise"] - df["cogs_realise"]
    df["taux_marge_brute"] = (df["marge_brute_realisee"] / df["ca_realise"]) * 100
    df["ecart_ca"] = df["ca_realise"] - df["ca_budget"]
    df["ecart_ebitda"] = df["ebitda_realise"] - df["ebitda_budget"]
    
    # Calculs BFR et Délais de rotation (sur base mensuelle de 30 jours)
    df["bfr"] = (df["creances_clients"] + df["stocks"]) - df["dettes_fournisseurs"]
    df["dso"] = (df["creances_clients"] / df["ca_realise"]) * 30       # Crédit clients en jours
    df["dpo"] = (df["dettes_fournisseurs"] / df["cogs_realise"]) * 30  # Crédit fournisseurs en jours
    
    return df

df = charger_donnees()

# 3. Barre latérale : Filtres pour la simulation
with st.sidebar:
    st.header("🔍 Filtres d'Analyse")
    trimestre_filtre = st.selectbox("Période / Trimestre", ["Année Complète", "T1", "T2", "T3", "T4"])
    devise = st.radio("Devise", ["kMAD", "kEUR", "kUSD"])

# Application du filtre
if trimestre_filtre != "Année Complète":
    df_vue = df[df["trimestre"] == trimestre_filtre].copy()
else:
    df_vue = df.copy()

st.divider()

# 4. Calculs des agrégats pour la période sélectionnée
ca_total_real = df_vue["ca_realise"].sum()
ca_total_budg = df_vue["ca_budget"].sum()
ecart_ca_pct = ((ca_total_real - ca_total_budg) / ca_total_budg) * 100

ebitda_total_real = df_vue["ebitda_realise"].sum()
ebitda_total_budg = df_vue["ebitda_budget"].sum()
ecart_ebitda_pct = ((ebitda_total_real - ebitda_total_budg) / ebitda_total_budg) * 100

marge_brute_pct = (df_vue["marge_brute_realisee"].sum() / ca_total_real) * 100
dso_moyen = df_vue["dso"].mean()
dpo_moyen = df_vue["dpo"].mean()
bfr_fin_periode = df_vue["bfr"].iloc[-1]
cash_fin_periode = df_vue["tresorerie_nette"].iloc[-1]

# 5. Affichage Ligne 1 : Performance Économique
st.subheader("1. Performance Économique (Cumul Période)")
c1, c2, c3, c4 = st.columns(4)
c1.metric("CA Réalisé", f"{ca_total_real:,.0f} {devise}".replace(",", " "), f"{ecart_ca_pct:+.1f}% vs Budget")
c2.metric("Taux de Marge Brute", f"{marge_brute_pct:.1f}%")
c3.metric("EBITDA Réalisé", f"{ebitda_total_real:,.0f} {devise}".replace(",", " "), f"{ecart_ebitda_pct:+.1f}% vs Budget")
c4.metric("Trésorerie Clôture", f"{cash_fin_periode:,.0f} {devise}".replace(",", " "))

# 6. Affichage Ligne 2 : BFR et Délais d'exploitation
st.subheader("2. BFR d'Exploitation & Délais de Règlement")
b1, b2, b3, b4 = st.columns(4)
b1.metric("BFR en Fin de Période", f"{bfr_fin_periode:,.0f} {devise}".replace(",", " "))
b2.metric("DSO (Crédit Clients)", f"{dso_moyen:.0f} jours")
b3.metric("DPO (Crédit Fournisseurs)", f"{dpo_moyen:.0f} jours")
b4.metric("Poids Masse Salariale", f"{(df_vue['charges_personnel'].sum() / ca_total_real * 100):.1f}% du CA")

st.divider()

# 7. Visualisations graphiques
g1, g2 = st.columns(2)

with g1:
    st.subheader("Analyse d'Écart : CA Réalisé vs Budget")
    fig_ca = px.bar(
        df_vue,
        x="mois",
        y=["ca_realise", "ca_budget"],
        barmode="group",
        labels={"value": f"Montant ({devise})", "variable": "Légende", "mois": "Mois"},
        color_discrete_map={"ca_realise": "#1f77b4", "ca_budget": "#aec7e8"}
    )
    fig_ca.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig_ca, use_container_width=True)

with g2:
    st.subheader("Évolution du BFR vs Trésorerie Nette")
    fig_bfr = px.line(
        df_vue,
        x="mois",
        y=["bfr", "tresorerie_nette"],
        markers=True,
        labels={"value": f"Montant ({devise})", "variable": "Indicateur", "mois": "Mois"},
        color_discrete_map={"bfr": "#ff7f0e", "tresorerie_nette": "#2ca02c"}
    )
    fig_bfr.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig_bfr, use_container_width=True)

st.divider()

# 8. Tableau synthétique avec téléchargement
st.subheader("📋 Tableau Récapitulatif des Données")
colonnes_affichage = {
    "mois": "Mois",
    "ca_realise": f"CA Réalisé ({devise})",
    "ca_budget": f"CA Budget ({devise})",
    "ecart_ca": f"Écart CA ({devise})",
    "ebitda_realise": f"EBITDA Réel ({devise})",
    "ebitda_budget": f"EBITDA Budget ({devise})",
    "ecart_ebitda": f"Écart EBITDA ({devise})",
    "bfr": f"BFR ({devise})"
}

df_table = df_vue[list(colonnes_affichage.keys())].rename(columns=colonnes_affichage)
st.dataframe(df_table, use_container_width=True)

csv_data = df_table.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Exporter ce tableau au format CSV",
    data=csv_data,
    file_name=f"analyse_controle_gestion_{trimestre_filtre}.csv",
    mime="text/csv"
)