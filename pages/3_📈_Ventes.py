import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from pathlib import Path
from fpdf import FPDF

# 1. Configuration & Style Corporate
st.set_page_config(
    page_title="Direction Commerciale & Performance",
    page_icon="📈",
    layout="wide"
)

st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        [data-testid="stMetric"] {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            padding: 16px 20px;
            border-radius: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.04);
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
        .diag-box {
            background-color: #F8FAFC;
            border-left: 4px solid #1E3A8A;
            padding: 14px 18px;
            border-radius: 6px;
            margin-bottom: 15px;
            font-size: 0.95rem;
            color: #334155;
            line-height: 1.5;
        }
    </style>
""", unsafe_allow_html=True)

# En-tête avec Logo
chemin_racine = Path(__file__).resolve().parent.parent
chemin_logo = chemin_racine / "assets" / "logo.png"

col_head1, col_head2 = st.columns([1, 5])
with col_head1:
    if chemin_logo.exists():
        st.image(str(chemin_logo), width=120)
with col_head2:
    st.title("📈 Direction Commerciale & Pilotage des Ventes")
    st.caption("Efficacité commerciale : courbe de Stobach (baleine), matrice BCG volume/marge et vélocité du pipeline.")

# 2. Chargement des données
@st.cache_data
def charger_donnees_ventes():
    chemin_csv = chemin_racine / "donnees_ventes.csv"
    if not chemin_csv.exists():
        chemin_csv = Path(__file__).resolve().parent / "donnees_ventes.csv"
    if not chemin_csv.exists():
        st.error("Fichier 'donnees_ventes.csv' introuvable.")
        st.stop()
    return pd.read_csv(chemin_csv)

df_ventes = charger_donnees_ventes()

# 3. Filtres
with st.sidebar:
    st.header("⚙️ Paramètres d'Analyse")
    mois_dispo = ["Tous les mois"] + list(df_ventes["mois"].unique())
    mois_choisi = st.selectbox("Période sous revue", mois_dispo, index=0)

    regions_dispo = ["Toutes les régions"] + list(df_ventes["region"].unique())
    region_choisie = st.selectbox("Région Commerciale", regions_dispo, index=0)

    canaux_dispo = ["Tous les canaux"] + list(df_ventes["canal"].unique())
    canal_choisi = st.selectbox("Canal de Distribution", canaux_dispo, index=0)
    devise = st.radio("Devise", ["MAD", "EUR", "USD"])

df_vue = df_ventes.copy()
if mois_choisi != "Tous les mois":
    df_vue = df_vue[df_vue["mois"] == mois_choisi]
if region_choisie != "Toutes les régions":
    df_vue = df_vue[df_vue["region"] == region_choisie]
if canal_choisi != "Tous les canaux":
    df_vue = df_vue[df_vue["canal"] == canal_choisi]

# 4. Calculs des KPIs
ca_total_kmad = df_vue["ca_realise_kmad"].sum()
marge_totale_kmad = df_vue["marge_brute_kmad"].sum()
taux_marge_commerciale = (marge_totale_kmad / ca_total_kmad * 100) if ca_total_kmad > 0 else 0
total_quantites = df_vue["quantite_vendue"].sum()
prix_moyen_vente = ((ca_total_kmad * 1000) / total_quantites) if total_quantites > 0 else 0

prospects_total = df_vue["prospects"].sum()
devis_total = df_vue["devis_emis"].sum()
gagnes_total = df_vue["opportunites_gagnees"].sum()

taux_transfo_devis = (devis_total / prospects_total * 100) if prospects_total > 0 else 0
taux_closing = (gagnes_total / devis_total * 100) if devis_total > 0 else 0

# 5. Onglets
tab_kpis, tab_pipeline, tab_stobach, tab_bcg, tab_pdf = st.tabs([
    "📊 Synthèse Activité & Marges",
    "🎯 Pipeline & Vélocité",
    "🐋 Courbe de Stobach (Baleine)",
    "📦 Matrice BCG Volume/Marge",
    "📄 Synthèse Commerciale PDF"
])

# --- ONGLET 1 : SYNTHÈSE ACTIVITÉ ---
with tab_kpis:
    st.subheader("Performance Commerciale Globale")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Chiffre d'Affaires", f"{ca_total_kmad:,.0f} k{devise}".replace(",", " "))
    k2.metric("Marge Commerciale", f"{marge_totale_kmad:,.0f} k{devise}".replace(",", " "), f"Taux: {taux_marge_commerciale:.1f}%")
    k3.metric("Volume Vendu", f"{total_quantites:,.0f} unités".replace(",", " "))
    k4.metric("Prix Moyen Unitaire", f"{prix_moyen_vente:,.0f} {devise}".replace(",", " "))

    st.markdown(f"""
        <div class='diag-box'>
        <b>Note d'Activité Commerciale :</b> L'activité enregistre un chiffre d'affaires consolidé de <b>{ca_total_kmad:,.0f} k{devise}</b> 
        avec une marge brute moyenne de <b>{taux_marge_commerciale:.1f}%</b>. Le taux de concrétisation global ressort à <b>{taux_closing:.1f}%</b>.
        </div>
    """, unsafe_allow_html=True)

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("Évolution Mensuelle des Ventes")
        df_mensuel = df_vue.groupby("mois", as_index=False)[["ca_realise_kmad", "marge_brute_kmad"]].sum()
        ordre_mois = ["Janvier", "Fevrier", "Mars", "Avril", "Mai", "Juin"]
        df_mensuel["mois"] = pd.Categorical(df_mensuel["mois"], categories=ordre_mois, ordered=True)
        df_mensuel = df_mensuel.sort_values("mois")

        fig_evol = px.bar(
            df_mensuel, x="mois", y=["ca_realise_kmad", "marge_brute_kmad"],
            barmode="group",
            title=f"CA vs Marge Brute (k{devise})",
            labels={"value": f"Montant (k{devise})", "variable": "Indicateur", "mois": "Mois"},
            color_discrete_map={"ca_realise_kmad": "#1E3A8A", "marge_brute_kmad": "#10B981"}
        )
        st.plotly_chart(fig_evol, use_container_width=True)

    with col_g2:
        st.subheader("Contribution par Canal de Vente")
        df_canal = df_vue.groupby("canal", as_index=False)["ca_realise_kmad"].sum()
        fig_canal = px.pie(
            df_canal, names="canal", values="ca_realise_kmad",
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        st.plotly_chart(fig_canal, use_container_width=True)

# --- ONGLET 2 : PIPELINE & VÉLOCITÉ ---
with tab_pipeline:
    st.subheader("1. Entonnoir de Conversion Commerciale")
    fig_funnel = go.Figure(go.Funnel(
        y=["1. Prospects Qualifiés", "2. Devis Émis & Négociation", "3. Contrats Signés"],
        x=[prospects_total, devis_total, gagnes_total],
        textinfo="value+percent previous",
        marker=dict(color=["#93C5FD", "#3B82F6", "#1E3A8A"])
    ))
    fig_funnel.update_layout(title="Pipeline Commercial Consolidé")
    st.plotly_chart(fig_funnel, use_container_width=True)

    st.divider()
    st.subheader("2. Calculateur de Vélocité des Ventes")
    st.caption("Formule standard : Vélocité = (Opportunités x Panier Moyen x Taux Closing) / Durée Moyenne du Cycle de Vente.")

    vc1, vc2 = st.columns(2)
    with vc1:
        duree_cycle_jours = st.slider("Durée moyenne d'un cycle de vente (jours)", 15, 120, 45)
    with vc2:
        panier_moyen_estime = (ca_total_kmad * 1000) / gagnes_total if gagnes_total > 0 else 0
        st.metric("Panier Moyen Réalisé", f"{panier_moyen_estime:,.0f} {devise}".replace(",", " "))

    velocite_journaliere = (devis_total * panier_moyen_estime * (taux_closing / 100.0)) / duree_cycle_jours if duree_cycle_jours > 0 else 0
    velocite_mensuelle = (velocite_journaliere * 30) / 1000.0

    st.metric("Vélocité Commerciale (Potentiel Récurrent)", f"{velocite_mensuelle:,.0f} k{devise} / mois", 
              help="Capacité de génération mensuelle de chiffre d'affaires basée sur la dynamique actuelle.")

# --- ONGLET 3 : COURBE DE STOBACH (BALEINE) ---
with tab_stobach:
    st.subheader("🐋 Courbe Cumulative de Rentabilité de Stobach (Courbe Baleine)")
    st.caption("Met en évidence les clients ou gammes très rentables qui financent les références non profitables.")

    df_stob = df_vue.groupby(["produit", "canal"], as_index=False)["marge_brute_kmad"].sum()
    df_stob = df_stob.sort_values(by="marge_brute_kmad", ascending=False).reset_index(drop=True)
    df_stob["cumul_marge"] = df_stob["marge_brute_kmad"].cumsum()
    df_stob["pct_profit_cumule"] = (df_stob["cumul_marge"] / df_stob["marge_brute_kmad"].sum()) * 100
    df_stob["segment"] = df_stob["produit"] + " (" + df_stob["canal"] + ")"

    fig_baleine = go.Figure()
    fig_baleine.add_trace(go.Scatter(
        x=df_stob["segment"], y=df_stob["pct_profit_cumule"],
        mode="lines+markers", line=dict(color="#1E3A8A", width=3),
        marker=dict(size=9, color="#3B82F6"),
        text=[f"{v:.1f}%" for v in df_stob["pct_profit_cumule"]],
        hoverinfo="x+text"
    ))
    fig_baleine.add_hline(y=100, line_dash="dash", line_color="#EF4444", annotation_text="100% de la Marge Cible")
    fig_baleine.update_layout(
        title="Courbe de Stobach (% de Profit Cumulé)",
        xaxis_title="Couples Produit / Canal de Distribution",
        yaxis_title="% du Profit Global Cumulé"
    )
    st.plotly_chart(fig_baleine, use_container_width=True)

# --- ONGLET 4 : MATRICE BCG VOLUME / MARGE ---
with tab_bcg:
    st.subheader("📦 Positionnement Stratégique : Volume vs Taux de Marge")
    
    df_bcg = df_vue.groupby("produit", as_index=False).agg({
        "quantite_vendue": "sum",
        "ca_realise_kmad": "sum",
        "marge_brute_kmad": "sum"
    })
    df_bcg["taux_marge"] = (df_bcg["marge_brute_kmad"] / df_bcg["ca_realise_kmad"]) * 100

    fig_quad = px.scatter(
        df_bcg, x="quantite_vendue", y="taux_marge",
        size="ca_realise_kmad", color="produit",
        text="produit",
        title="Matrice Volume vs Rentabilité (Taille = CA)",
        labels={"quantite_vendue": "Volume Vendu (Unités)", "taux_marge": "Taux de Marge (%)"}
    )
    fig_quad.update_traces(textposition="top center")
    fig_quad.add_hline(y=df_bcg["taux_marge"].mean(), line_dash="dot", line_color="gray")
    fig_quad.add_vline(x=df_bcg["quantite_vendue"].mean(), line_dash="dot", line_color="gray")
    st.plotly_chart(fig_quad, use_container_width=True)

# --- ONGLET 5 : RAPPORT COMMERCIAL PDF ---
with tab_pdf:
    st.subheader("📄 Synthèse Commerciale PDF Téléchargeable")

    def generer_pdf_ventes(periode, reg, dev, ca, marge, tx_marge, vol, closing, logo_path):
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        if logo_path.exists():
            pdf.image(str(logo_path), x=15, y=10, w=35)
            pdf.set_xy(55, 15)
        else:
            pdf.set_xy(15, 15)

        pdf.set_font('Helvetica', 'B', 16)
        pdf.set_text_color(30, 58, 138)
        pdf.cell(0, 10, 'NOTE DE SYNTHÈSE COMMERCIALE & OPÉRATIONS', ln=True, align='L' if logo_path.exists() else 'C')

        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(100, 116, 139)
        if logo_path.exists():
            pdf.set_x(55)
        pdf.cell(0, 6, f'Période : {periode} | Périmètre : {reg} | Confidentiel Direction', ln=True)
        pdf.ln(12)

        pdf.set_draw_color(226, 232, 240)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(8)

        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 8, '1. Performance des Ventes & Marges Brutes', ln=True)
        pdf.ln(2)

        pdf.set_font('Helvetica', '', 10)
        pdf.cell(90, 8, f'  - Chiffre d\'Affaires : {ca:,.0f} k{dev}', 1)
        pdf.cell(90, 8, f'  - Marge Commerciale : {marge:,.0f} k{dev}', 1, ln=True)
        pdf.cell(90, 8, f'  - Taux de Marge Brute : {tx_marge:.1f} %', 1)
        pdf.cell(90, 8, f'  - Volume Vendu : {vol:,.0f} unites', 1, ln=True)
        pdf.ln(6)

        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, '2. Efficacité Commerciale & Taux de Transformation', ln=True)
        pdf.ln(2)

        pdf.set_font('Helvetica', '', 10)
        pdf.cell(90, 8, f'  - Taux de Closing Devis : {closing:.1f} %', 1)
        pdf.cell(90, 8, '  - Tendance Pipeline : Active', 1, ln=True)
        pdf.ln(6)

        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, '3. Recommandations Commerciales & Stratégie', ln=True)
        pdf.ln(2)

        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(51, 65, 85)
        avis = (
            f"L'activite commerciale enregistre un chiffre d'affaires consolide de {ca:,.0f} k{dev} "
            f"avec un niveau de marge satisfaisant a {tx_marge:.1f}%.\n"
            f"L'efficacite de closing s'etablit a {closing:.1f}%. "
            "La courbe de Stobach indique une forte concentration de marge sur les gammes phares : "
            "prioriser la fidelisation des grands comptes tout en revoyant les conditions sur les segments dilutifs."
        )
        pdf.multi_cell(180, 5, avis, 1)

        return bytes(pdf.output())

    pdf_ventes_bytes = generer_pdf_ventes(
        mois_choisi, region_choisie, devise,
        ca_total_kmad, marge_totale_kmad, taux_marge_commerciale,
        total_quantites, taux_closing, chemin_logo
    )

    st.download_button(
        label="📥 Télécharger la Synthèse Commerciale (PDF)",
        data=pdf_ventes_bytes,
        file_name=f"Synthese_Commerciale_{mois_choisi}_{region_choisie}.pdf",
        mime="application/pdf"
    )