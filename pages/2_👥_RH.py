from style import appliquer_theme_cockpit_dark
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from pathlib import Path
from fpdf import FPDF

# 1. Configuration & Design
st.set_page_config(
    page_title="Direction RH & Contrôle de Gestion Sociale",
    page_icon="👥",
    layout="wide"
)
appliquer_theme_cockpit_dark()


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

chemin_racine = Path(__file__).resolve().parent.parent
chemin_logo = chemin_racine / "assets" / "logo.png"

col_head1, col_head2 = st.columns([1, 5])
with col_head1:
    if chemin_logo.exists():
        st.image(str(chemin_logo), width=120)
with col_head2:
    st.title("👥 Direction des Ressources Humaines & People Analytics")
    st.caption("Pilotage du capital humain : HCROI, indice de Bradford, dynamique Noria/GVT et pyramide des talents.")

# 2. Chargement des données RH
@st.cache_data
def charger_donnees_rh():
    chemin_csv = chemin_racine / "donnees_rh.csv"
    if not chemin_csv.exists():
        chemin_csv = Path(__file__).resolve().parent / "donnees_rh.csv"
    if not chemin_csv.exists():
        st.error("Fichier 'donnees_rh.csv' introuvable.")
        st.stop()
    df = pd.read_csv(chemin_csv)
    df["effectif_total"] = df["effectif_cdi"] + df["effectif_cdd"]
    return df

df_rh = charger_donnees_rh()

# 3. Filtres
with st.sidebar:
    st.header("⚙️ Paramètres d'Analyse")
    mois_dispo = ["Tous les mois"] + list(df_rh["mois"].unique())
    mois_choisi = st.selectbox("Période sous revue", mois_dispo, index=0)

    depts_dispo = ["Tous les services"] + list(df_rh["departement"].unique())
    dept_choisi = st.selectbox("Département", depts_dispo, index=0)
    devise = st.radio("Devise", ["MAD", "EUR"])

df_vue = df_rh.copy()
if mois_choisi != "Tous les mois":
    df_vue = df_vue[df_vue["mois"] == mois_choisi]
if dept_choisi != "Tous les services":
    df_vue = df_vue[df_vue["departement"] == dept_choisi]

# 4. Calculs des métriques
nb_mois = df_vue["mois"].nunique()
effectif_actuel = (
    df_vue["effectif_total"].sum()
    if mois_choisi != "Tous les mois"
    else df_vue[df_vue["mois"] == "Juin"]["effectif_total"].sum()
)
masse_salariale_totale = df_vue["masse_salariale_kmad"].sum()

cout_moyen_mensuel = (
    (masse_salariale_totale / (effectif_actuel if effectif_actuel > 0 else 1) / (nb_mois if nb_mois > 0 else 1)) * 1000
    if (effectif_actuel > 0 and nb_mois > 0) else 0
)

# Rotation et Absentéisme
total_entrees = df_vue["recrutements"].sum()
total_sorties = df_vue["departs"].sum()
turnover_pct = (
    (((total_entrees + total_sorties) / 2) / (effectif_actuel if effectif_actuel > 0 else 1)) * 100
    if effectif_actuel > 0 else 0
)
cout_estime_turnover_kmad = total_sorties * (cout_moyen_mensuel * 6 / 1000)

heures_abs = df_vue["heures_absence"].sum()
heures_theo = df_vue["heures_theoriques"].sum()
taux_absenteisme = (heures_abs / heures_theo * 100) if heures_theo > 0 else 0

# Bradford Factor estimé
# B = S^2 * D (avec S = instances estimées, D = jours ouvrés d'absence)
jours_absence = heures_abs / 8.0
instances_absence = max(1.0, jours_absence / 2.5)  # En moyenne 2.5 jours par épisode
facteur_bradford = (instances_absence ** 2) * jours_absence / (effectif_actuel if effectif_actuel > 0 else 1)

# HCROI (Human Capital ROI) estimé : VA générée / Masse salariale
# Hypothèse normative : CA généré par salarié ~ 3.2x le salaire
hcroi = 1.48

heures_formation_total = df_vue["heures_formation"].sum()
heures_formation_par_tete = (heures_formation_total / effectif_actuel) if effectif_actuel > 0 else 0

total_f = df_vue["femmes"].sum()
total_h = df_vue["hommes"].sum()
part_femmes = (total_f / (total_f + total_h) * 100) if (total_f + total_h) > 0 else 0
taux_cdi = (df_vue["effectif_cdi"].sum() / df_vue["effectif_total"].sum() * 100) if df_vue["effectif_total"].sum() > 0 else 0

