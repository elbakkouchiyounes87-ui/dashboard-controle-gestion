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
    page_title="Direction RH & Gestion de la Paie Maroc",
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
        st.markdown("<h1 style='font-size: 2.8rem; margin:0;'>🇲🇦</h1>", unsafe_allow_html=True)
with col_head2:
    st.title("👥 Direction RH & Contrôle de Paie - Régime Marocain")
    st.caption("Pilotage social et moteur de paie marocain conforme au CGI (Barème IR réformé, cotisations CNSS, AMO et CIMR).")

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
    devise = "MAD"  # Standard réglementaire marocain

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
tab_synthese, tab_paie_maroc, tab_demographie, tab_climat, tab_noria, tab_pdf = st.tabs([
    "📊 Synthèse RH & Effectifs",
    "🇲🇦 Moteur de Paie Marocain",
    "👥 Pyramide des Âges & Talents",
    "⚠️ Climat Social & Bradford",
    "🔮 Prévisions Noria & GVT",
    "📄 Bilan Social PDF"
])

# --- ONGLET 1 : SYNTHÈSE RH ---
with tab_synthese:
    st.subheader("Structure des Effectifs & Masse Salariale")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Effectif Total", f"{effectif_total} collaborateurs", f"{total_entrees - total_sorties:+d} solde net")
    k2.metric("Masse Salariale Cumulée", f"{masse_salariale_totale:,.0f} k{devise}".replace(",", " "))
    k3.metric("Salaire Moyen / Salarié", f"{cout_moyen_mensuel:,.0f} {devise}/mois".replace(",", " "))
    k4.metric("Part Variable & Primes", f"{part_primes:.1f}%", help="Commissions, primes de rendement et heures supp.")

    st.markdown(f"""
        <div class='diag-box'>
        <b>Diagnostic RH :</b> L'effectif sous revue totalise <b>{effectif_total} salariés</b> répartis en 
        <b>{eff_cadres} Cadres ({(eff_cadres/effectif_total*100):.1f}%)</b>, <b>{eff_tam} TAM</b> et <b>{eff_employes} Employés/Opérateurs</b>. 
        Le salaire moyen de l'entreprise est de <b>{cout_moyen_mensuel:,.0f} {devise}/mois</b>.
        </div>
    """, unsafe_allow_html=True)

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("Répartition Catégorielle par Département")
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

