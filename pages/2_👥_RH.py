import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from pathlib import Path
from fpdf import FPDF
from auth import verifier_authentification, afficher_bouton_deconnexion
from style import appliquer_theme_cockpit_dark

# 1. Configuration & Sécurité
st.set_page_config(
    page_title="Direction des RH - CHU",
    page_icon="🏥",
    layout="wide"
)

appliquer_theme_cockpit_dark()
verifier_authentification()
afficher_bouton_deconnexion()

# En-tête
chemin_racine = Path(__file__).resolve().parent.parent
chemin_logo = chemin_racine / "assets" / "logo.png"

col_head1, col_head2 = st.columns([1, 5])
with col_head1:
    if chemin_logo.exists():
        st.image(str(chemin_logo), width=110)
    else:
        st.markdown("<h1 style='font-size: 2.8rem; margin:0;'>🏥</h1>", unsafe_allow_html=True)
with col_head2:
    st.title("🏥 Direction des Ressources Humaines & Pilotage Médical - CHU")
    st.caption("People Analytics Hospitalières : suivi des pôles cliniques, absentéisme soignant, facteur Bradford et masse salariale.")

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

# 3. Filtres
with st.sidebar:
    st.header("⚙️ Paramètres d'Analyse CHU")
    mois_dispo = ["Tous les mois"] + list(df_rh["mois"].unique())
    mois_choisi = st.selectbox("Période sous revue", mois_dispo, index=0)

    depts_dispo = ["Tous les pôles"] + list(df_rh["departement"].unique())
    dept_choisi = st.selectbox("Pôle Hospitalier", depts_dispo, index=0)
    devise = st.radio("Devise", ["MAD", "EUR"])

df_vue = df_rh.copy()
if mois_choisi != "Tous les mois":
    df_vue = df_vue[df_vue["mois"] == mois_choisi]
if dept_choisi != "Tous les pôles":
    df_vue = df_vue[df_vue["departement"] == dept_choisi]

# 4. Calculs des Métriques Hospitalières
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

# Bradford Factor (évaluation de l'impact des micro-arrêts)
jours_absence = heures_abs / 8.0
instances_absence = max(1.0, jours_absence / 2.5)
facteur_bradford = (instances_absence ** 2) * jours_absence / (effectif_actuel if effectif_actuel > 0 else 1)

heures_formation_total = df_vue["heures_formation"].sum()
heures_formation_par_tete = (heures_formation_total / effectif_actuel) if effectif_actuel > 0 else 0

total_f = df_vue["femmes"].sum()
total_h = df_vue["hommes"].sum()
part_femmes = (total_f / (total_f + total_h) * 100) if (total_f + total_h) > 0 else 0
taux_titulaires = (df_vue["effectif_cdi"].sum() / df_vue["effectif_total"].sum() * 100) if df_vue["effectif_total"].sum() > 0 else 0

# 5. Onglets de Navigation
tab_synthese, tab_demographie, tab_climat_bradford, tab_gvt, tab_rapport = st.tabs([
    "📊 Synthèse Pôles & Effectifs",
    "👥 Pyramide des Âges Soignants",
    "⚠️ Climat, Bradford & Radar",
    "🔮 Prévisions Noria & GVT Hospitalier",
    "📄 Bilan Social Hospitalier PDF"
])