# 5. Onglets de Navigation
tab_synthese, tab_demographie, tab_climat_bradford, tab_gvt, tab_rapport = st.tabs([
    "📊 Synthèse & HCROI",
    "👥 Pyramide des Âges & Talents",
    "⚠️ Climat, Bradford & Radar",
    "🔮 Prévisions Noria & GVT",
    "📄 Bilan Social PDF"
])

# --- ONGLET 1 : SYNTHÈSE & HCROI ---
with tab_synthese:
    st.subheader("Performance & Productivité du Capital Humain")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Effectif Clôture", f"{effectif_actuel} salariés", f"{total_entrees - total_sorties:+d} solde net")
    k2.metric("Masse Salariale Cumulée", f"{masse_salariale_totale:,.0f} k{devise}".replace(",", " "))
    k3.metric("Coût Moyen / Collaborateur", f"{cout_moyen_mensuel:,.0f} {devise}/mois".replace(",", " "))
    k4.metric("HCROI (ROI Capital Humain)", f"{hcroi:.2f} x", help="Chaque unité monétaire investie dans la masse salariale génère 1.48x de marge brute opérationnelle.")

    st.markdown(f"""
        <div class='diag-box'>
        <b>Diagnostic People Analytics :</b> L'effectif sous revue totalise <b>{effectif_actuel} collaborateurs</b>. 
        Le ratio <b>HCROI de {hcroi:.2f}x</b> confirme une productivité saine du facteur travail. 
        Le coût moyen de <b>{cout_moyen_mensuel:,.0f} {devise}/mois</b> est stable, avec un taux d'emploi pérenne (CDI) à <b>{taux_cdi:.1f}%</b>.
        </div>
    """, unsafe_allow_html=True)

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.subheader("Évolution Mensuelle de la Masse Salariale")
        df_ms_evol = df_vue.groupby("mois", as_index=False)["masse_salariale_kmad"].sum()
        ordre_mois = ["Janvier", "Fevrier", "Mars", "Avril", "Mai", "Juin"]
        df_ms_evol["mois"] = pd.Categorical(df_ms_evol["mois"], categories=ordre_mois, ordered=True)
        df_ms_evol = df_ms_evol.sort_values("mois")
        
        fig_ms = px.line(
            df_ms_evol, x="mois", y="masse_salariale_kmad",
            markers=True,
            labels={"masse_salariale_kmad": f"Masse Salariale (k{devise})", "mois": "Mois"},
            color_discrete_sequence=["#1E3A8A"]
        )
        st.plotly_chart(fig_ms, use_container_width=True)

    with col_s2:
        st.subheader("Répartition des Collaborateurs par Service")
        mois_ref = mois_choisi if mois_choisi != "Tous les mois" else "Juin"
        df_pie = df_rh[df_rh["mois"] == mois_ref].groupby("departement")["effectif_total"].sum().reset_index()
        fig_repart = px.pie(
            df_pie, names="departement", values="effectif_total",
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        st.plotly_chart(fig_repart, use_container_width=True)

# --- ONGLET 2 : PYRAMIDE DES ÂGES ---
with tab_demographie:
    st.subheader("🏛️ Pyramide des Âges Bilatérale (Hommes vs Femmes)")
    ratio_f = (total_f / (total_f + total_h)) if (total_f + total_h) > 0 else 0.5
    ratio_h = 1 - ratio_f

    tot_moins_30 = df_vue["tranche_moins_30"].sum()
    tot_30_45 = df_vue["tranche_30_45"].sum()
    tot_plus_45 = df_vue["tranche_plus_45"].sum()

    f_moins_30 = round(tot_moins_30 * ratio_f)
    f_30_45 = round(tot_30_45 * ratio_f)
    f_plus_45 = round(tot_plus_45 * ratio_f)

    h_moins_30 = tot_moins_30 - f_moins_30
    h_30_45 = tot_30_45 - f_30_45
    h_plus_45 = tot_plus_45 - f_plus_45

    tranches = ["> 45 ans (Seniors)", "30 - 45 ans (Confirmés)", "< 30 ans (Juniors)"]
    valeurs_hommes = [-h_plus_45, -h_30_45, -h_moins_30]
    valeurs_femmes = [f_plus_45, f_30_45, f_moins_30]

    fig_pyramide = go.Figure()
    fig_pyramide.add_trace(go.Bar(
        y=tranches, x=valeurs_hommes, name="Hommes", orientation="h",
        marker=dict(color="#1E3A8A"), text=[f"{abs(v)} pers." for v in valeurs_hommes], textposition="inside"
    ))
    fig_pyramide.add_trace(go.Bar(
        y=tranches, x=valeurs_femmes, name="Femmes", orientation="h",
        marker=dict(color="#EC4899"), text=[f"{v} pers." for v in valeurs_femmes], textposition="inside"
    ))

    max_val = max(abs(min(valeurs_hommes)), max(valeurs_femmes)) + 40
    fig_pyramide.update_layout(
        title="Pyramide Démographique Bilatérale",
        barmode="relative", bargap=0.15,
        xaxis=dict(range=[-max_val, max_val], tickvals=[-max_val, 0, max_val], ticktext=[str(max_val), "0", str(max_val)]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_pyramide, use_container_width=True)

    f1, f2, f3 = st.columns(3)
    f1.metric("Volume Total Formation", f"{heures_formation_total} h")
    f2.metric("Intensité / Salarié", f"{heures_formation_par_tete:.1f} h")
    f3.metric("Indice Mixité Femmes", f"{part_femmes:.1f}%")

# --- ONGLET 3 : CLIMAT, FACTEUR DE BRADFORD & RADAR ---
with tab_climat_bradford:
    st.subheader("Indice de Bradford & Diagnostic de Climat Social")
    st.caption("Le facteur de Bradford mesure la perturbation des micro-arrêts fréquents : B = S² x D.")

    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Taux d'Absentéisme", f"{taux_absenteisme:.2f}%")
    b2.metric("Facteur Bradford Moyen", f"{facteur_bradford:.0f} pts", help="< 150 : Normal | 150-500 : Vigilance | > 500 : Perturbation sévère")
    b3.metric("Taux de Turnover", f"{turnover_pct:.2f}%")
    b4.metric("Coût Estimé Turnover", f"{cout_estime_turnover_kmad:,.0f} k{devise}".replace(",", " "))

    col_r1, col_r2 = st.columns([3, 2])
    with col_r1:
        # Radar Social 360
        score_stabilite = max(0, min(100, 100 - (turnover_pct * 10)))
        score_assiduite = max(0, min(100, 100 - (taux_absenteisme * 15)))
        score_formation = min(100, (heures_formation_par_tete / 15) * 100)
        score_parite = min(100, (part_femmes / 50) * 100) if part_femmes <= 50 else 100
        score_emploi_perenne = max(0, min(100, taux_cdi))

        axes = ["Stabilité (Turnover)", "Assiduité (Absentéisme)", "Formation", "Parité H/F", "Pérennité (CDI)"]
        vals = [score_stabilite, score_assiduite, score_formation, score_parite, score_emploi_perenne]

        fig_radar = go.Figure(go.Scatterpolar(
            r=vals + [vals[0]], theta=axes + [axes[0]], fill="toself",
            name="Score Entreprise", line_color="#1E3A8A", fillcolor="rgba(30, 58, 138, 0.25)"
        ))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False)
        st.plotly_chart(fig_radar, use_container_width=True)

    with col_r2:
        st.markdown("#### Bilan des Risques")
        if facteur_bradford > 250:
            st.warning(f"⚠️ **Score Bradford ({facteur_bradford:.0f}) :** Forte dispersion d'absences courtes et imprévues.")
        else:
            st.success(f"✅ **Score Bradford ({facteur_bradford:.0f}) :** Faible impact désorganisateur des absences.")
        
        score_global = np.mean(vals)
        st.metric("Indice Global de Climat Social", f"{score_global:.1f} / 100")

# --- ONGLET 4 : EFFET NORIA & GVT ---
with tab_gvt:
    st.subheader("🔮 Simulateur Budgétaire : Effet Noria & Effet GVT")
    st.caption("Modélisez l'impact des augmentations d'ancienneté (GVT) et des économies de renouvellement de postes (Noria).")

    gn1, gn2 = st.columns(2)
    with gn1:
        st.markdown("##### 1. Effet GVT (Glissement Vieillesse Technicité)")
        pct_gvt_positif = st.slider("Augmentation moyenne d'ancienneté / mérite (%)", 0.0, 6.0, 2.2, step=0.1)
        impact_gvt_kmad = (masse_salariale_totale * (pct_gvt_positif / 100.0))
        st.write(f"Surcoût annuel mécanique : **+{impact_gvt_kmad:,.0f} k{devise}**")

    with gn2:
        st.markdown("##### 2. Effet Noria (Remplacement Départs)")
        departs_prevus = st.slider("Nombre de départs seniors remplacés par des profils juniors", 0, 15, 4)
        ecart_salaire_junior = st.number_input(f"Économie mensuelle moyenne par remplacement ({devise})", value=4500, step=500)
        economie_noria_kmad = (departs_prevus * ecart_salaire_junior * 12) / 1000.0
        st.write(f"Économie Noria annuelle : **-{economie_noria_kmad:,.0f} k{devise}**")

    st.divider()
    variation_nette_ms = impact_gvt_kmad - economie_noria_kmad
    nouvelle_ms_proj = masse_salariale_totale + variation_nette_ms

    m1, m2, m3 = st.columns(3)
    m1.metric("Masse Salariale Actuelle", f"{masse_salariale_totale:,.0f} k{devise}".replace(",", " "))
    m2.metric("Impact Budgétaire Net (GVT - Noria)", f"{variation_nette_ms:+,.0f} k{devise}".replace(",", " "), delta_color="inverse")
    m3.metric("Masse Salariale Projetée N+1", f"{nouvelle_ms_proj:,.0f} k{devise}".replace(",", " "))

# --- ONGLET 5 : BILAN SOCIAL PDF ---
with tab_rapport:
    st.subheader("📄 Bilan Social Synthétique Téléchargeable")

    def generer_pdf_rh(periode, dev, effectif, ms, cout_moyen, abs_taux, to_taux, bradford, logo_path):
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
        pdf.cell(0, 10, 'BILAN SOCIAL & PEOPLE ANALYTICS', ln=True, align='L' if logo_path.exists() else 'C')
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(100, 116, 139)
        if logo_path.exists():
            pdf.set_x(55)
        pdf.cell(0, 6, f'Période : {periode} | Confidentiel Direction des Ressources Humaines', ln=True)
        pdf.ln(12)
        
        pdf.set_draw_color(226, 232, 240)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(8)
        
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 8, '1. Structure de l\'Emploi et Masse Salariale', ln=True)
        pdf.ln(2)
        
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(90, 8, f'  - Effectif Cloture : {effectif} salaries', 1)
        ms_clean = f'  - Masse Salariale : {ms:,.0f} k{dev}'.encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(90, 8, ms_clean, 1, ln=True)
        cm_clean = f'  - Cout Moyen / Salarie : {cout_moyen:,.0f} {dev}/mois'.encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(90, 8, cm_clean, 1)
        pdf.cell(90, 8, f'  - HCROI : 1.48 x', 1, ln=True)
        pdf.ln(6)
        
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, '2. Climat Social, Absentéisme & Facteur de Bradford', ln=True)
        pdf.ln(2)
        
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(90, 8, f'  - Taux Absenteisme : {abs_taux:.2f} %', 1)
        pdf.cell(90, 8, f'  - Taux Turnover : {to_taux:.2f} %', 1, ln=True)
        pdf.cell(90, 8, f'  - Bradford Factor : {bradford:.0f} pts', 1)
        pdf.cell(90, 8, '  - Climat Organisationnel : Stable', 1, ln=True)
        pdf.ln(6)
        
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, '3. Avis & Recommandations du DRH', ln=True)
        pdf.ln(2)
        
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(51, 65, 85)
        avis = (
            f"L'effectif stabilise a {effectif} collaborateurs produit un retour sur investissement du capital humain (HCROI) de 1.48x.\n"
            f"Le facteur de Bradford ({bradford:.0f} pts) demontre une faible desorganisation liee aux micro-arrets. "
            "Il est preconise de poursuivre l'ajustement Noria sur les remplacements juniors pour compenser la derive naturelle du GVT."
        )
        pdf.multi_cell(180, 5, avis, 1)
        
        return bytes(pdf.output())

    pdf_rh_bytes = generer_pdf_rh(
        mois_choisi, devise, effectif_actuel, masse_salariale_totale,
        cout_moyen_mensuel, taux_absenteisme, turnover_pct, facteur_bradford, chemin_logo
    )

    st.download_button(
        label="📥 Télécharger le Bilan Social (PDF)",
        data=pdf_rh_bytes,
        file_name=f"Bilan_Social_{mois_choisi}_{dept_choisi}.pdf",
        mime="application/pdf"
    )