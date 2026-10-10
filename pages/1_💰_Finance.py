import io
from pathlib import Path
from fpdf import FPDF
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# 1. Configuration & Design Corporate
st.set_page_config(
    page_title="Direction Financière - Pilotage Stratégique",
    page_icon="💰",
    layout="wide",
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

# 2. Affichage de l'en-tête et logo
chemin_racine = Path(__file__).resolve().parent.parent
chemin_logo = chemin_racine / "assets" / "logo.png"

col_h1, col_h2 = st.columns([1, 5])
with col_h1:
  if chemin_logo.exists():
    st.image(str(chemin_logo), width=120)
with col_h2:
  st.title("💰 Direction Financière & Contrôle Stratégique")
  st.caption(
      "Pilotage de la rentabilité, du BFR, prévisions budgétaires et calcul de"
      " coûts avancés (TDABC & Target Costing)."
  )


# 3. Chargement des données
def charger_donnees_demo():
  chemin_csv = chemin_racine / "donnees_controle_gestion.csv"
  if not chemin_csv.exists():
    chemin_csv = Path(__file__).resolve().parent / "donnees_controle_gestion.csv"
  if chemin_csv.exists():
    return pd.read_csv(chemin_csv)
  return None


with st.sidebar:
  st.header("📂 Données de l'Entreprise")
  fichier_importe = st.file_uploader(
      "Importer votre fichier financier",
      type=["csv", "xlsx", "xls"],
      help="Chargez votre balance ou tableau d'exploitation mensuel.",
  )

  if fichier_importe is not None:
    try:
      if fichier_importe.name.endswith(".csv"):
        df = pd.read_csv(fichier_importe)
      else:
        df = pd.read_excel(fichier_importe)
      st.success("✅ Données entreprise chargées !")
    except Exception as e:
      st.error(f"Erreur de lecture : {e}")
      df = charger_donnees_demo()
  else:
    df = charger_donnees_demo()
    st.info("ℹ️ Données de démonstration actives.")

  if df is not None:
    tampon_excel = io.BytesIO()
    with pd.ExcelWriter(tampon_excel, engine="openpyxl") as writer:
      df.to_excel(writer, index=False, sheet_name="Modele_Financier")
    tampon_excel.seek(0)
    st.download_button(
        label="📥 Télécharger le modèle Excel vierge",
        data=tampon_excel,
        file_name="modele_donnees_financieres.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

  st.divider()
  st.header("⚙️ Paramètres d'analyse")
  options_trimestre = (
      ["Année Complète"] + sorted(list(df["trimestre"].unique()))
      if df is not None and "trimestre" in df.columns
      else ["Année Complète"]
  )
  trimestre_filtre = st.selectbox("Période sous revue", options_trimestre)
  devise = st.radio("Devise de restitution", ["kMAD", "kEUR", "kUSD"])

if df is None:
  st.error("Aucune donnée disponible.")
  st.stop()

# 4. Filtrage et Calculs Financiers de Base
df_vue = (
    df
    if trimestre_filtre == "Année Complète"
    else df[df["trimestre"] == trimestre_filtre].copy()
)

ca_total = df_vue["ca_realise"].sum()
ca_budget_total = df_vue["ca_budget"].sum()
cogs_total = df_vue["cogs_realise"].sum()
charges_fixes = (
    df_vue["charges_personnel"].sum() + df_vue["autres_charges_fixes"].sum()
)
ebitda_total = df_vue["ebitda_realise"].sum()
marge_brute = ca_total - cogs_total
taux_marge_brute = (marge_brute / ca_total) if ca_total > 0 else 0

# Seuil de rentabilité & BFR
seuil_rentabilite = (
    (charges_fixes / taux_marge_brute) if taux_marge_brute > 0 else 0
)
nb_jours_periode = len(df_vue) * 30
point_mort_jours = (
    (seuil_rentabilite / ca_total * nb_jours_periode) if ca_total > 0 else 0
)
marge_securite = ca_total - seuil_rentabilite
indice_securite = (marge_securite / ca_total * 100) if ca_total > 0 else 0

creances_moy = df_vue["creances_clients"].mean()
stocks_moy = df_vue["stocks"].mean()
dettes_moy = df_vue["dettes_fournisseurs"].mean()

dso = (creances_moy / ca_total * nb_jours_periode) if ca_total > 0 else 0
dio = (stocks_moy / cogs_total * nb_jours_periode) if cogs_total > 0 else 0
dpo = (dettes_moy / cogs_total * nb_jours_periode) if cogs_total > 0 else 0
ccc = dso + dio - dpo
cash_actuel = df_vue["tresorerie_nette"].iloc[-1]

# 5. Onglets de Navigation
tab_synthese, tab_gestion, tab_couts_modernes, tab_prevision, tab_export = (
    st.tabs([
        "📈 Synthèse Direction",
        "⚙️ Rentabilité & BFR",
        "⏱️ Coûts Modernes (TDABC & Cible)",
        "🔮 Prévisions & Simulation",
        "📄 Rapport Exécutif PDF",
    ])
)

# --- ONGLET 1 : SYNTHÈSE DIRECTION ---
with tab_synthese:
  st.subheader("Performance Globale de la Période")
  c1, c2, c3, c4 = st.columns(4)
  ecart_ca = (
      ((ca_total - ca_budget_total) / ca_budget_total * 100)
      if ca_budget_total > 0
      else 0
  )
  c1.metric(
      "Chiffre d'Affaires",
      f"{ca_total:,.0f} {devise}".replace(",", " "),
      f"{ecart_ca:+.1f}% vs Budget",
  )
  c2.metric(
      "Marge Brute",
      f"{marge_brute:,.0f} {devise}".replace(",", " "),
      f"Taux: {taux_marge_brute*100:.1f}%",
  )
  c3.metric(
      "EBITDA",
      f"{ebitda_total:,.0f} {devise}".replace(",", " "),
      f"{(ebitda_total/ca_total*100):.1f}% du CA",
  )
  c4.metric(
      "Trésorerie Clôture", f"{cash_actuel:,.0f} {devise}".replace(",", " ")
  )

  st.markdown("### 🔔 Alertes et Diagnostic Automatisé")
  alert_col1, alert_col2 = st.columns(2)
  with alert_col1:
    if ccc > 90:
      st.warning(
          f"⚠️ **Attention Cash :** Cycle CCC allongé ({ccc:.0f} jours)."
          " Liquidités immobilisées dans le BFR."
      )
    else:
      st.success(f"✅ **Cycle d'exploitation maîtrisé :** CCC à {ccc:.0f} jours.")
  with alert_col2:
    if ca_total >= seuil_rentabilite:
      st.success(
          f"✅ **Activité bénéficiaire :** Marge de sécurité de"
          f" {marge_securite:,.0f} {devise} ({indice_securite:.1f}%)."
      )
    else:
      st.error(
          "🚨 **Déficit d'exploitation :** Activité inférieure au seuil de"
          f" rentabilité de {(seuil_rentabilite - ca_total):,.0f} {devise}."
      )

  fig_ca = px.bar(
      df_vue,
      x="mois",
      y=["ca_realise", "ca_budget"],
      barmode="group",
      title=f"Suivi d'Activité Réalisé vs Budget ({devise})",
      labels={
          "value": f"Montant ({devise})",
          "variable": "Série",
          "mois": "Mois",
      },
      color_discrete_map={"ca_realise": "#1E3A8A", "ca_budget": "#93C5FD"},
  )
  st.plotly_chart(fig_ca, use_container_width=True)

# --- ONGLET 2 : RENTABILITÉ & BFR ---
with tab_gestion:
  st.subheader("1. Seuil de Rentabilité & Marge de Sécurité")
  pm1, pm2, pm3, pm4 = st.columns(4)
  pm1.metric(
      "Seuil de Rentabilité (SR)",
      f"{seuil_rentabilite:,.0f} {devise}".replace(",", " "),
  )
  pm2.metric("Point Mort Temporel", f"{point_mort_jours:.0f} jours")
  pm3.metric(
      "Marge de Sécurité", f"{marge_securite:,.0f} {devise}".replace(",", " ")
  )
  pm4.metric("Indice de Sécurité", f"{indice_securite:.1f}%")

  st.divider()
  st.subheader("2. Cycle de Conversion du Cash (CCC = DSO + DIO - DPO)")
  ccc_col1, ccc_col2, ccc_col3, ccc_col4 = st.columns(4)
  ccc_col1.metric("CCC (Cycle Global Cash)", f"{ccc:.0f} jours")
  ccc_col2.metric("DSO (Crédit Clients)", f"{dso:.0f} jours")
  ccc_col3.metric("DIO (Rotation Stocks)", f"{dio:.0f} jours")
  ccc_col4.metric("DPO (Crédit Fournisseurs)", f"{dpo:.0f} jours")

  fig_ccc = go.Figure(
      go.Bar(
          x=[
              "DSO (Clients)",
              "DIO (Stocks)",
              "DPO (Fournisseurs négatif)",
              "Cycle Cash (CCC)",
          ],
          y=[dso, dio, -dpo, ccc],
          marker_color=["#3B82F6", "#F59E0B", "#EF4444", "#10B981"],
          text=[f"{v:.0f} j" for v in [dso, dio, -dpo, ccc]],
          textposition="auto",
      )
  )
  fig_ccc.update_layout(
      title="Décomposition du Cycle de Trésorerie (en jours)",
      yaxis_title="Jours",
  )
  st.plotly_chart(fig_ccc, use_container_width=True)

# --- ONGLET 3 : COÛTS MODERNES (TDABC & TARGET COSTING) ---
with tab_couts_modernes:
  st.subheader("1. Modèle TDABC : Coût Horaire & Capacité Inutilisée")
  st.caption(
      "Approche Robert Kaplan (Harvard) : mesure le coût unitaire de capacité"
      " et valorise la sous-activité sans pénaliser le coût des processus."
  )

  col_t1, col_t2 = st.columns(2)
  with col_t1:
    cout_ressources = st.number_input(
        f"Coût total du pôle/service ({devise})",
        value=float(charges_fixes),
        step=50.0,
    )
    nb_collaborateurs = st.number_input(
        "Effectif productif du pôle (ETP)", value=25, min_value=1
    )
    heures_mensuelles_base = st.number_input(
        "Heures contractuelles / mois / salarié", value=160, min_value=50
    )

  with col_t2:
    taux_efficience = (
        st.slider(
            "Capacité pratique réelle (%)",
            min_value=70,
            max_value=95,
            value=85,
            help="Prend en compte les pauses, réunions internes et maintenance.",
        )
        / 100.0
    )
    heures_reelles_requises = st.number_input(
        "Volume d'heures effectivement consommées sur les dossiers",
        value=float(nb_collaborateurs * heures_mensuelles_base * 0.75),
        step=10.0,
    )

  # Calculs TDABC
  capacite_theorique = nb_collaborateurs * heures_mensuelles_base
  capacite_pratique = capacite_theorique * taux_efficience
  taux_cout_unitaire_heure = (
      (cout_ressources / capacite_pratique) if capacite_pratique > 0 else 0
  )

  heures_inutilisees = max(0.0, capacite_pratique - heures_reelles_requises)
  cout_capacite_inutilisee = heures_inutilisees * taux_cout_unitaire_heure
  taux_utilisation = (
      (heures_reelles_requises / capacite_pratique * 100)
      if capacite_pratique > 0
      else 0
  )

  st.write("")
  td1, td2, td3, td4 = st.columns(4)
  td1.metric(
      "Capacité Pratique",
      f"{capacite_pratique:,.0f} h/mois",
      f"{capacite_theorique:,.0f} h théoriques",
  )
  td2.metric(
      "Taux Coût de Capacité",
      f"{taux_cout_unitaire_heure:,.2f} {devise}/heure",
      help="Coût horaire standard d'imputation TDABC",
  )
  td3.metric(
      "Taux d'Utilisation Réel",
      f"{taux_utilisation:.1f}%",
      delta_color="normal" if taux_utilisation >= 80 else "inverse",
  )
  td4.metric(
      "Coût de Sous-Activité",
      f"{cout_capacite_inutilisee:,.0f} {devise}",
      help="Montant des charges payées mais non absorbées par les opérations.",
  )

  # Graphique de répartition de la capacité
  fig_capa = go.Figure(
      go.Bar(
          x=["Heures Opérationnelles Utilisées", "Capacité Non Exploitée"],
          y=[heures_reelles_requises, heures_inutilisees],
          marker_color=["#1E3A8A", "#F59E0B"],
          text=[
              f"{heures_reelles_requises:,.0f} h",
              f"{heures_inutilisees:,.0f} h",
          ],
          textposition="auto",
      )
  )
  fig_capa.update_layout(
      title="Bilan d'Absorption de la Capacité Opérationnelle (en Heures)",
      yaxis_title="Heures",
  )
  st.plotly_chart(fig_capa, use_container_width=True)

  st.divider()

  # TARGET COSTING
  st.subheader("2. Simulateur de Target Costing (Coût Cible & Dérive de Valeur)")
  st.caption(
      "Méthode inversée : Prix de Vente Marché - Marge Exigée = Coût Cible"
      " Autorisé."
  )

  tc_col1, tc_col2, tc_col3 = st.columns(3)
  with tc_col1:
    prix_marche = st.number_input(
        f"Prix de vente cible marché ({devise}/unité)", value=1200.0, step=50.0
    )
  with tc_col2:
    taux_marge_exige = st.slider(
        "Marge opérationnelle exigée (%)", 10, 40, 25, step=1
    )
  with tc_col3:
    cout_estime_actuel = st.number_input(
        f"Coût de revient estimé actuel ({devise}/unité)",
        value=980.0,
        step=20.0,
    )

  marge_cible_valeur = prix_marche * (taux_marge_exige / 100.0)
  cout_cible = prix_marche - marge_cible_valeur
  ecart_cible = cout_estime_actuel - cout_cible

  res_tc1, res_tc2, res_tc3 = st.columns(3)
  res_tc1.metric(
      "Coût Cible Autorisé", f"{cout_cible:,.2f} {devise}".replace(",", " ")
  )
  res_tc2.metric(
      "Marge Unitaire Exigée",
      f"{marge_cible_valeur:,.2f} {devise}".replace(",", " "),
  )
  if ecart_cible > 0:
    res_tc3.metric(
        "Dérive de Coût (Gap Kaizen)",
        f"+{ecart_cible:,.2f} {devise}".replace(",", " "),
        delta_color="inverse",
        help="Montant d'économies à réaliser en conception ou négociation.",
    )
    st.error(
        f"🚨 **Écart de rentabilité :** Le coût actuel dépasse le coût cible de"
        f" **{ecart_cible:,.2f} {devise}** par unité. Action requise : analyse"
        " de la valeur ou réduction des coûts composants."
    )
  else:
    res_tc3.metric(
        "Surperformance Coût Cible",
        f"{abs(ecart_cible):,.2f} {devise}".replace(",", " "),
        delta_color="normal",
    )
    st.success(
        "✅ **Objectif atteint :** Le coût de revient respecte l'exigence de"
        " marge de l'entreprise."
    )

# --- ONGLET 4 : PRÉVISIONS & SIMULATION ---
with tab_prevision:
  st.subheader("Simulateur d'Impact Budgétaire (What-If)")
  sim_c1, sim_c2 = st.columns(2)
  with sim_c1:
    hypothese_ca = st.slider("Hypothèse de croissance CA (%)", -25, 25, 5, step=1)
  with sim_c2:
    hypothese_cogs = st.slider(
        "Variation des coûts matières/achats (%)", -20, 20, 2, step=1
    )

  ca_proj = ca_total * (1 + hypothese_ca / 100)
  cogs_proj = cogs_total * (1 + hypothese_cogs / 100)
  ebitda_proj = (ca_proj - cogs_proj) - charges_fixes

  res1, res2, res3 = st.columns(3)
  res1.metric(
      "CA Projeté",
      f"{ca_proj:,.0f} {devise}".replace(",", " "),
      delta=f"{hypothese_ca:+}%",
  )
  res2.metric(
      "EBITDA Projeté",
      f"{ebitda_proj:,.0f} {devise}".replace(",", " "),
      delta=f"{(ebitda_proj - ebitda_total):+,.0f} {devise}",
  )
  nouv_sr = (
      (charges_fixes / ((ca_proj - cogs_proj) / ca_proj))
      if (ca_proj - cogs_proj) > 0
      else 0
  )
  res3.metric(
      "Nouveau Seuil Rentabilité", f"{nouv_sr:,.0f} {devise}".replace(",", " ")
  )

# --- ONGLET 5 : RAPPORT EXÉCUTIF PDF ---
with tab_export:
  st.subheader("📄 Génération de la Synthèse Exécutive (Format PDF)")


  def generer_pdf_rapport(
      periode, dev, ca, ebitda, sr, ccc_val, marge_pct, logo_path
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
        "NOTE DE SYNTHÈSE FINANCIÈRE & GESTION",
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
        f"Période sous revue : {periode} | Devise : {dev} | Confidentiel"
        " Direction",
        ln=True,
    )
    pdf.ln(12)

    pdf.set_draw_color(226, 232, 240)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 8, "1. Performance Économique & Soldes Intermédiaires", ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(90, 8, f"  - Chiffre d'Affaires : {ca:,.0f} {dev}", 1)
    pdf.cell(90, 8, f"  - Taux Marge Brute : {marge_pct*100:.1f} %", 1, ln=True)
    pdf.cell(90, 8, f"  - EBITDA Réalisé : {ebitda:,.0f} {dev}", 1)
    pdf.cell(
        90,
        8,
        f"  - Marge EBITDA / CA : {(ebitda/ca*100 if ca>0 else 0):.1f} %",
        1,
        ln=True,
    )
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "2. Rentabilité Critique & Cycle d'Exploitation", ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(90, 8, f"  - Seuil de Rentabilité (SR) : {sr:,.0f} {dev}", 1)
    pdf.cell(
        90, 8, f"  - Cash Conversion Cycle : {ccc_val:.0f} jours", 1, ln=True
    )
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "3. Observations & Recommandations Stratégiques", ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(51, 65, 85)
    texte = (
        f"L'activité dégage une rentabilité brute de {marge_pct*100:.1f}%.\n"
        f"Le point mort critique d'exploitation est fixé à {sr:,.0f} {dev}. "
        f"Le cycle de conversion de cash ({ccc_val:.0f} jours) indique un"
        " besoin d'attention continue sur le recouvrement des créances clients"
        " (DSO) et la rotation des stocks pour préserver les liquidités"
        " disponibles."
    )
    pdf.multi_cell(180, 5, texte, 1)

    return bytes(pdf.output())


  pdf_bytes = generer_pdf_rapport(
      trimestre_filtre,
      devise,
      ca_total,
      ebitda_total,
      seuil_rentabilite,
      ccc,
      taux_marge_brute,
      chemin_logo,
  )

  st.download_button(
      label="📥 Télécharger le Rapport Exécutif (PDF)",
      data=pdf_bytes,
      file_name=f"Synthese_Direction_{trimestre_filtre}.pdf",
      mime="application/pdf",
  )