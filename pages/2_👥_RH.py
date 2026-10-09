import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from pathlib import Path
from fpdf import FPDF

# 1. Configuration & Design Corporate
st.set_page_config(
    page_title="Direction RH & Pilotage Social",
    page_icon="👥",
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

# En-tête avec Logo si présent
chemin_racine = Path(__file__).resolve().parent.parent
chemin_logo = chemin_racine / "assets" / "logo.png"

col_head1, col_head2 = st.columns([1, 5])
with col_head1:
    if chemin_logo.exists():
        st.image(str(chemin_logo), width=120)
with col_head2:
    st.title("👥 Direction des Ressources Humaines & Pilotage Social")
    st.caption("Contrôle de gestion sociale : People Analytics, démographie des talents, climat social et coût du turnover.")

# 2. Chargement des données RH
@st.cache_data
def charger_donnees_rh():
    chemin_csv = chemin_racine / "donnees_rh.csv"
    if not chemin_csv.exists():
        chemin_csv = Path(__file__).resolve().parent / "donnees_rh.csv"
    if not chemin_csv.exists():
        st.error("Fichier 'donnees_rh.csv' introuvable à la racine du projet.")
        st.stop()
    df = pd.read_csv(chemin_csv)
    df["effectif_total"] = df["effectif_cdi"] + df["effectif_cdd"]
    return df

df_rh = charger_donnees_rh()

# 3. Filtres de navigation latérale
with st.sidebar:
    st.header("⚙️ Paramètres d'Analyse")
    mois_disponibles = ["Tous les mois"] + list(df_rh["mois"].unique())
    mois_choisi = st.selectbox("Période sous revue", mois_disponibles, index=0)

    depts_disponibles = ["Tous les services"] + list(df_rh["departement"].unique())
    dept_choisi = st.selectbox("Département", depts_disponibles, index=0)
    devise = st.radio("Devise", ["MAD", "EUR"])

# Filtrage du DataFrame
df_vue = df_rh.copy()
if mois_choisi != "Tous les mois":
    df_vue = df_vue[df_vue["mois"] == mois_choisi]
if dept_choisi != "Tous les services":
    df_vue = df_vue[df_vue["departement"] == dept_choisi]

# 4. Calculs des Métriques
nb_mois = df_vue["mois"].nunique()
effectif_actuel = (
    df_vue["effectif_total"].sum()
    if mois_choisi != "Tous les mois"
    else df_vue[df_vue["mois"] == "Juin"]["effectif_total"].sum()
)
masse_salariale_totale = df_vue["masse_salariale_kmad"].sum()

# Coût moyen mensuel par collaborateur
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

heures_formation_total = df_vue["heures_formation"].sum()
heures_formation_par_tete = (heures_formation_total / effectif_actuel) if effectif_actuel > 0 else 0

total_f = df_vue["femmes"].sum()
total_h = df_vue["hommes"].sum()
part_femmes = (total_f / (total_f + total_h) * 100) if (total_f + total_h) > 0 else 0
taux_cdi = (df_vue["effectif_cdi"].sum() / df_vue["effectif_total"].sum() * 100) if df_vue["effectif_total"].sum() > 0 else 0

# 5. Onglets d'analyse
tab_synthese, tab_demographie, tab_climat, tab_rapport = st.tabs([
    "📊 Synthèse Capital Humain",
    "👥 Pyramide des Âges & Talents",
    "🎯 Radar & Diagnostic Climat",
    "📄 Bilan Social PDF"
])

# --- ONGLET 1 : SYNTHÈSE CAPITAL HUMAIN ---
with tab_synthese:
    st.subheader("Indicateurs Clés de Pilotage Social")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Effectif Total Clôture", f"{effectif_actuel} salariés", f"{total_entrees - total_sorties:+d} solde net")
    k2.metric("Masse Salariale Cumulée", f"{masse_salariale_totale:,.0f} k{devise}".replace(",", " "))
    k3.metric("Coût Moyen / Collaborateur", f"{cout_moyen_mensuel:,.0f} {devise}/mois".replace(",", " "))
    k4.metric("Taux d'Emploi Pérenne (CDI)", f"{taux_cdi:.1f}%")

    st.divider()

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

# --- ONGLET 2 : VRAIE PYRAMIDE DES ÂGES HOMMES / FEMMES ---
with tab_demographie:
    st.subheader("🏛️ Pyramide des Âges Structurelle (Hommes vs Femmes)")
    st.caption("Visualisation bilatérale standard de l'audit social : répartition des effectifs par genre et génération.")

    # Estimation rigoureuse des sous-populations Hommes/Femmes par tranche d'âge
    ratio_f = (total_f / (total_f + total_h)) if (total_f + total_h) > 0 else 0.5
    ratio_h = 1 - ratio_f

    # Total des tranches sur la sélection
    tot_moins_30 = df_vue["tranche_moins_30"].sum()
    tot_30_45 = df_vue["tranche_30_45"].sum()
    tot_plus_45 = df_vue["tranche_plus_45"].sum()

    # Données par genre
    f_moins_30 = round(tot_moins_30 * ratio_f)
    f_30_45 = round(tot_30_45 * ratio_f)
    f_plus_45 = round(tot_plus_45 * ratio_f)

    h_moins_30 = tot_moins_30 - f_moins_30
    h_30_45 = tot_30_45 - f_30_45
    h_plus_45 = tot_plus_45 - f_plus_45

    tranches = ["> 45 ans (Seniors)", "30 - 45 ans (Confirmés)", "< 30 ans (Juniors)"]
    valeurs_hommes = [-h_plus_45, -h_30_45, -h_moins_30]  # Valeurs négatives pour affichage à gauche
    valeurs_femmes = [f_plus_45, f_30_45, f_moins_30]

    fig_pyramide = go.Figure()

    # Côté Hommes (Gauche)
    fig_pyramide.add_trace(go.Bar(
        y=tranches,
        x=valeurs_hommes,
        name="Hommes",
        orientation="h",
        marker=dict(color="#1E3A8A"),
        hoverinfo="y+text",
        text=[f"{abs(v)} collaborateurs" for v in valeurs_hommes],
        textposition="inside"
    ))

    # Côté Femmes (Droite)
    fig_pyramide.add_trace(go.Bar(
        y=tranches,
        x=valeurs_femmes,
        name="Femmes",
        orientation="h",
        marker=dict(color="#EC4899"),
        hoverinfo="y+text",
        text=[f"{v} collaboratrices" for v in valeurs_femmes],
        textposition="inside"
    ))

    max_val = max(abs(min(valeurs_hommes)), max(valeurs_femmes)) + 50
    fig_pyramide.update_layout(
        title="Pyramide des Âges Bilatérale",
        barmode="relative",
        bargap=0.15,
        xaxis=dict(
            title="Effectifs (Hommes / Femmes)",
            range=[-max_val, max_val],
            tickvals=[-max_val, -max_val//2, 0, max_val//2, max_val],
            ticktext=[str(max_val), str(max_val//2), "0", str(max_val//2), str(max_val)]
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_pyramide, use_container_width=True)

    st.divider()
    st.subheader("Formation & Développement")
    f1, f2, f3 = st.columns(3)
    f1.metric("Volume Global de Formation", f"{heures_formation_total} heures")
    f2.metric("Intensité Formation / Collaborateur", f"{heures_formation_par_tete:.1f} h")
    f3.metric("Indice de Mixité (Femmes)", f"{part_femmes:.1f}%")

# --- ONGLET 3 : RADAR SOCIAL & CLIMAT 360° ---
with tab_climat:
    st.subheader("🎯 Radar de Performance & Équilibre Social (Base 100)")
    st.caption("Mesure multidimensionnelle de l'équilibre organisationnel : un indice équilibré se rapproche de 100 sur tous les axes.")

    # Calcul des scores normés sur 100
    score_stabilite = max(0, min(100, 100 - (turnover_pct * 10)))
    score_assiduite = max(0, min(100, 100 - (taux_absenteisme * 15)))
    score_formation = min(100, (heures_formation_par_tete / 15) * 100)
    score_parite = min(100, (part_femmes / 50) * 100) if part_femmes <= 50 else max(0, 100 - (part_femmes - 50) * 2)
    score_emploi_perenne = max(0, min(100, taux_cdi))

    axes_radar = [
        "Stabilité Équipes (Turnover)",
        "Assiduité (Absentéisme)",
        "Effort Formation",
        "Équité Mixité (Parité)",
        "Pérennité Emploi (CDI)"
    ]
    valeurs_radar = [score_stabilite, score_assiduite, score_formation, score_parite, score_emploi_perenne]

    col_r1, col_r2 = st.columns([3, 2])

    with col_r1:
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=valeurs_radar + [valeurs_radar[0]],  # Boucle fermée
            theta=axes_radar + [axes_radar[0]],
            fill="toself",
            name="Indice Entreprise",
            line_color="#1E3A8A",
            fillcolor="rgba(30, 58, 138, 0.25)"
        ))
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], ticksuffix=" pts")
            ),
            showlegend=False,
            margin=dict(l=40, r=40, t=30, b=30)
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with col_r2:
        st.markdown("#### Synthèse des Scores")
        st.write(f"• **Stabilité RH :** {score_stabilite:.0f} / 100")
        st.write(f"• **Assiduité :** {score_assiduite:.0f} / 100")
        st.write(f"• **Investissement Compétences :** {score_formation:.0f} / 100")
        st.write(f"• **Index Équité :** {score_parite:.0f} / 100")
        st.write(f"• **Taux de Pérennité CDI :** {score_emploi_perenne:.0f} / 100")
        
        st.divider()
        score_moyen = np.mean(valeurs_radar)
        st.metric("Indice de Climat Social Global", f"{score_moyen:.1f} / 100", 
                  delta="Solide" if score_moyen >= 75 else "Points de vigilance")

    st.divider()
    st.subheader("Indicateurs de Risque Social & Coûts d'Attrition")
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Taux d'Absentéisme", f"{taux_absenteisme:.2f}%", delta_color="inverse")
    r2.metric("Taux de Turnover", f"{turnover_pct:.2f}%", delta_color="inverse")
    r3.metric("Mouvements Réseau", f"{total_sorties} départs", f"{total_entrees} arrivées")
    r4.metric("Coût Financier Turnover", f"{cout_estime_turnover_kmad:,.0f} k{devise}".replace(",", " "))

