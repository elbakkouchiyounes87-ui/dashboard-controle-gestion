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
    page_title="CGRH & Gestion de la Paie - CHU",
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
    st.title("🏥 Pilotage CGRH & Contrôle de la Paie Hospitalière - CHU")
    st.caption("Pilotage global des effectifs hospitaliers, ratios d'encadrement, décomposition salariale et émission des fiches de paie.")

# 2. Chargement des données CHU
@st.cache_data
def charger_donnees_chu():
    chemin_csv = chemin_racine / "donnees_rh.csv"
    if not chemin_csv.exists():
        chemin_csv = Path(__file__).resolve().parent / "donnees_rh.csv"
    if not chemin_csv.exists():
        st.error("Fichier 'donnees_rh.csv' introuvable.")
        st.stop()
    df = pd.read_csv(chemin_csv)
    df["effectif_total"] = df["effectif_medecins"] + df["effectif_infirmiers"] + df["effectif_admin"]
    return df

df_chu = charger_donnees_chu()

# 3. Barre Latérale
with st.sidebar:
    st.header("⚙️ Filtres Hospitaliers")
    mois_dispo = ["Tous les mois"] + list(df_chu["mois"].unique())
    mois_choisi = st.selectbox("Période sous revue", mois_dispo, index=0)

    poles_dispo = ["Tous les pôles"] + list(df_chu["pole"].unique())
    pole_choisi = st.selectbox("Pôle Clinique", poles_dispo, index=0)
    devise = st.radio("Devise de restitution", ["MAD", "EUR"])

df_vue = df_chu.copy()
if mois_choisi != "Tous les mois":
    df_vue = df_vue[df_vue["mois"] == mois_choisi]
if pole_choisi != "Tous les pôles":
    df_vue = df_vue[df_vue["pole"] == pole_choisi]

# 4. Calculs des Métriques
nb_mois = df_vue["mois"].nunique()
mois_ref = mois_choisi if mois_choisi != "Tous les mois" else "Juin"

eff_medecins = df_vue["effectif_medecins"].sum() if mois_choisi != "Tous les mois" else df_chu[df_chu["mois"] == mois_ref]["effectif_medecins"].sum()
eff_infirmiers = df_vue["effectif_infirmiers"].sum() if mois_choisi != "Tous les mois" else df_chu[df_chu["mois"] == mois_ref]["effectif_infirmiers"].sum()
eff_admin = df_vue["effectif_admin"].sum() if mois_choisi != "Tous les mois" else df_chu[df_chu["mois"] == mois_ref]["effectif_admin"].sum()
effectif_total_chu = eff_medecins + eff_infirmiers + eff_admin

lits_ouverts_total = df_vue["lits_ouverts"].sum() if mois_choisi != "Tous les mois" else df_chu[df_chu["mois"] == mois_ref]["lits_ouverts"].sum()
total_jh = df_vue["journees_hospitalisation"].sum()

masse_salariale_totale = df_vue["masse_salariale_kmad"].sum()
gardes_totales = df_vue["gardes_astreintes_kmad"].sum()
part_gardes = (gardes_totales / masse_salariale_totale * 100) if masse_salariale_totale > 0 else 0

ratio_ide_lit = eff_infirmiers / lits_ouverts_total if lits_ouverts_total > 0 else 0
ratio_med_lit = eff_medecins / lits_ouverts_total if lits_ouverts_total > 0 else 0
cout_rh_par_jh = (masse_salariale_totale * 1000) / total_jh if total_jh > 0 else 0

jours_abs = df_vue["abs_maladie_jours"].sum()
taux_absenteisme = (jours_abs / (effectif_total_chu * 22 * nb_mois)) * 100 if (effectif_total_chu * nb_mois) > 0 else 0

# 5. Onglets
tab_synthese, tab_paie, tab_ratios, tab_cout_jh, tab_pdf = st.tabs([
    "📊 Synthèse CGRH Pôles",
    "💵 Gestion & Simulation de Paie CHU",
    "🩺 Ratios de Charge & Gardes",
    "💰 Coût RH / Journée (JH)",
    "📄 Note Exécutive CGRH & Paie (PDF)"
])