# --- ONGLET 1 : SYNTHÈSE PÔLES & EFFECTIFS ---
with tab_synthese:
    st.subheader("Effectifs Soignants & Masse Salariale Hospitalière")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Effectif Hospitalier Actif", f"{effectif_actuel} agents", f"{total_entrees - total_sorties:+d} solde net")
    k2.metric("Masse Salariale Cumulée", f"{masse_salariale_totale:,.0f} k{devise}".replace(",", " "))
    k3.metric("Rémunération Moyenne / Agent", f"{cout_moyen_mensuel:,.0f} {devise}/mois".replace(",", " "))
    k4.metric("Taux de Titulaires (Statutaires)", f"{taux_titulaires:.1f}%", help="Part des titulaires vs contractuels/renforts")

    st.markdown(f"""
        <div class='diag-box'>
        <b>Diagnostic RH Hospitalier :</b> Les pôles cliniques mobilisent <b>{effectif_actuel} soignants et praticiens</b>. 
        Le taux d'agents statutaires de <b>{taux_titulaires:.1f}%</b> assure la stabilité des soins. 
        Le coût salarial moyen est de <b>{cout_moyen_mensuel:,.0f} {devise}/agent/mois</b>.
        </div>
    """, unsafe_allow_html=True)

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.subheader("Évolution Mensuelle des Dépenses de Personnel")
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
        st.subheader("Répartition des Effectifs par Pôle Clinique")
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
    st.subheader("🏛️ Pyramide Démographique Médicale & Soignante")
    st.caption("Répartition Hommes / Femmes par génération dans les équipes soignantes du CHU.")

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

    tranches = ["> 45 ans (Praticiens Seniors)", "30 - 45 ans (Confirmés)", "< 30 ans (Internes / Jeunes IDE)"]
    valeurs_hommes = [-h_plus_45, -h_30_45, -h_moins_30]
    valeurs_femmes = [f_plus_45, f_30_45, f_moins_30]

    fig_pyramide = go.Figure()
    fig_pyramide.add_trace(go.Bar(
        y=tranches, x=valeurs_hommes, name="Hommes", orientation="h",
        marker=dict(color="#1E3A8A"), text=[f"{abs(v)} soignants" for v in valeurs_hommes], textposition="inside"
    ))
    fig_pyramide.add_trace(go.Bar(
        y=tranches, x=valeurs_femmes, name="Femmes", orientation="h",
        marker=dict(color="#EC4899"), text=[f"{v} soignantes" for v in valeurs_femmes], textposition="inside"
    ))

    max_val = max(abs(min(valeurs_hommes)), max(valeurs_femmes)) + 30
    fig_pyramide.update_layout(
        title="Pyramide des Âges Bilatérale Hospitalière",
        barmode="relative", bargap=0.15,
        xaxis=dict(range=[-max_val, max_val], tickvals=[-max_val, 0, max_val], ticktext=[str(max_val), "0", str(max_val)]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_pyramide, use_container_width=True)

    f1, f2, f3 = st.columns(3)
    f1.metric("Formation Continue Médicale", f"{heures_formation_total} h")
    f2.metric("Intensité / Agent", f"{heures_formation_par_tete:.1f} h")
    f3.metric("Féminisation des Équipes", f"{part_femmes:.1f}%")

# --- ONGLET 3 : CLIMAT, BRADFORD & RADAR ---
with tab_climat_bradford:
    st.subheader("Taux d'Absentéisme & Facteur de Bradford en Milieu Hospitalier")
    st.caption("Mesure de la désorganisation des gardes : les micro-arrêts fréquents impactent lourdement la continuité des soins.")

    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Taux d'Absentéisme Soignant", f"{taux_absenteisme:.2f}%", delta_color="inverse")
    b2.metric("Facteur Bradford Moyen", f"{facteur_bradford:.0f} pts", help="< 150 : Normal | 150-500 : Vigilance | > 500 : Alerte épuisement")
    b3.metric("Taux de Rotation / Mobilité", f"{turnover_pct:.2f}%", delta_color="inverse")
    b4.metric("Coût Estimé Remplacement", f"{cout_estime_turnover_kmad:,.0f} k{devise}".replace(",", " "))

    col_r1, col_r2 = st.columns([3, 2])
    with col_r1:
        # Radar de Qualité de Vie au Travail (QVT)
        score_stabilite = max(0, min(100, 100 - (turnover_pct * 10)))
        score_assiduite = max(0, min(100, 100 - (taux_absenteisme * 12)))
        score_formation = min(100, (heures_formation_par_tete / 15) * 100)
        score_parite = min(100, (part_femmes / 50) * 100) if part_femmes <= 50 else 100
        score_statut = max(0, min(100, taux_titulaires))

        axes = ["Stabilité Équipes", "Assiduité Soignants", "Formation Continue", "Mixité", "Taux Titularisation"]
        vals = [score_stabilite, score_assiduite, score_formation, score_parite, score_statut]

        fig_radar = go.Figure(go.Scatterpolar(
            r=vals + [vals[0]], theta=axes + [axes[0]], fill="toself",
            name="Score Pôle", line_color="#1E3A8A", fillcolor="rgba(30, 58, 138, 0.25)"
        ))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False)
        st.plotly_chart(fig_radar, use_container_width=True)

    with col_r2:
        st.markdown("#### Diagnostic QVT & Continuité des Soins")
        if taux_absenteisme > 6.0:
            st.warning(f"⚠️ **Tension RH :** Taux d'absentéisme de {taux_absenteisme:.2f}%. Risque de recours excessif aux heures supplémentaires.")
        else:
            st.success(f"✅ **Assiduité satisfaisante :** Absentéisme sous contrôle à {taux_absenteisme:.2f}%.")
        
        score_global = np.mean(vals)
        st.metric("Indice de Climat Hospitalier", f"{score_global:.1f} / 100")

