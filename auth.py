import streamlit as st

# Dictionnaire des utilisateurs autorisés : "identifiant": "mot_de_passe"
UTILISATEURS_AUTORISES = {
    "admin": "Admin@2026",
    "direction": "Management2026",
}


def verifier_authentification():
  """Vérifie si l'utilisateur est connecté via un identifiant et mot de passe.

  Bloque l'affichage tant que la connexion n'est pas établie.
  """
  if "est_authentifie" not in st.session_state:
    st.session_state["est_authentifie"] = False
  if "utilisateur_connecte" not in st.session_state:
    st.session_state["utilisateur_connecte"] = None

  if not st.session_state["est_authentifie"]:
    # Centrage du formulaire de connexion
    col_gauche, col_centre, col_droite = st.columns([1, 1.8, 1])

    with col_centre:
      st.markdown("<br><br>", unsafe_allow_html=True)
      with st.container(border=True):
        st.markdown(
            "<h2 style='text-align: center; margin-bottom: 2px;'>🔒 Espace"
            " Sécurisé</h2>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='text-align: center; color: #64748B; font-size: 0.9rem;"
            " margin-bottom: 20px;'>Portail Décisionnel d'Entreprise - Données"
            " Confidentielles</p>",
            unsafe_allow_html=True,
        )

        with st.form("formulaire_connexion"):
          identifiant_saisi = st.text_input(
              "Identifiant :",
              placeholder="Nom d'utilisateur...",
              key="login_user",
          )
          mdp_saisi = st.text_input(
              "Mot de passe :",
              type="password",
              placeholder="••••••••••••",
              key="login_pwd",
          )

          st.write("")
          bouton_valider = st.form_submit_button(
              "Se connecter ➔", use_container_width=True, type="primary"
          )

          if bouton_valider:
            identifiant_clean = identifiant_saisi.strip()
            if (
                identifiant_clean in UTILISATEURS_AUTORISES
                and UTILISATEURS_AUTORISES[identifiant_clean] == mdp_saisi
            ):
              st.session_state["est_authentifie"] = True
              st.session_state["utilisateur_connecte"] = identifiant_clean
              st.rerun()
            else:
              st.error("❌ Identifiant ou mot de passe incorrect.")

    # Arrêt de l'exécution du reste de la page
    st.stop()


def afficher_bouton_deconnexion():
  """Affiche le statut de connexion et le bouton pour se déconnecter."""
  with st.sidebar:
    st.divider()
    user = st.session_state.get("utilisateur_connecte", "Utilisateur")
    st.caption(f"Connecté en tant que : **{user}**")
    if st.button("🚪 Se déconnecter", use_container_width=True):
      st.session_state["est_authentifie"] = False
      st.session_state["utilisateur_connecte"] = None
      st.rerun()