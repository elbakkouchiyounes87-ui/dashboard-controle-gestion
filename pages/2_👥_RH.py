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
    page_title="Direction des Ressources Humaines & Paie",
    page_icon="👥",
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
        st.markdown("<h1 style='font-size: 2.8rem; margin:0;'>👥</h1>", unsafe_allow_html=True)
with col_head2:
    st.title("👥 Direction des Ressources Humaines & Pilotage de la Paie")
    st.caption("People Analytics d'Entreprise : analyse des effectifs, absentéisme, simulateur de paie et dynamique salariale (Noria/GVT).")

# 2. Chargement des données
@st.cache_data
def charger_donnees_rh():
    chemin_csv = chemin_racine / "donnees_rh.csv"
    if not chemin_csv.exists():
        chemin_csv = Path(__file__).resolve().parent / "donnees_rh.csv"
    if not chemin_csv.exists():
        st.error("Fichier 'donnees_rh.csv' introuvable.")
        st.stop()
    df = pd.read_csv(chemin_csv)
    df["effectif_total"] = df["effectif_cadres"] + df["effectif_tam"] + df["effectif_employes"]
    return df

df_rh = charger_donnees_rh()

# 3. Filtres
with st.sidebar:
    st.header("⚙️ Paramètres d'Analyse")
    mois_dispo = ["Tous les mois"] + list(df_rh["mois"].unique())
    mois_choisi = st.selectbox("Période sous revue", mois_dispo, index=0)

    depts_dispo = ["Tous les départements"] + list(df_rh["departement"].unique())
    dept_choisi = st.selectbox("Département", depts_dispo, index=0)
    devise = st.radio("Devise", ["MAD", "EUR", "USD"])

df_vue = df_rh.copy()
if mois_choisi != "Tous les mois":
    df_vue = df_vue[df_vue["mois"] == mois_choisi]
if dept_choisi != "Tous les départements":
    df_vue = df_vue[df_vue["departement"] == dept_choisi]

# 4. Calculs des Métriques d'Entreprise
nb_mois = df_vue["mois"].nunique()
mois_ref = mois_choisi if mois_choisi != "Tous les mois" else "Juin"

eff_cadres = df_vue["effectif_cadres"].sum() if mois_choisi != "Tous les mois" else df_rh[df_rh["mois"] == mois_ref]["effectif_cadres"].sum()
eff_tam = df_vue["effectif_tam"].sum() if mois_choisi != "Tous les mois" else df_rh[df_rh["mois"] == mois_ref]["effectif_tam"].sum()
eff_employes = df_vue["effectif_employes"].sum() if mois_choisi != "Tous les mois" else df_rh[df_rh["mois"] == mois_ref]["effectif_employes"].sum()
effectif_total = eff_cadres + eff_tam + eff_employes

masse_salariale_totale = df_vue["masse_salariale_kmad"].sum()
primes_totales = df_vue["primes_variables_kmad"].sum()
part_primes = (primes_totales / masse_salariale_totale * 100) if masse_salariale_totale > 0 else 0

cout_moyen_mensuel = (
    (masse_salariale_totale / (effectif_total or 1) / (nb_mois or 1)) * 1000
    if (effectif_total > 0 and nb_mois > 0) else 0
)

# Rotation et Absentéisme
total_entrees = df_vue["recrutements"].sum()
total_sorties = df_vue["departs"].sum()
turnover_pct = (
    (((total_entrees + total_sorties) / 2) / (effectif_total or 1)) * 100
    if effectif_total > 0 else 0
)

heures_abs = df_vue["heures_absence"].sum()
heures_theo = df_vue["heures_theoriques"].sum()
taux_absenteisme = (heures_abs / heures_theo * 100) if heures_theo > 0 else 0

jours_abs = heures_abs / 8.0
instances_abs = max(1.0, jours_abs / 2.5)
facteur_bradford = (instances_abs ** 2) * jours_abs / (effectif_total or 1)

heures_formation_total = df_vue["heures_formation"].sum()
heures_formation_par_tete = (heures_formation_total / effectif_total) if effectif_total > 0 else 0

total_f = df_vue["femmes"].sum()
total_h = df_vue["hommes"].sum()
part_femmes = (total_f / (total_f + total_h) * 100) if (total_f + total_h) > 0 else 0

# 5. Onglets de Navigation
tab_synthese, tab_paie, tab_demographie, tab_climat, tab_noria, tab_pdf = st.tabs([
    "📊 Synthèse RH & Effectifs",
    "💵 Gestion & Simulation de Paie",
    "👥 Pyramide des Âges & Talents",
    "⚠️ Climat, Bradford & Radar",
    "🔮 Prévisions Noria & GVT",
    "📄 Bilan Social PDF"
])

