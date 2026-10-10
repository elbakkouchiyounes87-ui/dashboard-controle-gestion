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
    st.caption("Efficacité commerciale : entonnoir de conversion, marge par produit/canal et analyse Pareto.")

# 2. Chargement des données
@st.cache_data
def charger_donnees_ventes():
    chemin_csv = chemin_racine / "donnees_ventes.csv"
    if not chemin_csv.exists():
        chemin_csv = Path(__file__).resolve().parent / "donnees_ventes.csv"
    if not chemin_csv.exists():
        st.error("Fichier 'donnees_ventes.csv' introuvable à la racine du projet.")
        st.stop()
    return pd.read_csv(chemin_csv)

df_ventes = charger_donnees_ventes()

# 3. Filtres dans la barre latérale
with st.sidebar:
    st.header("⚙️ Paramètres d'Analyse")
    mois_dispo = ["Tous les mois"] + list(df_ventes["mois"].unique())
    mois_choisi = st.selectbox("Période sous revue", mois_dispo, index=0)

    regions_dispo = ["Toutes les régions"] + list(df_ventes["region"].unique())
    region_choisie = st.selectbox("Région Commerciale", regions_dispo, index=0)

    canaux_dispo = ["Tous les canaux"] + list(df_ventes["canal"].unique())
    canal_choisi = st.selectbox("Canal de Distribution", canaux_dispo, index=0)
    devise = st.radio("Devise", ["MAD", "EUR", "USD"])

# Filtrage du DataFrame
df_vue = df_ventes.copy()
if mois_choisi != "Tous les mois":
    df_vue = df_vue[df_vue["mois"] == mois_choisi]
if region_choisie != "Toutes les régions":
    df_vue = df_vue[df_vue["region"] == region_choisie]
if canal_choisi != "Tous les canaux":
    df_vue = df_vue[df_vue["canal"] == canal_choisi]

# 4. Calculs des KPIs Stratégiques
ca_total_kmad = df_vue["ca_realise_kmad"].sum()
marge_totale_kmad = df_vue["marge_brute_kmad"].sum()
taux_marge_commerciale = (marge_totale_kmad / ca_total_kmad * 100) if ca_total_kmad > 0 else 0
total_quantites = df_vue["quantite_vendue"].sum()
prix_moyen_vente = ((ca_total_kmad * 1000) / total_quantites) if total_quantites > 0 else 0

# Pipeline & Conversion
prospects_total = df_vue["prospects"].sum()
devis_total = df_vue["devis_emis"].sum()
gagnes_total = df_vue["opportunites_gagnees"].sum()

taux_transfo_devis = (devis_total / prospects_total * 100) if prospects_total > 0 else 0
taux_succes_global = (gagnes_total / prospects_total * 100) if prospects_total > 0 else 0
taux_closing = (gagnes_total / devis_total * 100) if devis_total > 0 else 0

# 5. Onglets d'analyse
tab_kpis, tab_pipeline, tab_mix, tab_pdf = st.tabs([
    "📊 Synthèse Activité & Marges",
    "🎯 Entonnoir de Vente (Pipeline)",
    "📦 Mix Produits & Analyse ABC",
    "📄 Synthèse Commerciale PDF"
])

# --- ONGLET 1 : SYNTHÈSE ACTIVITÉ & MARGES ---
with tab_kpis:
    st.subheader("Performance Commerciale Globale")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Chiffre d'Affaires", f"{ca_total_kmad:,.0f} k{devise}".replace(",", " "))
    k2.metric("Marge Commerciale", f"{marge_totale_kmad:,.0f} k{devise}".replace(",", " "), f"Taux: {taux_marge_commerciale:.1f}%")
    k3.metric("Volume Vendu", f"{total_quantites:,.0f} unités".replace(",", " "))
    k4.metric("Prix Moyen Unitaire", f"{prix_moyen_vente:,.0f} {devise}".replace(",", " "))

    st.divider()

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