# --- ONGLET 1 : SYNTHÈSE CGRH ---
with tab_synthese:
    st.subheader("Structure des Métiers & Masse Globale")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Corps Médical (PHU/Praticiens)", f"{eff_medecins} médecins", f"{(eff_medecins/effectif_total_chu*100):.1f}% de l'effectif")
    k2.metric("Personnel Soignant (IDE/AS)", f"{eff_infirmiers} soignants", f"{(eff_infirmiers/effectif_total_chu*100):.1f}% de l'effectif")
    k3.metric("Personnel Administratif (PATL)", f"{eff_admin} agents", f"Ratio support : {(eff_admin/(eff_medecins+eff_infirmiers)*100):.1f}%")
    k4.metric("Masse Salariale Totale", f"{masse_salariale_totale:,.0f} k{devise}".replace(",", " "), f"Gardes/Astreintes : {part_gardes:.1f}%")

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        df_poles = df_chu[df_chu["mois"] == mois_ref].groupby("pole")[["effectif_medecins", "effectif_infirmiers", "effectif_admin"]].sum().reset_index()
        fig_tri = px.bar(
            df_poles, x="pole", y=["effectif_medecins", "effectif_infirmiers", "effectif_admin"],
            barmode="stack", labels={"value": "Effectif (ETP)", "pole": "Pôle Clinique"},
            title="Ventilation Corps Médical / Soins / Administration",
            color_discrete_map={"effectif_medecins": "#1E3A8A", "effectif_infirmiers": "#0284C7", "effectif_admin": "#10B981"}
        )
        st.plotly_chart(fig_tri, use_container_width=True)

    with col_g2:
        salaires_base = masse_salariale_totale - gardes_totales
        fig_pie_ms = px.pie(
            names=["Traitements Indiciaires de Base", "Gardes, Astreintes & Sujétions"],
            values=[salaires_base, gardes_totales], hole=0.45,
            title=f"Répartition du Budget de Rémunération ({devise})",
            color_discrete_sequence=["#1E3A8A", "#F59E0B"]
        )
        st.plotly_chart(fig_pie_ms, use_container_width=True)