# --- ONGLET 1 : SYNTHÈSE RH ---
with tab_synthese:
    st.subheader("Structure des Effectifs & Masse Salariale")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Effectif Total", f"{effectif_total} collaborateurs", f"{total_entrees - total_sorties:+d} solde net")
    k2.metric("Masse Salariale Cumulée", f"{masse_salariale_totale:,.0f} k{devise}".replace(",", " "))
    k3.metric("Coût Moyen / Collaborateur", f"{cout_moyen_mensuel:,.0f} {devise}/mois".replace(",", " "))
    k4.metric("Part Variable & Primes", f"{part_primes:.1f}%", help="Part des bonus, commissions et heures supplémentaires")

    st.markdown(f"""
        <div class='diag-box'>
        <b>Diagnostic People Analytics :</b> L'effectif sous revue totalise <b>{effectif_total} collaborateurs</b> répartis entre 
        <b>{eff_cadres} Cadres ({(eff_cadres/effectif_total*100):.1f}%)</b>, <b>{eff_tam} Techniciens & Maîtrise</b> et <b>{eff_employes} Employés/Opérateurs</b>. 
        Le coût salarial moyen est de <b>{cout_moyen_mensuel:,.0f} {devise}/salarié/mois</b> avec une composante variable maîtrisée à <b>{part_primes:.1f}%</b>.
        </div>
    """, unsafe_allow_html=True)

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("Structure Socio-Professionnelle par Département")
        df_dept = df_rh[df_rh["mois"] == mois_ref].groupby("departement")[["effectif_cadres", "effectif_tam", "effectif_employes"]].sum().reset_index()
        fig_tri = px.bar(
            df_dept, x="departement", y=["effectif_cadres", "effectif_tam", "effectif_employes"],
            barmode="stack", labels={"value": "Effectif", "departement": "Département"},
            title="Ventilation Cadres / TAM / Employés",
            color_discrete_map={"effectif_cadres": "#1E3A8A", "effectif_tam": "#0284C7", "effectif_employes": "#10B981"}
        )
        st.plotly_chart(fig_tri, use_container_width=True)

    with col_g2:
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