# --- ONGLET 4 : NORIA & GVT HOSPITALIER ---
with tab_gvt:
    st.subheader("🔮 Simulateur Budgétaire : GVT (Échelons) & Noria (Départs en Retraite)")
    st.caption("Modélisez l'avancement d'échelon réglementaire (GVT) et les renouvellements de postes soignants.")

    gn1, gn2 = st.columns(2)
    with gn1:
        st.markdown("##### 1. Glissement Vieillesse Technicité (GVT Statutaire)")
        pct_gvt = st.slider("Avancement moyen d'échelons & ancienneté (%)", 0.0, 5.0, 2.0, step=0.1)
        impact_gvt_kmad = (masse_salariale_totale * (pct_gvt / 100.0))
        st.write(f"Surcoût statutaire mécanique : **+{impact_gvt_kmad:,.0f} k{devise}**")

    with gn2:
        st.markdown("##### 2. Effet Noria Hospitalier")
        departs_seniors = st.slider("Praticiens/IDE seniors remplacés par de jeunes recrues", 0, 20, 6)
        gain_mensuel_poste = st.number_input(f"Écart indiciaire mensuel moyen ({devise})", value=3500, step=500)
        economie_noria_kmad = (departs_seniors * gain_mensuel_poste * 12) / 1000.0
        st.write(f"Économie Noria annuelle : **-{economie_noria_kmad:,.0f} k{devise}**")

    st.divider()
    variation_nette = impact_gvt_kmad - economie_noria_kmad
    ms_proj = masse_salariale_totale + variation_nette

    m1, m2, m3 = st.columns(3)
    m1.metric("Masse Salariale Actuelle", f"{masse_salariale_totale:,.0f} k{devise}".replace(",", " "))
    m2.metric("Variation Nette (GVT - Noria)", f"{variation_nette:+,.0f} k{devise}".replace(",", " "), delta_color="inverse")
    m3.metric("Masse Salariale Projetée N+1", f"{ms_proj:,.0f} k{devise}".replace(",", " "))

# --- ONGLET 5 : BILAN SOCIAL HOSPITALIER PDF ---
with tab_rapport:
    st.subheader("📄 Bilan Social Hospitalier (Format PDF)")

    def generer_pdf_chu_social(periode, pole, dev, effectif, ms, cout_moyen, abs_taux, to_taux, bradford, logo_path):
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
        pdf.cell(0, 10, 'BILAN SOCIAL HOSPITALIER - DIRECTION RH (CHU)', ln=True, align='L' if logo_path.exists() else 'C')
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(100, 116, 139)
        if logo_path.exists():
            pdf.set_x(55)
        pdf.cell(0, 6, f'Période : {periode} | Périmètre : {pole} | Confidentiel Direction', ln=True)
        pdf.ln(12)
        
        pdf.set_draw_color(226, 232, 240)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(8)
        
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 8, '1. Effectifs Soignants et Masse Salariale', ln=True)
        pdf.ln(2)
        
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(90, 8, f'  - Effectif Hospitalier Total : {effectif} agents', 1)
        ms_clean = f'  - Masse Salariale : {ms:,.0f} k{dev}'.encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(90, 8, ms_clean, 1, ln=True)
        cm_clean = f'  - Salaire Moyen / Soignant : {cout_moyen:,.0f} {dev}/mois'.encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(90, 8, cm_clean, 1)
        pdf.cell(90, 8, '  - Continuite Soins : Assuree 24/7', 1, ln=True)
        pdf.ln(6)
        
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, '2. Climat Social, Continuité des Gardes & Bradford', ln=True)
        pdf.ln(2)
        
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(90, 8, f'  - Taux Absenteisme : {abs_taux:.2f} %', 1)
        pdf.cell(90, 8, f'  - Taux Rotation / Mobilité : {to_taux:.2f} %', 1, ln=True)
        pdf.cell(90, 8, f'  - Facteur Bradford : {bradford:.0f} pts', 1)
        pdf.cell(90, 8, '  - Diagnostic Organisationnel : Sous controle', 1, ln=True)
        pdf.ln(6)
        
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, '3. Avis & Recommandations de la Direction RH', ln=True)
        pdf.ln(2)
        
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(51, 65, 85)
        avis = (
            f"Les equipes mobilisent {effectif} agents soignants et medicaux sur le perimetre {pole}.\n"
            f"Le taux d'absenteisme s'eleve a {abs_taux:.2f}% avec un facteur de Bradford de {bradford:.0f} pts. "
            "Il est preconise de veiller au renouvellement previsionnel des profils seniors "
            "et de maintenir une politique incitative sur les services sous tension de garde (Urgences et Reanimation)."
        )
        pdf.multi_cell(180, 5, avis, 1)
        
        return bytes(pdf.output())

    pdf_bytes = generer_pdf_chu_social(
        mois_choisi, dept_choisi, devise, effectif_actuel,
        masse_salariale_totale, cout_moyen_mensuel, taux_absenteisme,
        turnover_pct, facteur_bradford, chemin_logo
    )

    st.download_button(
        label="📥 Télécharger le Bilan Social Hospitalier (PDF)",
        data=pdf_bytes,
        file_name=f"Bilan_Social_CHU_{mois_choisi}_{dept_choisi.replace(' ', '_')}.pdf",
        mime="application/pdf"
    )