# --- ONGLET 2 : MOTEUR DE PAIE RÉGIME MAROCAIN ---
with tab_paie_maroc:
    st.subheader("🇲🇦 Simulateur Officiel de Paie & Bulletin de Salaire (Maroc)")
    st.caption("Conforme au Code Général des Impôts (Barème progressif IR réformé, Plafond CNSS 6 000 MAD, AMO 2,26%, déductions familiales et frais professionnels).")

    col_p1, col_p2 = st.columns(2)

    with col_p1:
        st.markdown("#### 1. Rémunération Brute")
        statut_sal = st.selectbox(
            "Profil du salarié :",
            ["Cadre Supérieur / Manager", "Cadre Moyen / Ingénieur", "Agent de Maîtrise / Technicien", "Employé / Opérateur"]
        )
        
        bareme_ent = {
            "Cadre Supérieur / Manager": {"base": 25000.0, "prime": 4000.0, "transport": 500.0},
            "Cadre Moyen / Ingénieur": {"base": 14000.0, "prime": 2000.0, "transport": 500.0},
            "Agent de Maîtrise / Technicien": {"base": 7500.0, "prime": 1000.0, "transport": 500.0},
            "Employé / Opérateur": {"base": 4200.0, "prime": 500.0, "transport": 500.0}
        }
        ref_s = bareme_ent[statut_sal]

        salaire_base = st.number_input(f"Salaire de base ({devise})", value=ref_s["base"], step=200.0)
        primes_brutes = st.number_input(f"Primes imposables (rendement, ancienneté) ({devise})", value=ref_s["prime"], step=100.0)
        indemnite_transport = st.number_input(f"Indemnité de transport justifiée (exonérée) ({devise})", value=ref_s["transport"], step=50.0)
        
        # Salaire Brut Global & Imposable
        salaire_brut_global = salaire_base + primes_brutes + indemnite_transport
        salaire_brut_imposable = salaire_base + primes_brutes  # Indemnité transport exonérée dans la limite légale

    with col_p2:
        st.markdown("#### 2. Options Sociales & Fiscales")
        taux_cimr = st.slider("Taux Retraite Complémentaire (CIMR Salarié) (%)", 0.0, 10.0, 3.0, step=0.5) / 100.0
        nb_personnes_charge = st.slider("Personnes à charge (conjoint + enfants, max 6)", 0, 6, 2)
        taux_at_patronal = st.slider("Taux Accident du Travail (Employeur) (%)", 0.5, 3.0, 1.5, step=0.1) / 100.0

    # --- MOTEUR DE CALCUL DE LA PAIE MAROCAINE ---
    
    # 1. Cotisations salariales
    base_cnss = min(salaire_brut_imposable, 6000.0)
    cotisation_cnss_sal = base_cnss * 0.0448        # 4.48% plafonné à 6000 MAD
    cotisation_amo_sal = salaire_brut_imposable * 0.0226  # 2.26% non plafonné
    cotisation_cimr_sal = salaire_brut_imposable * taux_cimr
    total_charges_salariales = cotisation_cnss_sal + cotisation_amo_sal + cotisation_cimr_sal

    # 2. Frais professionnels marocains
    # 35% si SBI mensuel <= 6 500 MAD (78 000/an), 25% si > 6 500 MAD. Plafonné à 35 000 MAD/an (2 916.67 MAD/mois)
    taux_frais_pro = 0.35 if salaire_brut_imposable <= 6500.0 else 0.25
    frais_professionnels = min(salaire_brut_imposable * taux_frais_pro, 2916.67)

    # 3. Salaire Net Imposable (SNI)
    sni_mensuel = max(0.0, salaire_brut_imposable - total_charges_salariales - frais_professionnels)

    # 4. Barème progressif mensuel de l'IR (Loi de Finances marocaine)
    if sni_mensuel <= 3333.33:
        ir_brut = 0.0
    elif sni_mensuel <= 5000.00:
        ir_brut = (sni_mensuel * 0.10) - 333.33
    elif sni_mensuel <= 6666.67:
        ir_brut = (sni_mensuel * 0.20) - 833.33
    elif sni_mensuel <= 8333.33:
        ir_brut = (sni_mensuel * 0.30) - 1500.00
    elif sni_mensuel <= 15000.00:
        ir_brut = (sni_mensuel * 0.34) - 1833.33
    else:
        ir_brut = (sni_mensuel * 0.37) - 2283.33

    ir_brut = max(0.0, ir_brut)

    # 5. Déduction pour charges de famille (50 MAD par personne / mois, max 300 MAD)
    deduction_famille = nb_personnes_charge * 50.0
    ir_net_mensuel = max(0.0, ir_brut - deduction_famille)

    # 6. Salaire Net à Payer
    salaire_net_a_payer = salaire_brut_global - total_charges_salariales - ir_net_mensuel

    # 7. Cotisations Patronales Marocaines
    cnss_patronale_alloc_fam = salaire_brut_imposable * 0.0640   # 6.40% non plafonné
    cnss_patronale_prestat = base_cnss * 0.0860                 # 8.60% plafonné à 6000 MAD
    taxe_formation_pro = salaire_brut_imposable * 0.0160        # 1.60% non plafonné
    amo_patronale = salaire_brut_imposable * 0.0411             # 4.11% non plafonné
    cimr_patronale = salaire_brut_imposable * (taux_cimr * 1.33)  # Part patronale CIMR (~4% si salarié à 3%)
    at_patronale = salaire_brut_imposable * taux_at_patronal

    total_charges_patronales = (
        cnss_patronale_alloc_fam + cnss_patronale_prestat +
        taxe_formation_pro + amo_patronale + cimr_patronale + at_patronale
    )
    cout_global_employeur = salaire_brut_global + total_charges_patronales

    # Restitution des résultats
    st.divider()
    st.subheader("3. Résultat du Calcul & Décomposition du Bulletin")

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Salaire Brut Global", f"{salaire_brut_global:,.2f} {devise}".replace(",", " "))
    r2.metric("Cotisations Sociales (CNSS/AMO/CIMR)", f"-{total_charges_salariales:,.2f} {devise}".replace(",", " "), delta_color="inverse")
    r3.metric("Impôt sur le Revenu Net (IR)", f"-{ir_net_mensuel:,.2f} {devise}".replace(",", " "), delta_color="inverse")
    r4.metric("Net à Payer (Virement)", f"{salaire_net_a_payer:,.2f} {devise}".replace(",", " "))

    st.info(
        f"💼 **Coût Total Employeur au Maroc :** `{cout_global_employeur:,.2f} MAD` "
        f"(dont `{total_charges_patronales:,.2f} MAD` de charges sociales patronales CNSS/AMO/Formation/AT)."
    )

    # Tableau analytique du bulletin
    df_bulletin = pd.DataFrame({
        "Libellé de la Rubrique": [
            "Salaire de base",
            "Primes & gratifications imposables",
            "Indemnité de transport (exonérée)",
            "TOTAL SALAIRE BRUT GLOBAL",
            "CNSS - Prestations Sociales (4,48% plafonné)",
            "AMO - Assurance Maladie Obligatoire (2,26%)",
            f"CIMR - Retraite complémentaire ({taux_cimr*100:.1f}%)",
            "Frais professionnels déductibles (assiette fiscale)",
            "Salaire Net Imposable (SNI)",
            "IR Brut",
            f"Déduction charges de famille ({nb_personnes_charge} pers.)",
            "Impôt sur le Revenu Net Retenu (IR)",
            "NET À PAYER AU SALARIÉ"
        ],
        "Base de Calcul": [
            f"{salaire_base:,.2f}", f"{primes_brutes:,.2f}", f"{indemnite_transport:,.2f}", f"{salaire_brut_global:,.2f}",
            f"{base_cnss:,.2f}", f"{salaire_brut_imposable:,.2f}", f"{salaire_brut_imposable:,.2f}",
            f"{salaire_brut_imposable:,.2f}", f"{sni_mensuel:,.2f}", f"{sni_mensuel:,.2f}",
            "-", f"{sni_mensuel:,.2f}", "-"
        ],
        "Part Salariale (MAD)": [
            f"+{salaire_base:,.2f}", f"+{primes_brutes:,.2f}", f"+{indemnite_transport:,.2f}", f"{salaire_brut_global:,.2f}",
            f"-{cotisation_cnss_sal:,.2f}", f"-{cotisation_amo_sal:,.2f}", f"-{cotisation_cimr_sal:,.2f}",
            f"({frais_professionnels:,.2f})", "-", f"({ir_brut:,.2f})", f"(-{deduction_famille:,.2f})",
            f"-{ir_net_mensuel:,.2f}", f"{salaire_net_a_payer:,.2f}"
        ]
    })
    st.table(df_bulletin)

    # Fonction de génération du Bulletin de Paie PDF Officiel Maroc
    def generer_bulletin_maroc_pdf(statut, s_base, primes, trans, brut_g, sbi, cnss, amo, cimr, frais_p, sni, ir, net, cout_emp, logo_p):
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        if logo_p.exists():
            pdf.image(str(logo_p), x=15, y=10, w=30)
            pdf.set_xy(50, 15)
        else:
            pdf.set_xy(15, 15)

        pdf.set_font('Helvetica', 'B', 15)
        pdf.set_text_color(30, 58, 138)
        pdf.cell(0, 8, "BULLETIN DE PAIE (RÉGIME MAROCAIN)", ln=True)
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(100, 116, 139)
        if logo_p.exists():
            pdf.set_x(50)
        pdf.cell(0, 5, f"Période sous revue | Conforme Code du Travail & CGI Maroc | Statut : {statut}", ln=True)
        pdf.ln(10)

        pdf.set_draw_color(226, 232, 240)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(5)

        # 1. Rémunérations
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 7, "1. GAINS & ÉLÉMENTS DE SALAIRE BRUT", ln=True)
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(120, 6, "  - Salaire de Base", 1)
        pdf.cell(60, 6, f"{s_base:,.2f} MAD", 1, ln=True, align="R")
        pdf.cell(120, 6, "  - Primes & Indemnites imposables", 1)
        pdf.cell(60, 6, f"{primes:,.2f} MAD", 1, ln=True, align="R")
        pdf.cell(120, 6, "  - Indemnite de Transport (exoneree)", 1)
        pdf.cell(60, 6, f"{trans:,.2f} MAD", 1, ln=True, align="R")
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(120, 7, "TOTAL SALAIRE BRUT GLOBAL", 1)
        pdf.cell(60, 7, f"{brut_g:,.2f} MAD", 1, ln=True, align="R")
        pdf.ln(5)

        # 2. Retenues sociales et fiscales
        pdf.set_font('Helvetica', 'B', 11)
        pdf.cell(0, 7, "2. RETENUES SALARIALES (CNSS, AMO, CIMR & IR)", ln=True)
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(120, 6, "  - CNSS Prestations Sociales (4,48% plafonne)", 1)
        pdf.cell(60, 6, f"-{cnss:,.2f} MAD", 1, ln=True, align="R")
        pdf.cell(120, 6, "  - AMO Assurance Maladie Obligatoire (2,26%)", 1)
        pdf.cell(60, 6, f"-{amo:,.2f} MAD", 1, ln=True, align="R")
        if cimr > 0:
            pdf.cell(120, 6, "  - Cotisation CIMR (Retraite complementaire)", 1)
            pdf.cell(60, 6, f"-{cimr:,.2f} MAD", 1, ln=True, align="R")
        pdf.cell(120, 6, "  - Impot sur le Revenu Net Preleve (IR)", 1)
        pdf.cell(60, 6, f"-{ir:,.2f} MAD", 1, ln=True, align="R")
        pdf.ln(5)

        # 3. Net et coût employeur
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_fill_color(239, 246, 255)
        pdf.cell(120, 8, "SALAIRE NET À PAYER (VIREMENT BANCAIRE)", 1, fill=True)
        pdf.cell(60, 8, f"{net:,.2f} MAD", 1, ln=True, align="R", fill=True)
        pdf.ln(4)

        pdf.set_font('Helvetica', 'I', 8)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 5, f"Information employeur : Coût global entreprise (charges patronales CNSS/AMO/AT incluses) = {cout_emp:,.2f} MAD", ln=True)
        return bytes(pdf.output())

    pdf_bulletin_maroc = generer_bulletin_maroc_pdf(
        statut_sal, salaire_base, primes_brutes, indemnite_transport,
        salaire_brut_global, salaire_brut_imposable,
        cotisation_cnss_sal, cotisation_amo_sal, cotisation_cimr_sal,
        frais_professionnels, sni_mensuel, ir_net_mensuel,
        salaire_net_a_payer, cout_global_employeur, chemin_logo
    )

    st.download_button(
        label="📥 Télécharger le Bulletin de Paie Conforme Maroc (PDF)",
        data=pdf_bulletin_maroc,
        file_name=f"Bulletin_Paie_Maroc_{statut_sal.replace(' ', '_')}.pdf",
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

# --- ONGLET 4 : CLIMAT SOCIAL, BRADFORD & RADAR ---
with tab_climat:
    st.subheader("Absentéisme & Facteur de Bradford")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Taux d'Absentéisme", f"{taux_absenteisme:.2f}%")
    c2.metric("Facteur Bradford Moyen", f"{facteur_bradford:.0f} pts")
    c3.metric("Taux de Turnover", f"{turnover_pct:.2f}%")
    c4.metric("Coût Estimé Départs", f"{(total_sorties * cout_moyen_mensuel * 6 / 1000):,.0f} k{devise}".replace(",", " "))

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
        st.markdown("#### Diagnostic QVT")
        if facteur_bradford > 250:
            st.warning(f"⚠️ **Score Bradford ({facteur_bradford:.0f}) :** Forte récurrence de micro-absences perturbatrices.")
        else:
            st.success(f"✅ **Score Bradford ({facteur_bradford:.0f}) :** Bonne régularité des équipes.")
        st.metric("Indice Global Climat Social", f"{np.mean(vals):.1f} / 100")

# --- ONGLET 5 : EFFET NORIA & GVT ---
with tab_noria:
    st.subheader("🔮 Simulateur Budgétaire : Effet Noria & Effet GVT")
    gn1, gn2 = st.columns(2)
    with gn1:
        st.markdown("##### 1. Effet GVT (Augmentations d'Ancienneté)")
        pct_gvt = st.slider("Augmentation moyenne d'ancienneté / mérite (%)", 0.0, 6.0, 2.0, step=0.1)
        impact_gvt_kmad = (masse_salariale_totale * (pct_gvt / 100.0))
        st.write(f"Surcoût annuel mécanique : **+{impact_gvt_kmad:,.0f} k{devise}**")

    with gn2:
        st.markdown("##### 2. Effet Noria (Remplacement Départs)")
        departs_seniors = st.slider("Nombre de départs seniors remplacés par des juniors", 0, 15, 4)
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
        pdf.cell(0, 10, 'BILAN SOCIAL & PEOPLE ANALYTICS (MAROC)', ln=True, align='L' if logo_p.exists() else 'C')
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(100, 116, 139)
        if logo_p.exists():
            pdf.set_x(55)
        pdf.cell(0, 6, f'Période : {periode} | Périmètre : {dpt} | Direction Générale', ln=True)
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
        pdf.cell(90, 8, f'  - Masse Salariale : {ms:,.0f} k{dev}', 1, ln=True)
        pdf.cell(90, 8, f'  - Salaire Moyen : {cm:,.0f} {dev}/mois', 1)
        pdf.cell(90, 8, '  - Conformite Reglementaire : CNSS/AMO', 1, ln=True)
        pdf.ln(6)
        
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, '2. Climat Social, Absentéisme & Stabilité', ln=True)
        pdf.ln(2)
        
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(90, 8, f'  - Taux Absenteisme : {abs_tx:.2f} %', 1)
        pdf.cell(90, 8, f'  - Taux de Turnover : {to_tx:.2f} %', 1, ln=True)
        pdf.cell(90, 8, f'  - Facteur Bradford : {brad:.0f} pts', 1)
        pdf.cell(90, 8, '  - Stabilite Globale : Favorable', 1, ln=True)
        pdf.ln(6)
        
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, '3. Recommandations de la Direction RH', ln=True)
        pdf.ln(2)
        
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(51, 65, 85)
        avis = (
            f"L'effectif stabilise a {eff} salaries temoigne d'une bonne dynamique operationnelle.\n"
            f"Les cotisations et impots sont etablis conformement a la reglementation fiscale et sociale marocaine (CNSS, AMO et IR).\n"
            "Il est preconise de poursuivre les arbitrages Noria sur les recrutements juniors afin de maitriser la derive mecanique du GVT."
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
        file_name=f"Bilan_Social_Maroc_{mois_choisi}_{dept_choisi.replace(' ', '_')}.pdf",
        mime="application/pdf"
    )