# --- ONGLET 2 : GESTION & SIMULATION DE PAIE ---
with tab_paie:
    st.subheader("💵 Simulateur de Bulletin de Paie d'Entreprise")
    st.caption("Calcul des composantes de paie : Salaire brut, cotisations salariales, impôt sur le revenu, salaire net et charges patronales.")

    col_sim1, col_sim2 = st.columns(2)
    with col_sim1:
        st.markdown("#### 1. Rémunération Brute du Collaborateur")
        statut_sal = st.selectbox("Statut du salarié :", ["Cadre Supérieur / Dirigeant", "Cadre Moyen / Ingénieur", "Technicien / Maîtrise", "Employé / Opérateur"])
        
        bareme_ent = {
            "Cadre Supérieur / Dirigeant": {"base": 24000.0, "prime": 4000.0, "avantage": 2000.0},
            "Cadre Moyen / Ingénieur": {"base": 14000.0, "prime": 2000.0, "avantage": 800.0},
            "Technicien / Maîtrise": {"base": 7500.0, "prime": 1000.0, "avantage": 300.0},
            "Employé / Opérateur": {"base": 4800.0, "prime": 500.0, "avantage": 0.0}
        }
        ref_sal = bareme_ent[statut_sal]

        salaire_base = st.number_input(f"Salaire de base mensuel ({devise})", value=ref_sal["base"], step=200.0)
        primes_variables = st.number_input(f"Primes d'objectifs & commissions ({devise})", value=ref_sal["prime"], step=100.0)
        avantages_nature = st.number_input(f"Avantages en nature / indemnités ({devise})", value=ref_sal["avantage"], step=100.0)

    with col_sim2:
        st.markdown("#### 2. Déductions & Charges Sociales")
        taux_retraite_sal = st.number_input("Cotisation Retraite Salarié (%)", value=6.0, step=0.5) / 100.0
        taux_couverture_sante = st.number_input("Assurance Maladie / Mutuelle (%)", value=3.0, step=0.2) / 100.0
        nb_personnes_charge = st.slider("Nombre de personnes à charge (déduction fiscale)", 0, 6, 2)
        charges_patronales_pct = st.number_input("Taux global charges patronales employeur (%)", value=20.0, step=0.5) / 100.0

    # Calculs de Paie
    brut_total = salaire_base + primes_variables + avantages_nature
    cotisations_salariales = brut_total * (taux_retraite_sal + taux_couverture_sante)
    
    # Base imposable et barème progressif indicatif
    frais_pro = min(brut_total * 0.20, 2500.0)
    net_imposable = max(0.0, brut_total - cotisations_salariales - frais_pro)

    if net_imposable <= 2500:
        ir_brut = 0.0
    elif net_imposable <= 4166:
        ir_brut = (net_imposable - 2500) * 0.10
    elif net_imposable <= 5000:
        ir_brut = (net_imposable * 0.20) - 416.67
    elif net_imposable <= 6666:
        ir_brut = (net_imposable * 0.30) - 916.67
    elif net_imposable <= 15000:
        ir_brut = (net_imposable * 0.34) - 1183.33
    else:
        ir_brut = (net_imposable * 0.38) - 1783.33

    abattement_famille = nb_personnes_charge * 30.0
    ir_net = max(0.0, ir_brut - abattement_famille)

    salaire_net = brut_total - cotisations_salariales - ir_net
    charges_patronales = brut_total * charges_patronales_pct
    cout_global_employeur = brut_total + charges_patronales

    st.divider()
    st.subheader("3. Décomposition du Bulletin de Paie")
    
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Salaire Brut Total", f"{brut_total:,.2f} {devise}".replace(",", " "))
    p2.metric("Charges Salariales", f"-{cotisations_salariales:,.2f} {devise}".replace(",", " "), delta_color="inverse")
    p3.metric("Impôt sur le Revenu (IR)", f"-{ir_net:,.2f} {devise}".replace(",", " "), delta_color="inverse")
    p4.metric("Salaire Net à Payer", f"{salaire_net:,.2f} {devise}".replace(",", " "))

    st.write(f"💼 **Coût Total Entreprise (Super-Brut) :** `{cout_global_employeur:,.2f} {devise}` (dont `{charges_patronales:,.2f} {devise}` de charges patronales).")

    # Édition PDF Bulletin
    def generer_pdf_bulletin(statut, s_base, s_prime, s_av, brut, c_sal, ir, net, cout_tot, dev, logo_p):
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        if logo_p.exists():
            pdf.image(str(logo_p), x=15, y=12, w=30)
            pdf.set_xy(50, 15)
        else:
            pdf.set_xy(15, 15)
            
        pdf.set_font('Helvetica', 'B', 15)
        pdf.set_text_color(30, 58, 138)
        pdf.cell(0, 8, "BULLETIN DE PAIE - SYNTHÈSE MENSUELLE", ln=True)
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(100, 116, 139)
        if logo_p.exists():
            pdf.set_x(50)
        pdf.cell(0, 6, f"Profil : {statut} | Direction des Ressources Humaines", ln=True)
        pdf.ln(10)
        
        pdf.set_draw_color(226, 232, 240)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(6)
        
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 7, "1. ÉLÉMENTS DU SALAIRE BRUT", ln=True)
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(120, 7, "  - Salaire de base contractuel", 1)
        pdf.cell(60, 7, f"{s_base:,.2f} {dev}", 1, ln=True, align="R")
        pdf.cell(120, 7, "  - Primes et bonus de performance", 1)
        pdf.cell(60, 7, f"{s_prime:,.2f} {dev}", 1, ln=True, align="R")
        pdf.cell(120, 7, "  - Indemnites et avantages", 1)
        pdf.cell(60, 7, f"{s_av:,.2f} {dev}", 1, ln=True, align="R")
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(120, 7, "TOTAL SALAIRE BRUT", 1)
        pdf.cell(60, 7, f"{brut:,.2f} {dev}", 1, ln=True, align="R")
        pdf.ln(6)
        
        pdf.cell(0, 7, "2. DÉDUCTIONS OBLIGATOIRES & RETENUES", ln=True)
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(120, 7, "  - Cotisations de securite sociale et retraite", 1)
        pdf.cell(60, 7, f"-{c_sal:,.2f} {dev}", 1, ln=True, align="R")
        pdf.cell(120, 7, "  - Retenue Impot sur le Revenu (IR)", 1)
        pdf.cell(60, 7, f"-{ir:,.2f} {dev}", 1, ln=True, align="R")
        pdf.ln(6)
        
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_fill_color(239, 246, 255)
        pdf.cell(120, 9, "NET À PAYER AU SALARIÉ", 1, fill=True)
        pdf.cell(60, 9, f"{net:,.2f} {dev}", 1, ln=True, align="R", fill=True)
        pdf.ln(4)
        
        pdf.set_font('Helvetica', 'I', 8)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 6, f"Coût global employeur supporte par l'entreprise : {cout_tot:,.2f} {dev}", ln=True)
        return bytes(pdf.output())

    pdf_paie_bytes = generer_pdf_bulletin(
        statut_sal, salaire_base, primes_variables, avantages_nature,
        brut_total, cotisations_salariales, ir_net, salaire_net,
        cout_global_employeur, devise, chemin_logo
    )

    st.download_button(
        label="📥 Télécharger le Bulletin de Paie Simulé (PDF)",
        data=pdf_paie_bytes,
        file_name=f"Bulletin_Paie_{statut_sal.replace(' ', '_')}.pdf",
        mime="application/pdf"
    )

