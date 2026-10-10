from style import appliquer_theme_cockpit_dark
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
appliquer_theme_cockpit_dark()


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
        .diagnostic-card {
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
      "Pilotage de la rentabilité, diagnostic de faillite (Altman Z-Score) et"
      " simulation de gestion moderne."
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
      "Importer un fichier financier",
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
        label="📥 Télécharger le modèle Excel",
        data=tampon_excel,
        file_name="modele_donnees_financieres.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

  st.divider()
  st.header("⚙️ Paramètres")
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
bfr_actuel = (
    df_vue["creances_clients"].iloc[-1]
    + df_vue["stocks"].iloc[-1]
    - df_vue["dettes_fournisseurs"].iloc[-1]
)

# --- CALCUL DU SCORE Z D'ALTMAN (Version Entreprise Privée) ---
# Estimation des agrégats bilantiels moyens
total_actif_estime = max(ca_total * 0.75, 1000)
fonds_de_roulement = bfr_actuel + cash_actuel
reserves_estimees = ebitda_total * 0.4
ebit_estime = ebitda_total * 0.8
capitaux_propres_estimes = total_actif_estime * 0.45
dettes_totales_estimees = total_actif_estime * 0.55

x1 = fonds_de_roulement / total_actif_estime
x2 = reserves_estimees / total_actif_estime
x3 = ebit_estime / total_actif_estime
x4 = capitaux_propres_estimes / dettes_totales_estimees
x5 = ca_total / total_actif_estime

score_z = 0.717 * x1 + 0.847 * x2 + 3.107 * x3 + 0.420 * x4 + 0.998 * x5

# 5. Onglets de Navigation
(
    tab_synthese,
    tab_gestion,
    tab_altman,
    tab_couts_modernes,
    tab_prevision,
    tab_export,
) = st.tabs([
    "📈 Synthèse Direction",
    "⚙️ Rentabilité & BFR",
    "🛡️ Solvabilité & Altman Z-Score",
    "⏱️ Coûts Modernes (TDABC & Cible)",
    "🔮 Prévisions & Simulation",
    "📄 Rapport Exécutif PDF",
])

# --- ONGLET 1 : SYNTHÈSE DIRECTION & ANALYSTE VIRTUEL ---
with tab_synthese:
  st.subheader("Performance Globale & Diagnostic Automatisé")
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

  # ANALYSTE VIRTUEL : SYNTHÈSE CONTEXTUELLE EN TEMPS RÉEL
  st.markdown("### 🤖 Note de Conjoncture de l'Analyste Virtuel")

  points_diagnostic = []
  if ecart_ca >= 0:
    points_diagnostic.append(
        f"L'activité commerciale surperforme l'objectif initial de"
        f" **{ecart_ca:+.1f}%**."
    )
  else:
    points_diagnostic.append(
        f"Le chiffre d'affaires accuse un retard de **{abs(ecart_ca):.1f}%** par"
        " rapport aux engagements budgétaires."
    )

  if taux_marge_brute >= 0.40:
    points_diagnostic.append(
        f"Le pouvoir de fixation des prix (*pricing power*) est solide avec un"
        f" taux de marge brute robuste de **{taux_marge_brute*100:.1f}%**."
    )
  else:
    points_diagnostic.append(
        f"La marge brute ressort à **{taux_marge_brute*100:.1f}%**, reflétant"
        " une pression sur les prix de vente ou une hausse des coûts directs."
    )

  if ccc > 90:
    points_diagnostic.append(
        f"Le cycle de conversion du cash (**{ccc:.0f} jours**) pèse sur la"
        " liquidité : une action ciblée de réduction du délai de recouvrement"
        f" (DSO : {dso:.0f} j) est requise."
    )
  else:
    points_diagnostic.append(
        f"La gestion du besoin en fonds de roulement est performante (**{ccc:.0f}"
        " jours** de cycle d'exploitation)."
    )

  texte_diagnostic = " ".join(points_diagnostic)
  st.markdown(
      f"<div class='diagnostic-card'><b>Diagnostic Stratégique :</b>"
      f" {texte_diagnostic}</div>",
      unsafe_allow_html=True,
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

# --- ONGLET 3 : SOLVABILITÉ & ALTMAN Z-SCORE ---
with tab_altman:
  st.subheader("🛡️ Évaluation du Risque de Défaillance (Altman Z-Score)")
  st.caption(
      "Modèle de référence d'Edward Altman pour entreprises privées / PME : Z'"
      " = 0.717*X1 + 0.847*X2 + 3.107*X3 + 0.420*X4 + 0.998*X5"
  )

  col_z1, col_z2 = st.columns([3, 2])

  with col_z1:
    fig_gauge = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score_z,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "Indice de Santé Financière (Z-Score)"},
            gauge={
                "axis": {"range": [0, 5], "tickwidth": 1},
                "bar": {"color": "#1E3A8A"},
                "steps": [
                    {"range": [0, 1.23], "color": "#FEE2E2"},  # Zone de détresse (Rouge clair)
                    {"range": [1.23, 2.90], "color": "#FEF3C7"},  # Zone grise / surveillance (Jaune)
                    {"range": [2.90, 5], "color": "#D1FAE5"},  # Zone saine (Vert)
                ],
                "threshold": {
                    "line": {"color": "red", "width": 4},
                    "thickness": 0.75,
                    "value": 1.23,
                },
            },
        )
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

  with col_z2:
    st.markdown("#### Interprétation Normative")
    if score_z >= 2.90:
      st.success(
          f"🟢 **Zone Sécurisée (Score : {score_z:.2f})** : L'entreprise"
          " présente une structure de bilan très équilibrée. Le risque de"
          " défaillance à 2 ans est quasi nul."
      )
    elif score_z >= 1.23:
      st.warning(
          f"🟡 **Zone de Surveillance (Score : {score_z:.2f})** : Situation"
          " financière intermédiaire. La solvabilité est maintenue mais une"
          " dégradation du BFR ou de l'EBITDA fragiliserait la structure."
      )
    else:
      st.error(
          f"🔴 **Zone de Vulnérabilité (Score : {score_z:.2f})** : Alerte"
          " critique. Risque élevé de rupture de trésorerie ou de défaillance à"
          " court/moyen terme."
      )

    st.divider()
    st.markdown("**Composantes du modèle :**")
    st.write(f"• **X1 (Liquidité / Actif) :** {x1:.3f}")
    st.write(f"• **X2 (Réserves / Actif) :** {x2:.3f}")
    st.write(f"• **X3 (Productivité Économique - EBIT) :** {x3:.3f}")
    st.write(f"• **X4 (Levier Financier - Fonds Propres/Dettes) :** {x4:.3f}")
    st.write(f"• **X5 (Rotation des Actifs) :** {x5:.3f}")