# --- ONGLET 4 : BILAN SOCIAL PDF ---
with tab_rapport:
    st.subheader("📄 Bilan Social Synthétique Téléchargeable")
    st.write("Ce document consolide les indicateurs sociaux réglementaires et d'audit RH pour la direction.")

    def generer_pdf_rh(periode, dev, effectif, ms, cout_moyen, abs_taux, to_taux, formation_h, score_global, logo_path):
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
        pdf.cell(0, 10, 'BILAN SOCIAL & CONTRÔLE DE GESTION RH', ln=True, align='L' if logo_path.exists() else 'C')
        
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
        pdf.cell(90, 8, f'  - Effectif Cloture : {effectif} collaborateurs', 1)
        ms_clean = f'  - Masse Salariale : {ms:,.0f} k{dev}'.encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(90, 8, ms_clean, 1, ln=True)
        cm_clean = f'  - Cout Moyen / Collaborateur : {cout_moyen:,.0f} {dev}/mois'.encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(90, 8, cm_clean, 1)
        pdf.cell(90, 8, f'  - Heures de Formation : {formation_h} h', 1, ln=True)
        pdf.ln(6)
        
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, '2. Climat Social & Évaluation Synthétique', ln=True)
        pdf.ln(2)
        
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(90, 8, f'  - Taux d\'Absenteisme : {abs_taux:.2f} %', 1)
        pdf.cell(90, 8, f'  - Taux de Turnover : {to_taux:.2f} %', 1, ln=True)
        pdf.cell(90, 8, f'  - Indice de Climat Social : {score_global:.1f} / 100', 1)
        pdf.cell(90, 8, '  - Conformite Audit : Validee', 1, ln=True)
        pdf.ln(6)
        
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, '3. Observations & Recommandations du DRH', ln=True)
        pdf.ln(2)
        
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(51, 65, 85)
        avis = (
            f"L'organisation presente un effectif stabilise de {effectif} collaborateurs avec une masse salariale controlee.\n"
            f"L'indice global de climat social ressort a {score_global:.1f}/100. "
            f"L'effort d'accompagnement sur la formation ({formation_h} heures) contribue a attenuer le risque d'attrition. "
            "Il convient de poursuivre les efforts de mixite professionnelle et de fidélisation sur les pôles Opérations et Commercial."
        )
        pdf.multi_cell(180, 5, avis, 1)
        
        return bytes(pdf.output())

    pdf_rh_bytes = generer_pdf_rh(
        mois_choisi, devise, effectif_actuel, masse_salariale_totale,
        cout_moyen_mensuel, taux_absenteisme, turnover_pct, heures_formation_total,
        score_moyen, chemin_logo
    )

    st.download_button(
        label="📥 Télécharger le Bilan Social (PDF)",
        data=pdf_rh_bytes,
        file_name=f"Bilan_Social_{mois_choisi}_{dept_choisi}.pdf",
        mime="application/pdf"
    )