# --- ONGLET 3 : PYRAMIDE DES ÂGES ---
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

    max_val = max(abs(min(valeurs_hommes)), max(valeurs_femmes)) + 30
    fig_pyramide.update_layout(
        title="Pyramide Démographique de l'Entreprise",
        barmode="relative", bargap=0.15,
        xaxis=dict(range=[-max_val, max_val], tickvals=[-max_val, 0, max_val], ticktext=[str(max_val), "0", str(max_val)]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_pyramide, use_container_width=True)

    d1, d2, d3 = st.columns(3)
    d1.metric("Formation Continue", f"{heures_formation_total} h")
    d2.metric("Intensité / Collaborateur", f"{heures_formation_par_tete:.1f} h")
    d3.metric("Mixité (Femmes)", f"{part_femmes:.1f}%")

# --- ONGLET 4 : CLIMAT SOCIAL, BRADFORD & RADAR ---
with tab_climat:
    st.subheader("Absentéisme & Facteur de Perturbation de Bradford")
    st.caption("Le facteur de Bradford mesure la perturbation des micro-arrêts fréquents : B = S² x D.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Taux d'Absentéisme", f"{taux_absenteisme:.2f}%")
    c2.metric("Facteur Bradford Moyen", f"{facteur_bradford:.0f} pts", help="< 150 : Normal | 150-500 : Vigilance | > 500 : Perturbation sévère")
    c3.metric("Taux de Turnover", f"{turnover_pct:.2f}%")
    c4.metric("Coût Estimé Turnover", f"{(total_sorties * cout_moyen_mensuel * 6 / 1000):,.0f} k{devise}".replace(",", " "))

    col_r1, col_r2 = st.columns([3, 2])
    with col_r1:
        score_stabilite = max(0, min(100, 100 - (turnover_pct * 10)))
        score_assiduite = max(0, min(100, 100 - (taux_absenteisme * 15)))
        score_formation = min(100, (heures_formation_par_tete / 15) * 100)
        score_parite = min(100, (part_femmes / 50) * 100) if part_femmes <= 50 else 100
        score_cadres = min(100, (eff_cadres / effectif_total) * 300) if effectif_total > 0 else 50

        axes = ["Stabilité (Turnover)", "Assiduité", "Formation Continue", "Mixité H/F", "Taux d'Encadrement"]
        vals = [score_stabilite, score_assiduite, score_formation, score_parite, score_cadres]

        fig_radar = go.Figure(go.Scatterpolar(
            r=vals + [vals[0]], theta=axes + [axes[0]], fill="toself",
            name="Score Entreprise", line_color="#1E3A8A", fillcolor="rgba(30, 58, 138, 0.25)"
        ))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False)
        st.plotly_chart(fig_radar, use_container_width=True)

    with col_r2:
        st.markdown("#### Diagnostic de Climat Social")
        if facteur_bradford > 250:
            st.warning(f"⚠️ **Score Bradford ({facteur_bradford:.0f}) :** Forte récurrence de micro-absences imprévues.")
        else:
            st.success(f"✅ **Score Bradford ({facteur_bradford:.0f}) :** Faible impact désorganisateur des arrêts.")
        
        st.metric("Indice Global QVT & Climat", f"{np.mean(vals):.1f} / 100")