# --- ONGLET 2 : ENTONNOIR DE CONVERSION (FUNNEL) ---
with tab_pipeline:
    st.subheader("Entonnoir de Conversion Commerciale")
    st.caption("Mesure des déperditions entre le premier contact et la signature finale.")

    p1, p2, p3 = st.columns(3)
    p1.metric("Qualification (Prospects -> Devis)", f"{taux_transfo_devis:.1f}%")
    p2.metric("Closing (Devis -> Signatures)", f"{taux_closing:.1f}%")
    p3.metric("Taux de Réussite Global", f"{taux_succes_global:.1f}%", help="Contrats signés / Total prospects contactés")

    # Graphique Funnel Plotly
    fig_funnel = go.Figure(go.Funnel(
        y=["1. Prospects Qualifiés", "2. Devis Émis & Négociation", "3. Contrats Signés (Won)"],
        x=[prospects_total, devis_total, gagnes_total],
        textinfo="value+percent previous",
        marker=dict(color=["#93C5FD", "#3B82F6", "#1E3A8A"])
    ))
    fig_funnel.update_layout(title="Pipeline Commercial Consolidé")
    st.plotly_chart(fig_funnel, use_container_width=True)

    # Diagnostic commercial
    st.markdown("### 🔔 Diagnostic d'Efficacité Commerciale")
    if taux_closing < 35:
        st.warning(f"⚠️ **Alerte Closing :** Le taux de concrétisation des devis est bas ({taux_closing:.1f}%). Revoir les conditions tarifaires ou les délais de réponse aux prospects.")
    else:
        st.success(f"✅ **Excellente efficacité de closing :** {taux_closing:.1f}% des devis aboutissent à une signature.")

# --- ONGLET 3 : MIX PRODUITS & ANALYSE ABC ---
with tab_mix:
    st.subheader("Rentabilité & Poids des Produits (Matrice ABC)")
    
    df_prod = df_vue.groupby("produit", as_index=False).agg({
        "quantite_vendue": "sum",
        "ca_realise_kmad": "sum",
        "marge_brute_kmad": "sum"
    }).sort_values(by="ca_realise_kmad", ascending=False)

    df_prod["taux_marge"] = (df_prod["marge_brute_kmad"] / df_prod["ca_realise_kmad"]) * 100
    df_prod["part_ca_cumulee"] = (df_prod["ca_realise_kmad"].cumsum() / df_prod["ca_realise_kmad"].sum()) * 100

    col_m1, col_m2 = st.columns([3, 2])
    with col_m1:
        fig_prod = px.bar(
            df_prod, x="produit", y=["ca_realise_kmad", "marge_brute_kmad"],
            barmode="group",
            title=f"Performance par Gamme de Produits (k{devise})",
            labels={"value": f"Montant (k{devise})", "variable": "Mesure", "produit": "Gamme"},
            color_discrete_map={"ca_realise_kmad": "#1E3A8A", "marge_brute_kmad": "#10B981"}
        )
        st.plotly_chart(fig_prod, use_container_width=True)

    with col_m2:
        st.markdown("#### Détail Analytique par Produit")
        st.dataframe(
            df_prod[["produit", "quantite_vendue", "ca_realise_kmad", "taux_marge"]].rename(
                columns={
                    "produit": "Produit",
                    "quantite_vendue": "Unités",
                    "ca_realise_kmad": f"CA (k{devise})",
                    "taux_marge": "Marge (%)"
                }
            ).style.format({"Unités": "{:,.0f}", f"CA (k{devise})": "{:,.0f}", "Marge (%)": "{:.1f}%"}),
            use_container_width=True
        )

# --- ONGLET 4 : SYNTHÈSE COMMERCIALE PDF ---
with tab_pdf:
    st.subheader("📄 Génération de la Synthèse Commerciale (PDF)")
    st.write("Éditez un rapport commercial consolidé d'une page pour la direction commerciale et générale.")

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

        # 1. Performance financière
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

        # 2. Pipeline
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, '2. Efficacité Commerciale & Taux de Transformation', ln=True)
        pdf.ln(2)

        pdf.set_font('Helvetica', '', 10)
        pdf.cell(90, 8, f'  - Taux de Closing Devis : {closing:.1f} %', 1)
        pdf.cell(90, 8, '  - Tendance Pipeline : Active', 1, ln=True)
        pdf.ln(6)

        # 3. Observations
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, '3. Recommandations Commerciales & Stratégie', ln=True)
        pdf.ln(2)

        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(51, 65, 85)
        avis = (
            f"L'activite commerciale enregistre un chiffre d'affaires consolide de {ca:,.0f} k{dev} "
            f"avec un niveau de marge satisfaisant a {tx_marge:.1f}%.\n"
            f"L'efficacite de closing s'etablit a {closing:.1f}%. "
            "Il est preconise de concentrer les efforts marketing sur les gammes a forte contribution "
            "et de maintenir la dynamique de developpement sur les canaux a forte rentabilite unitaire."
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