# --- ONGLET 4 : COÛTS MODERNES (TDABC & TARGET COSTING) ---
with tab_couts_modernes:
  st.subheader("1. Modèle TDABC : Coût Horaire & Capacité Inutilisée")
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
        st.slider("Capacité pratique réelle (%)", 70, 95, 85) / 100.0
    )
    heures_reelles_requises = st.number_input(
        "Volume d'heures effectivement consommées",
        value=float(nb_collaborateurs * heures_mensuelles_base * 0.75),
        step=10.0,
    )

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

  td1, td2, td3, td4 = st.columns(4)
  td1.metric("Capacité Pratique", f"{capacite_pratique:,.0f} h/mois")
  td2.metric(
      "Taux Coût Capacité", f"{taux_cout_unitaire_heure:,.2f} {devise}/h"
  )
  td3.metric("Taux d'Utilisation", f"{taux_utilisation:.1f}%")
  td4.metric(
      "Coût Sous-Activité",
      f"{cout_capacite_inutilisee:,.0f} {devise}",
      delta_color="inverse",
  )

  st.divider()
  st.subheader("2. Simulateur de Target Costing (Coût Cible)")
  tc_col1, tc_col2, tc_col3 = st.columns(3)
  with tc_col1:
    prix_marche = st.number_input(
        f"Prix de vente marché ({devise}/u)", value=1200.0, step=50.0
    )
  with tc_col2:
    taux_marge_exige = st.slider(
        "Marge opérationnelle exigée (%)", 10, 40, 25, step=1
    )
  with tc_col3:
    cout_estime_actuel = st.number_input(
        f"Coût estimé actuel ({devise}/u)", value=980.0, step=20.0
    )

  marge_cible_valeur = prix_marche * (taux_marge_exige / 100.0)
  cout_cible = prix_marche - marge_cible_valeur
  ecart_cible = cout_estime_actuel - cout_cible

  res_tc1, res_tc2, res_tc3 = st.columns(3)
  res_tc1.metric(
      "Coût Cible Autorisé", f"{cout_cible:,.2f} {devise}".replace(",", " ")
  )
  res_tc2.metric(
      "Marge Exigée", f"{marge_cible_valeur:,.2f} {devise}".replace(",", " ")
  )
  if ecart_cible > 0:
    res_tc3.metric(
        "Gap Kaizen (Économie requise)",
        f"+{ecart_cible:,.2f} {devise}".replace(",", " "),
        delta_color="inverse",
    )
  else:
    res_tc3.metric(
        "Surperformance",
        f"{abs(ecart_cible):,.2f} {devise}".replace(",", " "),
        delta_color="normal",
    )