# --- ONGLET 2 : GESTION & SIMULATION DE PAIE CHU ---
with tab_paie:
    st.subheader("💵 Moteur de Calcul & Simulateur de Bulletin de Paie Hospitalière")
    st.caption("Modélisation des régimes de rémunération hospitalière : traitement de base, sujétions de garde, cotisations sociales et impôt.")

    col_sim1, col_sim2 = st.columns([1, 1])

    with col_sim1:
        st.markdown("#### 1. Profil de l'Agent Hospitalier")
        categorie_agent = st.selectbox(
            "Corps professionnel :",
            ["Médecin Spécialiste / PHU", "Infirmier Diplômé d'État (IDE)", "Aide-Soignant (AS)", "Cadre Administratif / Gestionnaire"]
        )
        
        # Valeurs de référence indiciaires
        bareme_base = {
            "Médecin Spécialiste / PHU": {"base": 14000.0, "taux_garde": 800.0, "indem_spec": 3500.0},
            "Infirmier Diplômé d'État (IDE)": {"base": 6200.0, "taux_garde": 250.0, "indem_spec": 1200.0},
            "Aide-Soignant (AS)": {"base": 4200.0, "taux_garde": 150.0, "indem_spec": 700.0},
            "Cadre Administratif / Gestionnaire": {"base": 7500.0, "taux_garde": 0.0, "indem_spec": 900.0}
        }
        params_agent = bareme_base[categorie_agent]

        traitement_base = st.number_input(f"Traitement de Base Indiciaire ({devise})", value=params_agent["base"], step=200.0)
        prime_technicite = st.number_input(f"Indemnité de Fonction / Risque / Technicité ({devise})", value=params_agent["indem_spec"], step=100.0)
        
        st.markdown("##### Sujétions de Permanence des Soins")
        nb_gardes = st.slider("Nombre de gardes de 12h effectuées dans le mois", 0, 10, 3 if "Administratif" not in categorie_agent else 0)
        taux_unitaire_garde = st.number_input(f"Indemnité brute par garde ({devise})", value=params_agent["taux_garde"], step=50.0)

    with col_sim2:
        st.markdown("#### 2. Déductions & Cotisations Sociales")
        taux_retraite = st.number_input("Cotisation Retraite (ex: CMR / RCAR) (%)", value=10.0, step=0.5) / 100.0
        taux_couverture_sante = st.number_input("Assurance Maladie Obligatoire (CNOPS / Mutuelle) (%)", value=2.5, step=0.1) / 100.0
        nb_deductions_charge = st.slider("Nombre de personnes à charge (abattement fiscal)", 0, 6, 2)
        charges_patronales_pct = st.number_input("Charges patronales employeur CHU (%)", value=15.0, step=0.5) / 100.0

    # Moteur de calcul de la paie
    total_gardes_val = nb_gardes * taux_unitaire_garde
    salaire_brut_global = traitement_base + prime_technicite + total_gardes_val

    # Retenues sociales
    retenue_retraite = (traitement_base + prime_technicite) * taux_retraite
    retenue_sante = salaire_brut_global * taux_couverture_sante
    total_retenues_sociales = retenue_retraite + retenue_sante

    # Base imposable (Brut imposable - charges sociales - déduction forfaitaire pour frais pro)
    frais_pro_forfait = min(salaire_brut_global * 0.20, 2500.0)
    net_imposable = max(0.0, salaire_brut_global - total_retenues_sociales - frais_pro_forfait)

    # Barème progressif IR indicatif
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

    abattement_charges = nb_deductions_charge * 30.0
    ir_net = max(0.0, ir_brut - abattement_charges)

    salaire_net_a_payer = salaire_brut_global - total_retenues_sociales - ir_net
    cout_total_chu = salaire_brut_global * (1 + charges_patronales_pct)

    st.divider()
    st.subheader("3. Décomposition du Bulletin de Paie Hospitalier")
    
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Salaire Brut Global", f"{salaire_brut_global:,.2f} {devise}".replace(",", " "))
    p2.metric("Retenues Sociales (Employé)", f"-{total_retenues_sociales:,.2f} {devise}".replace(",", " "), delta_color="inverse")
    p3.metric("Impôt sur le Revenu (IR)", f"-{ir_net:,.2f} {devise}".replace(",", " "), delta_color="inverse")
    p4.metric("Net à Payer à l'Agent", f"{salaire_net_a_payer:,.2f} {devise}".replace(",", " "))

    st.write(f"💼 **Coût Global Employeur pour le CHU :** `{cout_total_chu:,.2f} {devise}` (incluant `{cout_total_chu - salaire_brut_global:,.2f} {devise}` de charges patronales).")

    # Tableau détaillé type fiche de paie
    df_detail_paie = pd.DataFrame({
        "Rubrique de Paie": [
            "1. Traitement de base indiciaire",
            "2. Indemnité de technicité / fonction",
            "3. Indemnités de gardes & permanence des soins",
            "Total Salaire Brut",
            "4. Retenue Retraite",
            "5. Retenue CNOPS / Couverture Médicale",
            "6. Impôt sur le Revenu Net (IR)",
            "Net à Payer à l'Agent Hospitalier"
        ],
        "Sens": ["Gain", "Gain", "Gain", "TOTAL BRUT", "Retenue", "Retenue", "Retenue", "NET"],
        "Montant": [
            traitement_base, prime_technicite, total_gardes_val, salaire_brut_global,
            retenue_retraite, retenue_sante, ir_net, salaire_net_a_payer
        ]
    })
    
    st.dataframe(df_detail_paie.style.format({"Montant": "{:,.2f} " + devise}), use_container_width=True)

    # Fonction d'édition du bulletin PDF
    def generer_bulletin_pdf(categorie, brut, net, base, prime, gardes_v, ret_retraite, ret_sante, ir, cout_chu, dev, logo_p):
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
        pdf.cell(0, 8, "BULLETIN DE PAIE HOSPITALIER - CHU", ln=True)
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(100, 116, 139)
        if logo_p.exists():
            pdf.set_x(50)
        pdf.cell(0, 6, f"Corps : {categorie} | Direction des Ressources Humaines & Affaires Financières", ln=True)
        pdf.ln(10)
        
        pdf.set_draw_color(226, 232, 240)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(6)
        
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 7, "ÉLÉMENTS DE RÉMUNÉRATION BRUTE", ln=True)
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(120, 7, "  - Traitement de base indiciaire", 1)
        pdf.cell(60, 7, f"{base:,.2f} {dev}", 1, ln=True, align="R")
        pdf.cell(120, 7, "  - Indemnite de fonction / technicit/risque", 1)
        pdf.cell(60, 7, f"{prime:,.2f} {dev}", 1, ln=True, align="R")
        pdf.cell(120, 7, "  - Indemnites de gardes et astreintes", 1)
        pdf.cell(60, 7, f"{gardes_v:,.2f} {dev}", 1, ln=True, align="R")
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(120, 7, "TOTAL SALAIRE BRUT", 1)
        pdf.cell(60, 7, f"{brut:,.2f} {dev}", 1, ln=True, align="R")
        pdf.ln(6)
        
        pdf.cell(0, 7, "RETENUES OBLIGATOIRES & PRÉLÈVEMENTS", ln=True)
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(120, 7, "  - Cotisation Caisse de Retraite", 1)
        pdf.cell(60, 7, f"-{ret_retraite:,.2f} {dev}", 1, ln=True, align="R")
        pdf.cell(120, 7, "  - Assurance Maladie Obligatoire (CNOPS)", 1)
        pdf.cell(60, 7, f"-{ret_sante:,.2f} {dev}", 1, ln=True, align="R")
        pdf.cell(120, 7, "  - Impot sur le Revenu (IR)", 1)
        pdf.cell(60, 7, f"-{ir:,.2f} {dev}", 1, ln=True, align="R")
        pdf.ln(6)
        
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_fill_color(239, 246, 255)
        pdf.cell(120, 9, "NET À PAYER À L'AGENT HOSPITALIER", 1, fill=True)
        pdf.cell(60, 9, f"{net:,.2f} {dev}", 1, ln=True, align="R", fill=True)
        pdf.ln(4)
        
        pdf.set_font('Helvetica', 'I', 8)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 6, f"Coût total supporté par le CHU (charges patronales comprises) : {cout_chu:,.2f} {dev}", ln=True)
        return bytes(pdf.output())

    bulletin_bytes = generer_bulletin_pdf(
        categorie_agent, salaire_brut_global, salaire_net_a_payer,
        traitement_base, prime_technicite, total_gardes_val,
        retenue_retraite, retenue_sante, ir_net, cout_total_chu, devise, chemin_logo
    )
    
    st.download_button(
        label="📥 Télécharger le Bulletin de Paie Simulé (PDF)",
        data=bulletin_bytes,
        file_name=f"Bulletin_Paie_CHU_{categorie_agent.replace(' ', '_')}.pdf",
        mime="application/pdf"
    )

