import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from pathlib import Path
from fpdf import FPDF

# 1. Configuration et Design CSS "Corporate"
st.set_page_config(
    page_title="Direction Financière - Pilotage & Décision",
    page_icon="💰",
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

st.title("💰 Direction Financière & Contrôle Stratégique")
st.caption("Plateforme décisionnelle d'aide au pilotage de la rentabilité, du cash et des prévisions.")

# 2. Chargement des données
@st.cache_data
def charger_donnees():
    chemin_racine = Path(__file__).resolve().parent.parent
    chemin_csv = chemin_racine / "donnees_controle_gestion.csv"
    if not chemin_csv.exists():
        chemin_csv = Path(__file__).resolve().parent / "donnees_controle_gestion.csv"
    if not chemin_csv.exists():
        st.error("Fichier 'donnees_controle_gestion.csv' introuvable.")
        st.stop()
    return pd.read_csv(chemin_csv)

df = charger_donnees()

# 3. Filtres dans la barre latérale
with st.sidebar:
    st.header("⚙️ Paramètres d'analyse")
    trimestre_filtre = st.selectbox("Période", ["Année Complète", "T1", "T2", "T3", "T4"])
    devise = st.radio("Devise de restitution", ["kMAD", "kEUR", "kUSD"])
    st.divider()
    st.info("💡 **Génération PDF :** Le rapport téléchargeable prend en compte la période sélectionnée ci-dessus.")

df_vue = df if trimestre_filtre == "Année Complète" else df[df["trimestre"] == trimestre_filtre].copy()

# 4. Calculs Financiers Stratégiques
# Agrégats d'exploitation
ca_total = df_vue["ca_realise"].sum()
ca_budget_total = df_vue["ca_budget"].sum()
cogs_total = df_vue["cogs_realise"].sum()
charges_fixes = df_vue["charges_personnel"].sum() + df_vue["autres_charges_fixes"].sum()
ebitda_total = df_vue["ebitda_realise"].sum()
marge_brute = ca_total - cogs_total
taux_marge_brute = (marge_brute / ca_total) if ca_total > 0 else 0

# --- SEUIL DE RENTABILITÉ & POINT MORT ---
# SR = Charges Fixes / Taux de Marge sur Coûts Variables
seuil_rentabilite = (charges_fixes / taux_marge_brute) if taux_marge_brute > 0 else 0
nb_jours_periode = len(df_vue) * 30  # 30 jours conventionnels par mois
point_mort_jours = (seuil_rentabilite / ca_total * nb_jours_periode) if ca_total > 0 else 0
marge_securite = ca_total - seuil_rentabilite
indice_securite = (marge_securite / ca_total * 100) if ca_total > 0 else 0

# --- CYCLE DE CONVERSION DU CASH (CCC) ---
# DSO = (Créances / CA) * jours
# DIO = (Stocks / COGS) * jours
# DPO = (Dettes fournisseurs / COGS) * jours
creances_moy = df_vue["creances_clients"].mean()
stocks_moy = df_vue["stocks"].mean()
dettes_moy = df_vue["dettes_fournisseurs"].mean()

dso = (creances_moy / ca_total * nb_jours_periode) if ca_total > 0 else 0
dio = (stocks_moy / cogs_total * nb_jours_periode) if cogs_total > 0 else 0
dpo = (dettes_moy / cogs_total * nb_jours_periode) if cogs_total > 0 else 0
ccc = dso + dio - dpo  # Cash Conversion Cycle

bfr_actuel = df_vue["creances_clients"].iloc[-1] + df_vue["stocks"].iloc[-1] - df_vue["dettes_fournisseurs"].iloc[-1]
cash_actuel = df_vue["tresorerie_nette"].iloc[-1]

# 5. Affichage des Onglets Principaux
tab_synthese, tab_gestion, tab_prevision, tab_export = st.tabs([
    "📊 Synthèse Direction (KPIs & Alertes)",
    "⚙️ Rentabilité, BFR & Point Mort",
    "🔮 Prévisions & Simulation",
    "📄 Rapport Exécutif PDF"
])

# --- ONGLET 1 : SYNTHÈSE DIRECTION ---
with tab_synthese:
    st.subheader("Performance Globale de la Période")
    c1, c2, c3, c4 = st.columns(4)
    ecart_ca = ((ca_total - ca_budget_total) / ca_budget_total * 100) if ca_budget_total > 0 else 0
    c1.metric("Chiffre d'Affaires", f"{ca_total:,.0f} {devise}".replace(",", " "), f"{ecart_ca:+.1f}% vs Budget")
    c2.metric("Marge Brute", f"{marge_brute:,.0f} {devise}".replace(",", " "), f"Taux: {taux_marge_brute*100:.1f}%")
    c3.metric("EBITDA", f"{ebitda_total:,.0f} {devise}".replace(",", " "), f"{(ebitda_total/ca_total*100):.1f}% du CA")
    c4.metric("Trésorerie Clôture", f"{cash_actuel:,.0f} {devise}".replace(",", " "))

    # Alerte automatique de gestion
    st.markdown("### 🔔 Alertes et Diagnostic Automatisé")
    alert_col1, alert_col2 = st.columns(2)
    with alert_col1:
        if ccc > 90:
            st.warning(f"⚠️ **Attention sur le Cash :** Le cycle de conversion du cash est long ({ccc:.0f} jours). Les liquidités mettent plus de 3 mois à revenir en banque.")
        else:
            st.success(f"✅ **Bonne maîtrise du cycle d'exploitation :** Cycle de cash équilibré ({ccc:.0f} jours).")
    with alert_col2:
        if ca_total >= seuil_rentabilite:
            st.success(f"✅ **Seuil de rentabilité franchi :** L'entreprise dégage une marge de sécurité de {marge_securite:,.0f} {devise} ({indice_securite:.1f}% de marge).")
        else:
            st.error(f"🚨 **Déficit d'exploitation :** Le CA est inférieur au seuil de rentabilité de {(seuil_rentabilite - ca_total):,.0f} {devise}.")

    # Graphique CA Réalisé vs Budget
    fig_ca = px.bar(
        df_vue, x="mois", y=["ca_realise", "ca_budget"],
        barmode="group",
        title=f"Suivi d'Activité Réalisé vs Budget ({devise})",
        labels={"value": f"Montant ({devise})", "variable": "Série", "mois": "Mois"},
        color_discrete_map={"ca_realise": "#1E3A8A", "ca_budget": "#93C5FD"}
    )
    st.plotly_chart(fig_ca, use_container_width=True)

# --- ONGLET 2 : ANALYSE POINT MORT & BFR AVANCÉ ---
with tab_gestion:
    st.subheader("1. Seuil de Rentabilité & Marge de Sécurité")
    pm1, pm2, pm3, pm4 = st.columns(4)
    pm1.metric("Seuil de Rentabilité (SR)", f"{seuil_rentabilite:,.0f} {devise}".replace(",", " "))
    pm2.metric("Point Mort Temporel", f"{point_mort_jours:.0f} jours", help="Nombre de jours d'activité nécessaires pour couvrir les charges fixes.")
    pm3.metric("Marge de Sécurité", f"{marge_securite:,.0f} {devise}".replace(",", " "))
    pm4.metric("Indice de Sécurité", f"{indice_securite:.1f}%", help="Part du CA pouvant être perdue avant d'être en perte.")

    st.divider()

    st.subheader("2. Cycle de Conversion du Cash (Cash Conversion Cycle - CCC)")
    st.caption("Formule standard : **CCC = DSO + DIO - DPO** (temps de transformation des stocks et créances en liquidités).")
    
    ccc_col1, ccc_col2, ccc_col3, ccc_col4 = st.columns(4)
    ccc_col1.metric("CCC (Cycle Global Cash)", f"{ccc:.0f} jours", delta_color="inverse")
    ccc_col2.metric("DSO (Délai Crédit Clients)", f"{dso:.0f} jours")
    ccc_col3.metric("DIO (Rotation des Stocks)", f"{dio:.0f} jours")
    ccc_col4.metric("DPO (Crédit Fournisseurs)", f"{dpo:.0f} jours")

    # Graphique de décomposition du cycle de cash
    fig_ccc = go.Figure(go.Bar(
        x=["DSO (Clients)", "DIO (Stocks)", "DPO (Fournisseurs négatif)", "Cycle Cash (CCC)"],
        y=[dso, dio, -dpo, ccc],
        marker_color=["#3B82F6", "#F59E0B", "#EF4444", "#10B981"],
        text=[f"{v:.0f} j" for v in [dso, dio, -dpo, ccc]],
        textposition="auto"
    ))
    fig_ccc.update_layout(title="Décomposition du Cycle de Trésorerie (en jours)", yaxis_title="Jours")
    st.plotly_chart(fig_ccc, use_container_width=True)

# --- ONGLET 3 : PRÉVISIONS & SIMULATION ---
with tab_prevision:
    st.subheader("Simulateur d'Impact Budgétaire (What-If)")
    sim_c1, sim_c2 = st.columns(2)
    with sim_c1:
        hypothese_ca = st.slider("Hypothèse de croissance CA (%)", -25, 25, 5, step=1)
    with sim_c2:
        hypothese_cogs = st.slider("Variation des coûts matières/achats (%)", -20, 20, 2, step=1)

    ca_proj = ca_total * (1 + hypothese_ca / 100)
    cogs_proj = cogs_total * (1 + hypothese_cogs / 100)
    ebitda_proj = (ca_proj - cogs_proj) - charges_fixes

    res1, res2, res3 = st.columns(3)
    res1.metric("CA Projeté", f"{ca_proj:,.0f} {devise}".replace(",", " "), delta=f"{hypothese_ca:+}%")
    res2.metric("EBITDA Projeté", f"{ebitda_proj:,.0f} {devise}".replace(",", " "), delta=f"{(ebitda_proj - ebitda_total):+,.0f} {devise}")
    res3.metric("Nouveau Seuil Rentabilité", f"{(charges_fixes / ((ca_proj - cogs_proj)/ca_proj)):,.0f} {devise}".replace(",", " "))

# --- ONGLET 4 : GÉNÉRATEUR DE RAPPORT PDF EXÉCUTIF ---
with tab_export:
    st.subheader("📄 Génération de la Synthèse Exécutive (Format PDF)")
    st.write("Ce rapport génère un document PDF d'une page prêt pour la direction générale ou le conseil d'administration.")

    # Fonction de génération PDF avec FPDF2
    def generer_pdf_rapport(periode, dev, ca, ebitda, sr, ccc_val, marge_pct):
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # En-tête
        pdf.set_font('Helvetica', 'B', 18)
        pdf.set_text_color(30, 58, 138)  # Bleu corporate
        pdf.cell(0, 10, 'NOTE DE SYNTHÈSE FINANCIÈRE & GESTION', ln=True, align='C')
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 6, f'Période sous revue : {periode} | Devise : {dev}', ln=True, align='C')
        pdf.ln(8)
        
        # Ligne de séparation
        pdf.set_draw_color(226, 232, 240)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(6)
        
        # Section 1 : Indicateurs Clés
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 8, '1. Performance Économique & Soldes Intermédiaires', ln=True)
        pdf.ln(2)
        
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(90, 8, f'  - Chiffre d\'Affaires Réalisé : {ca:,.0f} {dev}', 1)
        pdf.cell(90, 8, f'  - Taux de Marge Brute : {marge_pct*100:.1f} %', 1, ln=True)
        pdf.cell(90, 8, f'  - EBITDA Réalisé : {ebitda:,.0f} {dev}', 1)
        pdf.cell(90, 8, f'  - Taux d\'EBITDA / CA : {(ebitda/ca*100):.1f} %', 1, ln=True)
        pdf.ln(6)
        
        # Section 2 : Risque & Trésorerie
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, '2. Rentabilité Critique & Cycle d\'Exploitation', ln=True)
        pdf.ln(2)
        
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(90, 8, f'  - Seuil de Rentabilité (SR) : {sr:,.0f} {dev}', 1)
        pdf.cell(90, 8, f'  - Cash Conversion Cycle (CCC) : {ccc_val:.0f} jours', 1, ln=True)
        pdf.ln(6)
        
        # Section 3 : Recommandations du Contrôleur de Gestion
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, '3. Observations & Recommandations Stratégiques', ln=True)
        pdf.ln(2)
        
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(51, 65, 85)
        texte_recommandation = (
            f"L'activité dégage une rentabilité satisfaisante avec un taux de marge brute de {marge_pct*100:.1f}%.\n"
            f"Le seuil critique d'exploitation est fixé à {sr:,.0f} {dev}. "
            f"Le cycle de conversion de cash ({ccc_val:.0f} jours) indique un besoin d'attention continue "
            "sur le recouvrement des créances clients (DSO) et la rotation des stocks pour préserver les liquidités disponibles."
        )
        pdf.multi_cell(180, 5, texte_recommandation, 1)
        
        return bytes(pdf.output())

    # Génération du bouton de téléchargement
    pdf_bytes = generer_pdf_rapport(
        trimestre_filtre, devise, ca_total, ebitda_total, seuil_rentabilite, ccc, taux_marge_brute
    )

    st.download_button(
        label="📥 Télécharger le Rapport Exécutif (PDF)",
        data=pdf_bytes,
        file_name=f"Synthese_Direction_{trimestre_filtre}.pdf",
        mime="application/pdf"
    )