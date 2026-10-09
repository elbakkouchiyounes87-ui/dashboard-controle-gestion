import io
from pathlib import Path
from fpdf import FPDF
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# 1. Vérification de l'authentification
if not st.session_state.get("authentication_status"):
  st.warning("Accès restreint. Veuillez vous connecter sur la page d'accueil.")
  st.stop()

# 2. Configuration & Design Corporate
st.set_page_config(
    page_title="Direction RH & Contrôle Social", page_icon="👥", layout="wide"
)

st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)

# En-tête avec Logo
chemin_racine = Path(__file__).resolve().parent.parent
chemin_logo = chemin_racine / "assets" / "logo.png"

col_head1, col_head2 = st.columns([1, 5])
with col_head1:
  if chemin_logo.exists():
    st.image(str(chemin_logo), width=120)
with col_head2:
  st.title("👥 Direction des Ressources Humaines & Pilotage Social")
  st.caption(
      "Contrôle de gestion sociale : productivité du capital humain, climat"
      " social et développement des talents."
  )

# Déconnexion dans la barre latérale
if "authenticator" in st.session_state:
  st.sidebar.write(f"👤 Connecté : **{st.session_state['name']}**")
  st.session_state["authenticator"].logout("Se déconnecter", "sidebar")


# 3. Chargement des données RH
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

# 4. Filtres de navigation
with st.sidebar:
  st.header("⚙️ Paramètres d'Analyse")
  mois_disponibles = ["Tous les mois"] + list(df_rh["mois"].unique())
  mois_choisi = st.selectbox("Période sous revue", mois_disponibles, index=0)

  depts_disponibles = ["Tous les services"] + list(
      df_rh["departement"].unique()
  )
  dept_choisi = st.selectbox("Département", depts_disponibles, index=0)
  devise = st.radio("Devise", ["MAD", "EUR"])

# Filtrage
df_vue = df_rh.copy()
if mois_choisi != "Tous les mois":
  df_vue = df_vue[df_vue["mois"] == mois_choisi]
if dept_choisi != "Tous les services":
  df_vue = df_vue[df_vue["departement"] == dept_choisi]

# 5. Calculs des Métriques Avancées de Contrôle Social
nb_mois = df_vue["mois"].nunique()
effectif_actuel = (
    df_vue["effectif_total"].sum()
    if mois_choisi != "Tous les mois"
    else df_vue[df_vue["mois"] == "Juin"]["effectif_total"].sum()
)
masse_salariale_totale = df_vue["masse_salariale_kmad"].sum()

# Coût moyen mensuel par collaborateur
cout_moyen_mensuel = (
    (
        masse_salariale_totale
        / (effectif_actuel if effectif_actuel > 0 else 1)
        / nb_mois
    )
    * 1000
    if (effectif_actuel > 0 and nb_mois > 0)
    else 0
)

# Taux de turnover & Coût financier estimé du turnover
total_entrees = df_vue["recrutements"].sum()
total_sorties = df_vue["departs"].sum()
turnover_pct = (
    (
        ((total_entrees + total_sorties) / 2)
        / (effectif_actuel if effectif_actuel > 0 else 1)
    )
    * 100
    if effectif_actuel > 0
    else 0
)
# Coût estimé du turnover : ~6 mois de salaire moyen par collaborateur démissionnaire/remplacé
cout_estime_turnover_kmad = total_sorties * (cout_moyen_mensuel * 6 / 1000)

# Taux d'absentéisme
heures_abs = df_vue["heures_absence"].sum()
heures_theo = df_vue["heures_theoriques"].sum()
taux_absenteisme = (heures_abs / heures_theo * 100) if heures_theo > 0 else 0

# Taux de formation (Heures de formation par salarié)
heures_formation_total = df_vue["heures_formation"].sum()
heures_formation_par_tete = (
    (heures_formation_total / effectif_actuel) if effectif_actuel > 0 else 0
)

# Parité
total_f = df_vue["femmes"].sum()
part_femmes = (
    (total_f / (total_f + df_vue["hommes"].sum()) * 100)
    if (total_f + df_vue["hommes"].sum()) > 0
    else 0
)

# 6. Onglets d'analyse thématique
tab_synthese, tab_demographie, tab_climat, tab_rapport = st.tabs([
    "📊 Synthèse Capital Humain",
    "👥 Démographie & Compétences",
    "⚠️ Diagnostic Climat & Turnover",
    "📄 Bilan Social PDF",
])