# --- ONGLET 3 : RATIOS DE CHARGE & ENCADREMENT ---
with tab_ratios:
    st.subheader("Normes Sanitaires & Ratios d'Encadrement par Lit")
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Lits Ouverts", f"{lits_ouverts_total} lits")
    r2.metric("Encadrement IDE", f"{ratio_ide_lit:.2f} IDE / lit")
    r3.metric("Présence Médicale", f"{ratio_med_lit:.2f} Médecin / lit")
    r4.metric("Journées d'Hospitalisation", f"{total_jh:,.0f} JH".replace(",", " "))

    df_ratios_pole = df_chu[df_chu["mois"] == mois_ref].copy()
    df_ratios_pole["ratio_soignant_lit"] = df_ratios_pole["effectif_infirmiers"] / df_ratios_pole["lits_ouverts"]

    fig_ratios = px.bar(
        df_ratios_pole, x="pole", y="ratio_soignant_lit",
        title="Densité Soignante par Lit d'Hospitalisation (IDE / Lit)",
        text="ratio_soignant_lit",
        labels={"ratio_soignant_lit": "IDE / Lit", "pole": "Pôle Clinique"},
        color="ratio_soignant_lit", color_continuous_scale="Blues"
    )
    fig_ratios.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    fig_ratios.add_hline(y=1.0, line_dash="dash", line_color="#EF4444", annotation_text="Norme Minimale (1.0)")
    st.plotly_chart(fig_ratios, use_container_width=True)

