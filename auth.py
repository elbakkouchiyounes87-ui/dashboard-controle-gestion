import streamlit as st

# Définissez ici le code d'accès de votre choix
CODE_ACCES_VALIDE = "CDG2026"

def verifier_authentification():
    """Vérifie si l'utilisateur est authentifié. 
    Si ce n'est pas le cas, affiche un écran de connexion sécurisé et stoppe l'exécution."""
    
    if "est_authentifie" not in st.session_state:
        st.session_state["est_authentifie"] = False

    if not st.session_state["est_authentifie"]:
        col_centre = st.columns([1, 2, 1])[1]
        with col_centre:
            st.markdown("<br><br>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown("<h2 style='text-align: center; margin-bottom: 5px;'>🔒 Accès Sécurisé</h2>", unsafe_allow_html=True)
                st.caption("Portail Décisionnel d'Entreprise - Données Confidentielles")
                st.write("")
                
                code_saisi = st.text_input(
                    "Entrez votre code d'accès :", 
                    type="password", 
                    placeholder="Code d'accès...",
                    key="input_code_auth"
                )
                
                col_btn1, col_btn2 = st.columns([1, 1])
                with col_btn1:
                    if st.button("Valider ➔", use_container_width=True, type="primary"):
                        if code_saisi == CODE_ACCES_VALIDE:
                            st.session_state["est_authentifie"] = True
                            st.rerun()
                        else:
                            st.error("❌ Code incorrect. Veuillez réessayer.")
                
                st.caption("🔑 Mot de passe par défaut : `CDG2026`")
        
        st.stop()

def afficher_bouton_deconnexion():
    """Ajoute un bouton de déconnexion dans la barre latérale une fois connecté."""
    with st.sidebar:
        st.divider()
        if st.button("🚪 Se déconnecter", use_container_width=True):
            st.session_state["est_authentifie"] = False
            st.rerun()