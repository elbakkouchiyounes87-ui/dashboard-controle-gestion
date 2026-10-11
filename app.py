import streamlit as st
from pathlib import Path
from style import appliquer_theme_cockpit_dark

# Configuration de la page principale
st.set_page_config(
    page_title="Portail Entreprise - Tableaux de Bord",
    page_icon="🏢",
    layout="wide"
)
import streamlit as st
from pathlib import Path
from style import appliquer_theme_cockpit_dark
from auth import verifier_authentification, afficher_bouton_deconnexion

# Configuration de la page principale
st.set_page_config(
    page_title="Portail Entreprise - Tableaux de Bord",
    page_icon="🏢",
    layout="wide"
)

# Application du thème
appliquer_theme_cockpit_dark()

# 🔒 VÉRIFICATION DU CODE D'ACCÈS
verifier_authentification()
afficher_bouton_deconnexion()

# ... (le reste de votre code app.py continue normalement ci-dessous)
# Application du thème corporate clair
appliquer_theme_cockpit_dark()

# CSS pour le style des cartes de navigation
st.markdown("""
    <style>
        .hero-title {
            font-size: 2.3rem;
            font-weight: 800;
            color: #0F172A;
            margin-bottom: 6px;
        }
        .hero-subtitle {
            font-size: 1.05rem;
            color: #64748B;
            margin-bottom: 28px;
        }
        .service-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 12px;
        }
        .badge-finance { background-color: #EFF6FF; color: #1D4ED8; }
        .badge-rh { background-color: #FDF2F8; color: #BE185D; }
        .badge-ventes { background-color: #ECFDF5; color: #047857; }
        
        .kpi-pill {
            display: inline-block;
            background: #F1F5F9;
            color: #475569;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.78rem;
            margin: 2px 2px;
            font-weight: 500;
        }
    </style>
""", unsafe_allow_html=True)

# En-tête principal avec logo si existant
chemin_racine = Path(__file__).resolve().parent
chemin_logo = chemin_racine / "assets" / "logo.png"

col_logo, col_titre = st.columns([1, 6])
with col_logo:
    if chemin_logo.exists():
        st.image(str(chemin_logo), width=110)
    else:
        st.markdown("<h1 style='font-size: 3rem; margin:0;'>🏢</h1>", unsafe_allow_html=True)

with col_titre:
    st.markdown("<div class='hero-title'>Portail Décisionnel & Pilotage d'Entreprise</div>", unsafe_allow_html=True)
    st.markdown("<div class='hero-subtitle'>Plateforme de pilotage de la performance : sélectionnez un pôle d'activité pour accéder à votre espace de gestion.</div>", unsafe_allow_html=True)

st.divider()

# Grille de sélection des 3 Pôles d'Entreprise
col1, col2, col3 = st.columns(3, gap="medium")

# --- CARTE 1 : FINANCE ---
with col1:
    with st.container(border=True):
        st.markdown("<span class='service-badge badge-finance'>Direction Financière</span>", unsafe_allow_html=True)
        st.subheader("💰 Pilotage Financier")
        st.write("Gestion des résultats, rentabilité d'exploitation, analyse BFR et diagnostic de solvabilité bancaire.")
        
        st.markdown("""
            <div>
                <span class='kpi-pill'>Altman Z-Score</span>
                <span class='kpi-pill'>Point Mort</span>
                <span class='kpi-pill'>CCC / BFR</span>
                <span class='kpi-pill'>TDABC</span>
            </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Accéder à l'espace Finance ➔", key="btn_fin", use_container_width=True):
            st.switch_page("pages/1_💰_Finance.py")

# --- CARTE 2 : RESSOURCES HUMAINES ---
with col2:
    with st.container(border=True):
        st.markdown("<span class='service-badge badge-rh'>Capital Humain</span>", unsafe_allow_html=True)
        st.subheader("👥 Ressources Humaines")
        st.write("Audit social, évolution de la masse salariale, pyramide des âges et indicateurs de perturbation du travail.")
        
        st.markdown("""
            <div>
                <span class='kpi-pill'>HCROI</span>
                <span class='kpi-pill'>Facteur Bradford</span>
                <span class='kpi-pill'>Effet Noria & GVT</span>
                <span class='kpi-pill'>Bilan Social</span>
            </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Accéder à l'espace RH ➔", key="btn_rh", use_container_width=True):
            st.switch_page("pages/2_👥_RH.py")

# --- CARTE 3 : VENTES & OPERATIONS ---
with col3:
    with st.container(border=True):
        st.markdown("<span class='service-badge badge-ventes'>Opérations & Commerce</span>", unsafe_allow_html=True)
        st.subheader("📈 Commercial & Ventes")
        st.write("Pipeline des devis, rentabilité cumulative par produit/canal et matrice stratégique de marge.")
        
        st.markdown("""
            <div>
                <span class='kpi-pill'>Funnel Pipeline</span>
                <span class='kpi-pill'>Courbe de Stobach</span>
                <span class='kpi-pill'>Matrice BCG</span>
                <span class='kpi-pill'>Vélocité</span>
            </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Accéder à l'espace Ventes ➔", key="btn_ventes", use_container_width=True):
            st.switch_page("pages/3_📈_Ventes.py")

st.divider()

# Bandeau récapitulatif en pied de portail
r1, r2, r3 = st.columns(3)
with r1:
    st.info("🔒 **Accès Sécurisé** : Données internes confidentielles pour comités de direction.")
with r2:
    st.success("⚡ **Données Temps Réel** : Indicateurs synchronisés et recalculés en continu.")
with r3:
    st.warning("📄 **Rapports PDF** : Édition des comptes-rendus disponible sur chaque module.")