# --- ONGLET 4 : COÛT RH / JOURNÉE DE SOINS ---
with tab_cout_jh:
    st.subheader("Coût Salarial Rapporté à la Journée d'Hospitalisation (JH)")
    c1, c2, c3 = st.columns(3)
    c1.metric("Coût RH / Journée (JH)", f"{cout_rh_par_jh:,.0f} {devise} / JH".replace(",", " "))
    c2.metric("Journées Facturées", f"{total_jh:,.0f} JH".replace(",", " "))
    c3.metric("Coût Annuel Moyen / Lit", f"{(masse_salariale_totale*1000/lits_ouverts_total if lits_ouverts_total>0 else 0):,.0f} {devise}".replace(",", " "))

    df_cout_pole = df_chu.groupby("pole", as_index=False).agg({"masse_salariale_kmad": "sum", "journees_hospitalisation": "sum"})
    df_cout_pole["cout_jh"] = (df_cout_pole["masse_salariale_kmad"] * 1000) / df_cout_pole["journees_hospitalisation"]

    fig_jh = px.bar(
        df_cout_pole, x="pole", y="cout_jh",
        title=f"Coût Salarial par Journée d'Hospitalisation ({devise}/JH)",
        text="cout_jh", labels={"cout_jh": f"Coût / JH ({devise})", "pole": "Pôle"},
        color="cout_jh", color_continuous_scale="Teal"
    )
    fig_jh.update_traces(texttemplate="%{text:,.0f} " + devise, textposition="outside")
    st.plotly_chart(fig_jh, use_container_width=True)

# --- ONGLET 5 : NOTE EXÉCUTIVE PDF ---
with tab_pdf:
    st.subheader("📄 Note Médico-Économique & Bilan de Masse Salariale (PDF)")

    def generer_note_synthese_pdf(periode, pol, dev, eff_tot, ms_tot, g_tot, c_jh, logo_p):
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
        pdf.cell(0, 8, "NOTE DE CONTRÔLE DE GESTION RH & PAIE - CHU", ln=True)
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(100, 116, 139)
        if logo_p.exists():
            pdf.set_x(50)
        pdf.cell(0, 6, f"Période : {periode} | Périmètre : {pol} | Direction Générale", ln=True)
        pdf.ln(10)
        
        pdf.set_draw_color(226, 232, 240)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(6)
        
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 7, "INDICATEURS CONSOLIDÉS DE PAIE ET D'ACTIVITÉ", ln=True)
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(100, 7, f"  - Effectif Hospitalier Total : {eff_tot} agents", 1)
        pdf.cell(80, 7, f"  - Masse Salariale : {ms_tot:,.0f} k{dev}", 1, ln=True)
        pdf.cell(100, 7, f"  - Sujetions Gardes & Astreintes : {g_tot:,.0f} k{dev}", 1)
        pdf.cell(80, 7, f"  - Cout RH / Journee de Soins : {c_jh:,.0f} {dev}/JH", 1, ln=True)
        pdf.ln(6)
        
        pdf.set_font('Helvetica', 'B', 11)
        pdf.cell(0, 7, "SYNTHÈSE DU CONTRÔLEUR DE GESTION HOSPITALIER", ln=True)
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(51, 65, 85)
        texte = (
            f"La masse salariale consolidée s'établit à {ms_tot:,.0f} k{dev}. "
            f"Le poste 'gardes et astreintes' ({g_tot:,.0f} k{dev}) requiert un suivi strict des plannings de relève "
            f"afin d'assurer la continuité des soins tout en préservant le coût objectif de {c_jh:,.0f} {dev} par journée d'hospitalisation."
        )
        pdf.multi_cell(180, 5, texte, 1)
        return bytes(pdf.output())

    pdf_synthese_bytes = generer_note_synthese_pdf(
        mois_choisi, pole_choisi, devise, effectif_total_chu,
        masse_salariale_totale, gardes_totales, cout_rh_par_jh, chemin_logo
    )

    st.download_button(
        label="📥 Télécharger la Note Médico-Économique (PDF)",
        data=pdf_synthese_bytes,
        file_name=f"Note_CGRH_Paie_CHU_{mois_choisi}_{pole_choisi.replace(' ', '_')}.pdf",
        mime="application/pdf"
    )