# --- ONGLET 1 : SYNTHÈSE CAPITAL HUMAIN ---
with tab_synthese:
  st.subheader("Indicateurs Clés de Gestion des Effectifs & Coûts")
  k1, k2, k3, k4 = st.columns(4)
  k1.metric(
      "Effectif Total Clôture",
      f"{effectif_actuel} salariés",
      f"{total_entrees - total_sorties:+d} solde net",
  )
  k2.metric(
      "Masse Salariale Cumulée",
      f"{masse_salariale_totale:,.0f} k{devise}".replace(",", " "),
  )
  k3.metric(
      "Coût Moyen / Collaborateur",
      f"{cout_moyen_mensuel:,.0f} {devise}/mois".replace(",", " "),
  )
  k4.metric(
      "Taux de Flexibilité (CDD)",
      f"{(df_vue['effectif_cdd'].sum() / df_vue['effectif_total'].sum() * 100):.1f}%",
  )

  st.divider()

  # Évolution Masse Salariale vs Effectifs
  col_s1, col_s2 = st.columns(2)
  with col_s1:
    st.subheader("Évolution Mensuelle de la Masse Salariale")
    df_ms_evol = (
        df_vue.groupby("mois", as_index=False)["masse_salariale_kmad"]
        .sum()
        .sort_values(
            by="mois",
            key=lambda x: [
                "Janvier",
                "Fevrier",
                "Mars",
                "Avril",
                "Mai",
                "Juin",
            ].index(x.iloc[0]),
        )
    )
    fig_ms = px.line(
        df_ms_evol,
        x="mois",
        y="masse_salariale_kmad",
        markers=True,
        labels={
            "masse_salariale_kmad": f"Masse Salariale (k{devise})",
            "mois": "Mois",
        },
        color_discrete_sequence=["#1E3A8A"],
    )
    st.plotly_chart(fig_ms, use_container_width=True)

  with col_s2:
    st.subheader("Répartition des Collaborateurs par Service")
    mois_ref = mois_choisi if mois_choisi != "Tous les mois" else "Juin"
    df_pie = (
        df_rh[df_rh["mois"] == mois_ref]
        .groupby("departement")["effectif_total"]
        .sum()
        .reset_index()
    )
    fig_repart = px.pie(
        df_pie,
        names="departement",
        values="effectif_total",
        hole=0.45,
        color_discrete_sequence=px.colors.qualitative.Prism,
    )
    st.plotly_chart(fig_repart, use_container_width=True)

# --- ONGLET 2 : DÉMOGRAPHIE & FORMATION ---
with tab_demographie:
  st.subheader("1. Structure des Âges & Pyramide Simplifiée")
  p1, p2, p3, p4 = st.columns(4)

  total_jeunes = df_vue["tranche_moins_30"].sum()
  total_inter = df_vue["tranche_30_45"].sum()
  total_seniors = df_vue["tranche_plus_45"].sum()

  p1.metric(
      "< 30 ans (Jeunes Talents)",
      f"{(total_jeunes / (total_jeunes + total_inter + total_seniors) * 100):.1f}%",
  )
  p2.metric(
      "30 - 45 ans (Cœur d'Activité)",
      f"{(total_inter / (total_jeunes + total_inter + total_seniors) * 100):.1f}%",
  )
  p3.metric(
      "> 45 ans (Seniors / Expertise)",
      f"{(total_seniors / (total_jeunes + total_inter + total_seniors) * 100):.1f}%",
  )
  p4.metric("Indice Parité Femmes", f"{part_femmes:.1f}%")

  # Graphique de répartition des tranches d'âge par département
  df_age = (
      df_vue.groupby("departement", as_index=False)[
          ["tranche_moins_30", "tranche_30_45", "tranche_plus_45"]
      ]
      .sum()
      .rename(
          columns={
              "tranche_moins_30": "< 30 ans",
              "tranche_30_45": "30-45 ans",
              "tranche_plus_45": "> 45 ans",
          }
      )
  )

  fig_age = px.bar(
      df_age,
      x="departement",
      y=["< 30 ans", "30-45 ans", "> 45 ans"],
      barmode="stack",
      title="Structure Générationnelle par Département",
      labels={"value": "Nombre de Collaborateurs", "departement": "Service"},
      color_discrete_map={
          "< 30 ans": "#93C5FD",
          "30-45 ans": "#2563EB",
          "> 45 ans": "#1E3A8A",
      },
  )
  st.plotly_chart(fig_age, use_container_width=True)

  st.divider()
  st.subheader("2. Effort de Développement des Compétences")
  f1, f2 = st.columns(2)
  f1.metric("Volume Global de Formation", f"{heures_formation_total} heures")
  f2.metric(
      "Intensité de Formation / Salarié", f"{heures_formation_par_tete:.1f} h"
  )