# --- ONGLET 5 : EFFET NORIA & GVT ---
with tab_noria:
    st.subheader("🔮 Simulateur Budgétaire : Effet Noria & Effet GVT")
    st.caption("Modélisez l'impact des augmentations d'ancienneté (GVT) et des économies de remplacement de postes (Noria).")

    gn1, gn2 = st.columns(2)
    with gn1:
        st.markdown("##### 1. Effet GVT (Augmentations & Mérite)")
        pct_gvt = st.slider("Augmentation moyenne d'ancienneté / mérite (%)", 0.0, 6.0, 2.0, step=0.1)
        impact_gvt_kmad = (masse_salariale_totale * (pct_gvt / 100.0))
        st.write(f"Surcoût annuel mécanique : **+{impact_gvt_kmad:,.0f} k{devise}**")

    with gn2:
        st.markdown("##### 2. Effet Noria (Remplacement Départs)")
        departs_seniors = st.slider("Nombre de départs seniors remplacés par des profils juniors", 0, 15, 4)
        ecart_mensuel = st.number_input(f"Économie mensuelle moyenne par remplacement ({devise})", value=4000, step=500)
        economie_noria_kmad = (departs_seniors * ecart_mensuel * 12) / 1000.0
        st.write(f"Économie Noria annuelle : **-{economie_noria_kmad:,.0f} k{devise}**")

    st.divider()
    variation_nette = impact_gvt_kmad - economie_noria_kmad
    nouvelle_ms = masse_salariale_totale + variation_nette

    m1, m2, m3 = st.columns(3)
    m1.metric("Masse Salariale Actuelle", f"{masse_salariale_totale:,.0f} k{devise}".replace(",", " "))
    m2.metric("Variation Nette (GVT - Noria)", f"{variation_nette:+,.0f} k{devise}".replace(",", " "), delta_color="inverse")
    m3.metric("Masse Salariale Projetée N+1", f"{nouvelle_ms:,.0f} k{devise}".replace(",", " "))

# --- ONGLET 6 : BILAN SOCIAL PDF ---
with tab_pdf:
    st.subheader("📄 Bilan Social Corporate Téléchargeable (PDF)")

    def generer_pdf_social_entreprise(periode, dpt, dev, eff, ms, cm, abs_tx, to_tx, brad, logo_p):
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        if logo_p.exists():
            pdf.image(str(logo_p), x=15, y=10, w=35)
            pdf.set_xy(55, 15)
        else:
            pdf.set_xy(15, 15)
            
        pdf.set_font('Helvetica', 'B', 16)
        pdf.set_text_color(30, 58, 138)
        pdf.cell(0, 10, 'BILAN SOCIAL & PEOPLE ANALYTICS', ln=True, align='L' if logo_p.exists() else 'C')
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(100, 116, 139)
        if logo_p.exists():
            pdf.set_x(55)
        pdf.cell(0, 6, f'Période : {periode} | Périmètre : {dpt} | Confidentiel Direction', ln=True)
        pdf.ln(12)
        
        pdf.set_draw_color(226, 232, 240)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(8)
        
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 8, '1. Structure de l\'Emploi et Masse Salariale', ln=True)
        pdf.ln(2)
        
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(90, 8, f'  - Effectif Total : {eff} salaries', 1)
        ms_c = f'  - Masse Salariale : {ms:,.0f} k{dev}'.encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(90, 8, ms_c, 1, ln=True)
        cm_c = f'  - Cout Moyen / Salarie : {cm:,.0f} {dev}/mois'.encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(90, 8, cm_c, 1)
        pdf.cell(90, 8, '  - Taux Encadrement : Conforme', 1, ln=True)
        pdf.ln(6)
        
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, '2. Climat Social, Absentéisme & Stabilité', ln=True)
        pdf.ln(2)
        
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(90, 8, f'  - Taux Absenteisme : {abs_tx:.2f} %', 1)
        pdf.cell(90, 8, f'  - Taux de Turnover : {to_tx:.2f} %', 1, ln=True)
        pdf.cell(90, 8, f'  - Facteur Bradford : {brad:.0f} pts', 1)
        pdf.cell(90, 8, '  - Climat Global : Favorable', 1, ln=True)
        pdf.ln(6)
        
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, '3. Avis & Recommandations du DRH', ln=True)
        pdf.ln(2)
        
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(51, 65, 85)
        avis = (
            f"L'effectif stabilise a {eff} collaborateurs produit une activite reguliere sur le perimetre {dpt}.\n"
            f"L'absenteisme ressort a {abs_tx:.2f}% avec un score Bradford de {brad:.0f} pts demontrant une bonne continuite d'equipe. "
            "Il est preconise de poursuivre les arbitrages Noria sur les remplacements seniors afin de neutraliser l'impact mecanique du GVT."
        )
        pdf.multi_cell(180, 5, avis, 1)
        return bytes(pdf.output())

    pdf_social_bytes = generer_pdf_social_entreprise(
        mois_choisi, dept_choisi, devise, effectif_total,
        masse_salariale_totale, cout_moyen_mensuel, taux_absenteisme,
        turnover_pct, facteur_bradford, chemin_logo
    )

    st.download_button(
        label="📥 Télécharger le Bilan Social (PDF)",
        data=pdf_social_bytes,
        file_name=f"Bilan_Social_{mois_choisi}_{dept_choisi.replace(' ', '_')}.pdf",
        mime="application/pdf"
    )