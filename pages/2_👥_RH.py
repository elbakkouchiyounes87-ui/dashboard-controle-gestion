from pathlib import Path
from auth import afficher_bouton_deconnexion, verifier_authentification
from fpdf import FPDF
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from style import appliquer_theme_cockpit_dark

# 1. Configuration et Sécurité
st.set_page_config(
    page_title="Contrôle de Gestion Sociale - CHU", page_icon="🏥", layout="wide"
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
    st.markdown(
        "<h1 style='font-size: 2.8rem; margin:0;'>🏥</h1>", unsafe_allow_html=True
    )
with col_head2:
  st.title("🏥 Contrôle de Gestion RH & Pilotage Médico-Économique (CHU)")
  st.caption(
      "Pilotage stratégique des effectifs : corps médical, personnel soignant,"
      " encadrement administratif et coût par journée d'hospitalisation."
  )


# 2. Chargement des données
@st.cache_data
def charger_donnees_chu():
  chemin_csv = chemin_racine / "donnees_rh.csv"
  if not chemin_csv.exists():
    chemin_csv = Path(__file__).resolve().parent / "donnees_rh.csv"
  if not chemin_csv.exists():
    st.error("Fichier 'donnees_rh.csv' introuvable.")
    st.stop()
  df = pd.read_csv(chemin_csv)
  df["effectif_total"] = (
      df["effectif_medecins"] + df["effectif_infirmiers"] + df["effectif_admin"]
  )
  return df


df_chu = charger_donnees_chu()

# 3. Filtres
with st.sidebar:
  st.header("⚙️ Filtres Hospitaliers")
  mois_dispo = ["Tous les mois"] + list(df_chu["mois"].unique())
  mois_choisi = st.selectbox("Période sous revue", mois_dispo, index=0)

  poles_dispo = ["Tous les pôles"] + list(df_chu["pole"].unique())
  pole_choisi = st.selectbox("Pôle Clinique", poles_dispo, index=0)
  devise = st.radio("Devise", ["MAD", "EUR"])

df_vue = df_chu.copy()
if mois_choisi != "Tous les mois":
  df_vue = df_vue[df_vue["mois"] == mois_choisi]
if pole_choisi != "Tous les pôles":
  df_vue = df_vue[df_vue["pole"] == pole_choisi]

# 4. Calculs des Métriques CGRH Hospitalières
nb_mois = df_vue["mois"].nunique()
mois_ref = mois_choisi if mois_choisi != "Tous les mois" else "Juin"

eff_medecins = (
    df_vue["effectif_medecins"].sum()
    if mois_choisi != "Tous les mois"
    else df_chu[df_chu["mois"] == mois_ref]["effectif_medecins"].sum()
)
eff_infirmiers = (
    df_vue["effectif_infirmiers"].sum()
    if mois_choisi != "Tous les mois"
    else df_chu[df_chu["mois"] == mois_ref]["effectif_infirmiers"].sum()
)
eff_admin = (
    df_vue["effectif_admin"].sum()
    if mois_choisi != "Tous les mois"
    else df_chu[df_chu["mois"] == mois_ref]["effectif_admin"].sum()
)
effectif_total_chu = eff_medecins + eff_infirmiers + eff_admin

lits_ouverts_total = (
    df_vue["lits_ouverts"].sum()
    if mois_choisi != "Tous les mois"
    else df_chu[df_chu["mois"] == mois_ref]["lits_ouverts"].sum()
)
total_jh = df_vue["journees_hospitalisation"].sum()

masse_salariale_totale = df_vue["masse_salariale_kmad"].sum()
gardes_totales = df_vue["gardes_astreintes_kmad"].sum()
part_gardes = (
    (gardes_totales / masse_salariale_totale * 100)
    if masse_salariale_totale > 0
    else 0
)

# Ratios de gestion hospitalière
ratio_ide_lit = (
    eff_infirmiers / lits_ouverts_total if lits_ouverts_total > 0 else 0
)
ratio_med_lit = (
    eff_medecins / lits_ouverts_total if lits_ouverts_total > 0 else 0
)
ratio_support_soin = (
    (eff_admin / (eff_medecins + eff_infirmiers) * 100)
    if (eff_medecins + eff_infirmiers) > 0
    else 0
)

# Coût RH par Journée d'Hospitalisation (Coût / JH)
cout_rh_par_jh = (
    (masse_salariale_totale * 1000) / total_jh if total_jh > 0 else 0
)

# Absentéisme soignant
jours_abs = df_vue["abs_maladie_jours"].sum()
heures_abs = jours_abs * 8
taux_absenteisme = (
    (jours_abs / (effectif_total_chu * 22 * nb_mois)) * 100
    if (effectif_total_chu * nb_mois) > 0
    else 0
)
facteur_bradford = ((jours_abs / 2.8) ** 2) * jours_abs / (effectif_total_chu or 1)

# 5. Onglets de Pilotage CGRH
tab_kpis, tab_ratios, tab_cout_jh, tab_absenteisme, tab_pdf = st.tabs([
    "📊 Synthèse Médicale & Administrative",
    "🩺 Ratios de Charge & Encadrement",
    "💰 Coût RH / Journée de Soins (JH)",
    "⚠️ Absentéisme & Climat Hospitalier",
    "📄 Note Médico-Économique (PDF)",
])

# --- ONGLET 1 : SYNTHÈSE DES CORPS DE MÉTIER ---
with tab_kpis:
  st.subheader("Structure des Ressources Humaines du CHU")
  k1, k2, k3, k4 = st.columns(4)
  k1.metric(
      "Corps Médical (PHU/Praticiens)",
      f"{eff_medecins} médecins",
      f"{(eff_medecins/effectif_total_chu*100):.1f}% de l'effectif",
  )
  k2.metric(
      "Personnel Soignant (IDE/AS)",
      f"{eff_infirmiers} soignants",
      f"{(eff_infirmiers/effectif_total_chu*100):.1f}% de l'effectif",
  )
  k3.metric(
      "Personnel Administratif (PATL)",
      f"{eff_admin} agents",
      f"Ratio support : {ratio_support_soin:.1f}%",
  )
  k4.metric(
      "Masse Salariale Consolidée",
      f"{masse_salariale_totale:,.0f} k{devise}".replace(",", " "),
      f"Gardes : {part_gardes:.1f}%",
  )

  st.markdown(f"""
        <div class='diag-box'>
        <b>Diagnostic CGRH :</b> L'établissement mobilise <b>{effectif_total_chu} agents</b> pour une capacité de <b>{lits_ouverts_total} lits actifs</b>. 
        Le ratio d'administration et de soutien logistique est de <b>{ratio_support_soin:.1f}%</b> par rapport aux soignants, ce qui traduit une structure opérationnelle équilibrée. 
        Les indemnités de permanence des soins (gardes et astreintes) représentent <b>{part_gardes:.1f}%</b> du budget salarial.
        </div>
    """, unsafe_allow_html=True)

  col_g1, col_g2 = st.columns(2)
  with col_g1:
    st.subheader("Répartition des Métiers par Pôle Hospitalier")
    df_poles = (
        df_chu[df_chu["mois"] == mois_ref]
        .groupby("pole")[
            ["effectif_medecins", "effectif_infirmiers", "effectif_admin"]
        ]
        .sum()
        .reset_index()
    )

    fig_tri = px.bar(
        df_poles,
        x="pole",
        y=["effectif_medecins", "effectif_infirmiers", "effectif_admin"],
        barmode="stack",
        labels={"value": "Effectif (ETP)", "pole": "Pôle Clinique"},
        title="Ventilation Corps Médical / Soins / Administration",
        color_discrete_map={
            "effectif_medecins": "#1E3A8A",
            "effectif_infirmiers": "#0284C7",
            "effectif_admin": "#10B981",
        },
    )
    st.plotly_chart(fig_tri, use_container_width=True)

  with col_g2:
    st.subheader("Composantes de la Masse Salariale Hospitalière")
    salaires_base = masse_salariale_totale - gardes_totales
    fig_pie_ms = px.pie(
        names=["Traitements de Base", "Gardes, Astreintes & Sujétions"],
        values=[salaires_base, gardes_totales],
        hole=0.45,
        title=f"Structure Budgétaire Salariale ({devise})",
        color_discrete_sequence=["#1E3A8A", "#F59E0B"],
    )
    st.plotly_chart(fig_pie_ms, use_container_width=True)

# --- ONGLET 2 : RATIOS DE CHARGE & ENCADREMENT ---
with tab_ratios:
  st.subheader("Normes de Sécurité Sanitaire & Ratios d'Encadrement par Lit")
  st.caption(
      "Indicateurs de conformité médico-légale et de sécurité des patients."
  )

  r1, r2, r3, r4 = st.columns(4)
  r1.metric("Lits Ouverts Actifs", f"{lits_ouverts_total} lits")
  r2.metric(
      "Taux d'Encadrement Infirmier",
      f"{ratio_ide_lit:.2f} IDE / lit",
      help="Seuil de sécurité recommandé en soins aigus : > 1.2 IDE/lit",
  )
  r3.metric("Présence Médicale", f"{ratio_med_lit:.2f} Médecin / lit")
  r4.metric(
      "Patients pris en charge",
      f"{total_jh:,.0f} Journées".replace(",", " "),
  )

  st.divider()

  # Graphique de conformité par Pôle
  df_ratios_pole = df_chu[df_chu["mois"] == mois_ref].copy()
  df_ratios_pole["ratio_soignant_lit"] = (
      df_ratios_pole["effectif_infirmiers"] / df_ratios_pole["lits_ouverts"]
  )

  fig_ratios = px.bar(
      df_ratios_pole,
      x="pole",
      y="ratio_soignant_lit",
      title="Densité Soignante par Lit d'Hospitalisation (IDE / Lit)",
      text="ratio_soignant_lit",
      labels={"ratio_soignant_lit": "IDE / Lit", "pole": "Pôle Clinique"},
      color="ratio_soignant_lit",
      color_continuous_scale="Blues",
  )
  fig_ratios.update_traces(texttemplate="%{text:.2f}", textposition="outside")
  fig_ratios.add_hline(
      y=1.0,
      line_dash="dash",
      line_color="#EF4444",
      annotation_text="Seuil Standard Minimal (1.0)",
  )
  st.plotly_chart(fig_ratios, use_container_width=True)

# --- ONGLET 3 : COÛT RH PAR JOURNÉE D'HOSPITALISATION ---
with tab_cout_jh:
  st.subheader("Approche Médico-Économique : Coût Salarial à la Journée de Soins")
  st.caption(
      "Indicateur central de la tarification et de la négociation budgétaire"
      " avec les tutelles (Ministère / Assurance Maladie)."
  )

  c_j1, c_j2, c_j3 = st.columns(3)
  c_j1.metric(
      "Coût RH Moyen / Journée (JH)",
      f"{cout_rh_par_jh:,.0f} {devise} / JH".replace(",", " "),
  )
  c_j2.metric(
      "Journées Réalisées",
      f"{total_jh:,.0f} JH".replace(",", " "),
  )
  c_j3.metric(
      "Coût Annuel Moyen / Lit",
      f"{(masse_salariale_totale*1000/lits_ouverts_total if lits_ouverts_total>0 else 0):,.0f} {devise}".replace(
          ",", " "
      ),
  )

  df_cout_pole = (
      df_chu.groupby("pole", as_index=False)
      .agg({"masse_salariale_kmad": "sum", "journees_hospitalisation": "sum"})
  )
  df_cout_pole["cout_jh"] = (
      df_cout_pole["masse_salariale_kmad"]
      * 1000
      / df_cout_pole["journees_hospitalisation"]
  )

  fig_jh = px.bar(
      df_cout_pole,
      x="pole",
      y="cout_jh",
      title=f"Coût Salarial par Journée d'Hospitalisation selon le Pôle ({devise}/JH)",
      text="cout_jh",
      labels={"cout_jh": f"Coût / JH ({devise})", "pole": "Pôle"},
      color="cout_jh",
      color_continuous_scale="Teal",
  )
  fig_jh.update_traces(
      texttemplate="%{text:,.0f} " + devise, textposition="outside"
  )
  st.plotly_chart(fig_jh, use_container_width=True)

# --- ONGLET 4 : ABSENTÉISME & CLIMAT HOSPITALIER ---
with tab_absenteisme:
  st.subheader("Diagnostic de Climat & Risques Psychosociaux Hospitaliers")

  a1, a2, a3 = st.columns(3)
  a1.metric(
      "Taux d'Absentéisme Soignant",
      f"{taux_absenteisme:.2f}%",
      delta_color="inverse",
      help="Moyenne hospitalière tolérée : < 5.5%",
  )
  a2.metric(
      "Volume Jours d'Absence",
      f"{jours_abs} jours",
      f"{jours_abs*8} h perdues",
  )
  a3.metric(
      "Facteur Bradford Hospitalier",
      f"{facteur_bradford:.0f} pts",
      help="Mesure la récurrence des micro-arrêts de garde",
  )

  st.markdown("### 🔔 Alertes d'Organisation des Soins")
  if taux_absenteisme > 5.5:
    st.error(
        f"🚨 **Alerte Continuité :** Taux d'absentéisme élevé"
        f" ({taux_absenteisme:.2f}%). Risque de surmenage sur les équipes de"
        " garde et de déprogrammation d'interventions."
    )
  else:
    st.success(
        f"✅ **Situation sous contrôle :** Absentéisme soignant maîtrisé à"
        f" {taux_absenteisme:.2f}%."
    )

  df_abs_mois = (
      df_vue.groupby("mois", as_index=False)["abs_maladie_jours"]
      .sum()
  )
  ordre_mois = ["Janvier", "Fevrier", "Mars", "Avril", "Mai", "Juin"]
  df_abs_mois["mois"] = pd.Categorical(
      df_abs_mois["mois"], categories=ordre_mois, ordered=True
  )
  df_abs_mois = df_abs_mois.sort_values("mois")

  fig_abs = px.line(
      df_abs_mois,
      x="mois",
      y="abs_maladie_jours",
      markers=True,
      title="Évolution Mensuelle des Jours d'Absence pour Maladie",
      labels={"abs_maladie_jours": "Jours d'absence", "mois": "Mois"},
      color_discrete_sequence=["#EF4444"],
  )
  st.plotly_chart(fig_abs, use_container_width=True)

# --- ONGLET 5 : NOTE MÉDICO-ÉCONOMIQUE PDF ---
with tab_pdf:
  st.subheader("📄 Note Médico-Économique Téléchargeable (PDF)")


  def generer_pdf_cgrh_chu(
      periode,
      pol,
      dev,
      med,
      ide,
      adm,
      ms,
      gardes,
      jh,
      c_jh,
      abs_tx,
      logo_path,
  ):
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    if logo_path.exists():
      pdf.image(str(logo_path), x=15, y=10, w=35)
      pdf.set_xy(55, 15)
    else:
      pdf.set_xy(15, 15)

    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(
        0,
        9,
        "TABLEAU DE BORD CGRH & MÉDICO-ÉCONOMIQUE - CHU",
        ln=True,
        align="L" if logo_path.exists() else "C",
    )

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 116, 139)
    if logo_path.exists():
      pdf.set_x(55)
    pdf.cell(
        0,
        6,
        f"Période : {periode} | Périmètre : {pol} | Confidentiel Direction"
        " Générale",
        ln=True,
    )
    pdf.ln(12)

    pdf.set_draw_color(226, 232, 240)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(6)

    # 1. Structure
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(
        0, 8, "1. Structure des Ressources Humaines (Médical / Soins / PATL)", ln=True
    )
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(90, 8, f"  - Corps Medical (Praticiens/PHU) : {med} ETP", 1)
    pdf.cell(90, 8, f"  - Personnel Soignant (IDE/AS) : {ide} ETP", 1, ln=True)
    pdf.cell(90, 8, f"  - Personnel Administratif (PATL) : {adm} ETP", 1)
    pdf.cell(90, 8, f"  - TOTAL EFFECTIF CHU : {med+ide+adm} agents", 1, ln=True)
    pdf.ln(6)

    # 2. Performance Médico-Économique
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(
        0, 8, "2. Coût Salarial & Journées d'Hospitalisation (JH)", ln=True
    )
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(
        90,
        8,
        f"  - Masse Salariale Totale : {ms:,.0f} k{dev}".encode(
            "latin-1", "replace"
        ).decode("latin-1"),
        1,
    )
    pdf.cell(
        90,
        8,
        f"  - Indemnites de Garde : {gardes:,.0f} k{dev}".encode(
            "latin-1", "replace"
        ).decode("latin-1"),
        1,
        ln=True,
    )
    pdf.cell(
        90,
        8,
        f"  - Journees d'Hospitalisation : {jh:,.0f} JH".encode(
            "latin-1", "replace"
        ).decode("latin-1"),
        1,
    )
    pdf.cell(
        90,
        8,
        f"  - Cout RH / Journee : {c_jh:,.0f} {dev}/JH".encode(
            "latin-1", "replace"
        ).decode("latin-1"),
        1,
        ln=True,
    )
    pdf.ln(6)

    # 3. Climat
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "3. Climat Social & Recommandations CGRH", ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(51, 65, 85)
    reco = (
        f"Sur la periode sous revue, le cout moyen RH ressort a {c_jh:,.0f}"
        f" {dev} par journee de soins.\nLe taux d'absenteisme des soignants"
        f" ({abs_tx:.2f}%) necessite une surveillance active afin d'eviter"
        " l'inflation des heures supplementaires et des astreintes.\nIl est"
        " recommande de maintenir l'equilibre des ratios soignants par lit et"
        " de rationaliser les plannings de garde pour stabiliser le climat"
        " social."
    )
    pdf.multi_cell(180, 5, reco, 1)

    return bytes(pdf.output())


  pdf_chu_bytes = generer_pdf_cgrh_chu(
      mois_choisi,
      pole_choisi,
      devise,
      eff_medecins,
      eff_infirmiers,
      eff_admin,
      masse_salariale_totale,
      gardes_totales,
      total_jh,
      cout_rh_par_jh,
      taux_absenteisme,
      chemin_logo,
  )

  st.download_button(
      label="📥 Télécharger la Note Médico-Économique (PDF)",
      data=pdf_chu_bytes,
      file_name=f"Note_CGRH_CHU_{mois_choisi}_{pole_choisi.replace(' ', '_')}.pdf",
      mime="application/pdf",
  )