# --- ONGLET 3 : DIAGNOSTIC CLIMAT & RISQUE SOCIAL ---
with tab_climat:
  st.subheader("Indicateurs de Risque Social & Coûts d'Attrition")
  r1, r2, r3, r4 = st.columns(4)
  r1.metric(
      "Taux d'Absentéisme",
      f"{taux_absenteisme:.2f}%",
      delta_color="inverse",
      help="Seuil d'alerte moyen : > 4.5%",
  )
  r2.metric(
      "Taux de Turnover Annuel",
      f"{turnover_pct:.2f}%",
      delta_color="inverse",
      help="Taux de rotation externe",
  )
  r3.metric(
      "Départs Effectifs",
      f"{total_sorties} sorties",
      f"{total_entrees} recrutés",
  )
  r4.metric(
      "Coût Financier du Turnover",
      f"{cout_estime_turnover_kmad:,.0f} k{devise}".replace(",", " "),
      help="Coût estimé des départs (remplacement, perte de savoir-faire).",
  )

  # Alertes automatiques
  st.markdown("### 🔔 Diagnostic Automatique de Climat Social")
  a1, a2 = st.columns(2)
  with a1:
    if taux_absenteisme > 3.0:
      st.warning(
          f"⚠️ **Alerte Absentéisme :** Taux de {taux_absenteisme:.2f}%. Forte"
          " concentration constatée sur le pôle Opérations."
      )
    else:
      st.success(
          f"✅ **Climat stable :** Taux d'absentéisme maîtrisé"
          f" ({taux_absenteisme:.2f}%)."
      )
  with a2:
    if turnover_pct > 5.0:
      st.error(
          f"🚨 **Risque de Rétention :** Turnover de {turnover_pct:.2f}%."
          " Vigilance accrue sur les services Commerciaux."
      )
    else:
      st.success(
          f"✅ **Stabilité des équipes :** Faible taux de rotation"
          f" ({turnover_pct:.2f}%)."
      )

  # Graphique combiné Absentéisme & Masse Salariale
  df_abs = df_vue.groupby("mois", as_index=False).agg(
      {"heures_absence": "sum", "heures_theoriques": "sum"}
  )
  df_abs["taux"] = (df_abs["heures_absence"] / df_abs["heures_theoriques"]) * 100

  fig_abs = px.bar(
      df_abs,
      x="mois",
      y="taux",
      title="Évolution du Taux d'Absentéisme Mensuel (%)",
      labels={"taux": "Taux d'Absentéisme (%)", "mois": "Mois"},
      color="taux",
      color_continuous_scale="Reds",
  )
  st.plotly_chart(fig_abs, use_container_width=True)

# --- ONGLET 4 : BILAN SOCIAL PDF ---
with tab_rapport:
  st.subheader("📄 Bilan Social Synthétique Téléchargeable")
  st.write(
      "Ce document consolide les indicateurs sociaux réglementaires et d'audit"
      " RH pour la direction."
  )


  def generer_pdf_rh(
      periode,
      dev,
      effectif,
      ms,
      cout_moyen,
      abs_taux,
      to_taux,
      formation_h,
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

    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(
        0,
        10,
        "BILAN SOCIAL & CONTRÔLE DE GESTION RH",
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
        f"Période sous revue : {periode} | Données Confidentielles RH",
        ln=True,
    )
    pdf.ln(12)

    pdf.set_draw_color(226, 232, 240)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(8)

    # 1. Structure de l'Emploi
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 8, "1. Structure de l'Emploi et Masse Salariale", ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(90, 8, f"  - Effectif Total Cloture : {effectif} salaries", 1)
    pdf.cell(
        90, 8, f"  - Masse Salariale Totale : {ms:,.0f} k{dev}".encode("latin-1", "replace").decode("latin-1"), 1, ln=True
    )
    pdf.cell(
        90,
        8,
        f"  - Cout Moyen / Collaborateur : {cout_moyen:,.0f} {dev}/mois".encode("latin-1", "replace").decode("latin-1"),
        1,
    )
    pdf.cell(90, 8, f"  - Heures de Formation Dispensees : {formation_h} h", 1, ln=True)
    pdf.ln(6)

    # 2. Climat Social
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "2. Indicateurs de Climat Social & Rotation", ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(90, 8, f"  - Taux d'Absenteisme : {abs_taux:.2f} %", 1)
    pdf.cell(90, 8, f"  - Taux de Turnover : {to_taux:.2f} %", 1, ln=True)
    pdf.ln(6)

    # 3. Commentaires & Audit
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "3. Diagnostic & Plan d'Action Social", ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(51, 65, 85)
    avis = (
        f"L'effectif se stabilise a {effectif} collaborateurs avec une masse salariale controlee "
        f"a {ms:,.0f} k{dev}. L'effort de formation soutenu ({formation_h} heures) accompagne la montee en competence.\n"
        f"Le controleur de gestion sociale recommande une surveillance sur le taux d'absenteisme ({abs_taux:.2f}%) "
        "et la mise en place d'actions de retention sur les metiers sous tension."
    )
    pdf.multi_cell(180, 5, avis, 1)

    return bytes(pdf.output())


  pdf_rh_bytes = generer_pdf_rh(
      mois_choisi,
      devise,
      effectif_actuel,
      masse_salariale_totale,
      cout_moyen_mensuel,
      taux_absenteisme,
      turnover_pct,
      heures_formation_total,
      chemin_logo,
  )

  st.download_button(
      label="📥 Télécharger le Bilan Social (PDF)",
      data=pdf_rh_bytes,
      file_name=f"Bilan_Social_{mois_choisi}_{dept_choisi}.pdf",
      mime="application/pdf",
  )