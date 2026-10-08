import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from pathlib import Path

# 1. Configuration de la page
st.set_page_config(
    page_title="Direction des Ressources Humaines",
    page_icon="👥",
    layout="wide"
)

st.title("👥 Tableau de Bord RH & Contrôle de Gestion Sociale")
st.markdown("Suivi des effectifs, de la masse salariale, du turnover et de l'absentéisme.")

# 2. Chargement sécurisé des données
@st.cache_data
def charger_donnees_rh():
    chemin_racine = Path(__file__).resolve().parent.parent
    chemin_csv = chemin_racine / "donnees_rh.csv"
    
    if not chemin_csv.exists():
        chemin_csv = Path(__file__).resolve().parent / "donnees_rh.csv"
        
    if not chemin_csv.exists():
        st.error("Fichier introuvable : vérifiez que 'donnees_rh.csv' est bien placé à la racine du projet.")
        st.stop()
        
    df = pd.read_csv(chemin_csv)
    df["effectif_total"] = df["effectif_cdi"] + df["effectif_cdd"]
    return df

df_rh = charger_donnees_rh()

# 3. Filtres latéraux
with st.sidebar:
    st.header("⚙️ Filtres d'Analyse")
    mois_disponibles = ["Tous les mois"] + list(df_rh["mois"].unique())
    mois_choisi = st.selectbox("Mois d'analyse", mois_disponibles, index=0)
    
    departements = ["Tous"] + list(df_rh["departement"].unique())
    dept_choisi = st.selectbox("Département", departements, index=0)

# Filtrage du DataFrame
df_filtre = df_rh.copy()
if mois_choisi != "Tous les mois":
    df_filtre = df_filtre[df_filtre["mois"] == mois_choisi]
if dept_choisi != "Tous":
    df_filtre = df_filtre[df_filtre["departement"] == dept_choisi]

st.divider()

# 4. Calculs des agrégats RH
effectif_actuel = df_filtre["effectif_total"].sum() if mois_choisi != "Tous les mois" else df_filtre[df_filtre["mois"] == "Juin"]["effectif_total"].sum()
masse_salariale_totale = df_filtre["masse_salariale_kmad"].sum()

# Calcul du coût moyen par salarié par mois
nb_mois = df_filtre["mois"].nunique()
cout_moyen_salarie = (masse_salariale_totale / (effectif_actuel if effectif_actuel > 0 else 1) / nb_mois) * 1000

# Taux de turnover = ((Recrutements + Départs) / 2) / Effectif moyen
total_entrees = df_filtre["recrutements"].sum()
total_sorties = df_filtre["departs"].sum()
turnover_pct = (((total_entrees + total_sorties) / 2) / (effectif_actuel if effectif_actuel > 0 else 1)) * 100

# Taux d'absentéisme = Heures absence / Heures théoriques
taux_absenteisme = (df_filtre["heures_absence"].sum() / df_filtre["heures_theoriques"].sum()) * 100

# Taux de parité (part des femmes)
total_femmes = df_filtre["femmes"].sum()
part_femmes = (total_femmes / (total_femmes + df_filtre["hommes"].sum())) * 100

# 5. Affichage Ligne 1 : Effectifs et Masse Salariale
st.subheader("1. Synthèse Effectifs & Masse Salariale")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Effectif Total Clôture", f"{effectif_actuel} salariés", f"+{total_entrees - total_sorties} solde net")
k2.metric("Masse Salariale Cumulée", f"{masse_salariale_totale:,.0f} kMAD".replace(",", " "))
k3.metric("Coût Moyen Mensuel / Salarié", f"{cout_moyen_salarie:,.0f} MAD".replace(",", " "))
k4.metric("Part CDD / Flexibilité", f"{(df_filtre['effectif_cdd'].sum() / df_filtre['effectif_total'].sum() * 100):.1f}%")

# 6. Affichage Ligne 2 : Climat Social & Mouvements
st.subheader("2. Dynamique Sociale & Absentéisme")
s1, s2, s3, s4 = st.columns(4)
s1.metric("Taux d'Absentéisme", f"{taux_absenteisme:.2f}%", delta="-0.3 pt vs N-1", delta_color="inverse")
s2.metric("Taux de Turnover", f"{turnover_pct:.2f}%")
s3.metric("Entrées / Départs", f"{total_entrees} recrut. / {total_sorties} dép.")
s4.metric("Indice de Parité (Femmes)", f"{part_femmes:.1f}%")

st.divider()

# 7. Graphiques d'analyse
col_g1, col_g2 = st.columns(2)

with col_g1:
    st.subheader("Répartition des Effectifs par Département")
    # Agrégation par département sur le dernier mois disponible ou sélectionné
    mois_ref = mois_choisi if mois_choisi != "Tous les mois" else "Juin"
    df_dept = df_rh[df_rh["mois"] == mois_ref].groupby("departement")["effectif_total"].sum().reset_index()
    
    fig_pie = px.pie(
        df_dept,
        names="departement",
        values="effectif_total",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Safe
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col_g2:
    st.subheader("Évolution Mensuelle : Masse Salariale vs Absentéisme")
    df_mensuel = df_filtre.groupby("mois", as_index=False).agg({
        "masse_salariale_kmad": "sum",
        "heures_absence": "sum",
        "heures_theoriques": "sum"
    })
    # Calcul du taux mensuel
    df_mensuel["taux_abs"] = (df_mensuel["heures_absence"] / df_mensuel["heures_theoriques"]) * 100

    fig_combo = go.Figure()
    fig_combo.add_trace(go.Bar(
        x=df_mensuel["mois"],
        y=df_mensuel["masse_salariale_kmad"],
        name="Masse Salariale (kMAD)",
        marker_color="#2b5c8f"
    ))
    fig_combo.add_trace(go.Scatter(
        x=df_mensuel["mois"],
        y=df_mensuel["taux_abs"],
        name="Taux Absentéisme (%)",
        yaxis="y2",
        mode="lines+markers",
        line=dict(color="#d62728", width=3)
    ))
    fig_combo.update_layout(
        yaxis=dict(title="Masse Salariale (kMAD)"),
        yaxis2=dict(title="Absentéisme (%)", overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_combo, use_container_width=True)

st.divider()

# 8. Tableau détaillé avec export
st.subheader("📋 Données Détaillées par Département")
df_table = df_filtre[[
    "mois", "departement", "effectif_cdi", "effectif_cdd", "effectif_total",
    "recrutements", "departs", "masse_salariale_kmad"
]].rename(columns={
    "mois": "Mois",
    "departement": "Département",
    "effectif_cdi": "CDI",
    "effectif_cdd": "CDD",
    "effectif_total": "Total Salariés",
    "recrutements": "Recrutements",
    "departs": "Départs",
    "masse_salariale_kmad": "Masse Salariale (kMAD)"
})

st.dataframe(df_table, use_container_width=True)

csv_rh = df_table.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Télécharger les données RH (CSV)",
    data=csv_rh,
    file_name=f"reporting_rh_{mois_choisi}_{dept_choisi}.csv",
    mime="text/csv"
)