# --- ONGLET 5 : PRÉVISIONS & SIMULATION ---
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

# --- ONGLET 6 : RAPPORT EXÉCUTIF PDF ENRICHI ---
with tab_export:
  st.subheader("📄 Génération de la Synthèse Exécutive (Format PDF)")


  def generer_pdf_rapport(
      periode, dev, ca, ebitda, sr, ccc_val, marge_pct, z_val, logo_path
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
        f"Période : {periode} | Devise : {dev} | Confidentiel Direction",
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
    pdf.cell(0, 8, "2. Rentabilité Critique, BFR & Solvabilité", ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(90, 8, f"  - Seuil de Rentabilité (SR) : {sr:,.0f} {dev}", 1)
    pdf.cell(
        90, 8, f"  - Cash Conversion Cycle : {ccc_val:.0f} jours", 1, ln=True
    )
    pdf.cell(90, 8, f"  - Altman Z-Score : {z_val:.2f}", 1)
    statut_z = "Securise" if z_val >= 2.9 else ("Vigilance" if z_val >= 1.23 else "Alerte")
    pdf.cell(90, 8, f"  - Statut Solvabilite : {statut_z}", 1, ln=True)
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "3. Avis & Recommandations du Contrôleur de Gestion", ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(51, 65, 85)
    texte = (
        f"L'activite affiche un taux de marge de {marge_pct*100:.1f}% et un seuil de rentabilite de {sr:,.0f} {dev}.\n"
        f"Le score Z d'Altman a {z_val:.2f} temoigne d'une solvabilite globale evaluee comme '{statut_z}'.\n"
        f"Sur le plan de la tresorerie, le cycle d'exploitation ({ccc_val:.0f} jours) invite a maintenir les efforts "
        "sur le recouvrement des creances clients pour eviter l'erosion de la reserve disponible."
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
      score_z,
      chemin_logo,
  )

  st.download_button(
      label="📥 Télécharger le Rapport Exécutif & Solvabilité (PDF)",
      data=pdf_bytes,
      file_name=f"Synthese_Direction_Solvabilite_{trimestre_filtre}.pdf",
      mime="application/pdf",
  )