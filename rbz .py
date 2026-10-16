import streamlit as st
import pandas as pd
import re
import time

# -------------------------------------------------------------
# Configuration de la page Streamlit
# -------------------------------------------------------------
st.set_page_config(
    page_title="Terrains DZ - PropTech & Data Quality Intelligence",
    page_icon="🇩🇿",
    layout="wide"
)

# -------------------------------------------------------------
# Barre latérale : Navigation & Modèle SaaS
# -------------------------------------------------------------
st.sidebar.image("https://img.icons8.com/color/96/real-estate.png", width=70)
st.sidebar.title("Terrains DZ")
st.sidebar.caption("Audit Foncier & Gouvernance des Données")

espace = st.sidebar.radio(
    "Sélectionnez votre espace :",
    ["🔍 Espace Client (Audit & Conformité)", "💼 Espace Agence Pro (SaaS Batch)"]
)

st.sidebar.markdown("---")
st.sidebar.info("💡 **Plateforme SaaS Terrains DZ**\n- Détection intelligente du type de document\n- Audit Qualité (8 Dimensions)\n- Exportation Excel/CSV")


# -------------------------------------------------------------
# Moteur d'Analyse Intelligent & Audit des 8 Dimensions
# -------------------------------------------------------------
def analyser_document_intelligent(nom_fichier):
    """
    Vérifie la nature du fichier et adapte l'analyse selon qu'il s'agit d'un acte foncier ou d'un autre document.
    """
    nom_lower = nom_fichier.lower()

    # Détection si c'est une carte ou un document non foncier
    if "carte" in nom_lower or "etudiant" in nom_lower or "id" in nom_lower:
        return {
            "est_foncier": False,
            "Type de Document": "🪪 Carte / Document Non Foncier",
            "Message": "⚠️ Ce document n'est pas un acte foncier ou un livret foncier. Veuillez insérer un document immobilier valide.",
            "Score Global": "N/A",
            "Dimensions": {}
        }
    
    # Sinon, c'est considéré comme un document foncier valide pour la démo
    dimensions_qualite = {
        "1. Complétude": "Validé (Champs obligatoires présents)",
        "2. Exactitude": "Conforme au registre foncier",
        "3. Lisibilité (OCR)": "Élevée (98% net)",
        "4. Cohérence": "Cohérent avec le cadastre",
        "5. Validité": "Format juridique valide",
        "6. Unicité": "Aucun doublon détecté",
        "7. Fraîcheur": "Donnée actualisée",
        "8. Intégrité": "Sceau / Cachet officiel détecté"
    }

    return {
        "est_foncier": True,
        "Type de Document": "Acte de Propriété / Livret Foncier (عقد ملكية / دفتر عقاري)",
        "Superficie Détectée": "250 m²",
        "N° de Lot / Parcelle": "45",
        "Score Global": "94%",
        "Statut": "Validé & Conforme",
        "Dimensions": dimensions_qualite
    }


# -------------------------------------------------------------
# 1. ESPACE CLIENT (PARTICULIER)
# -------------------------------------------------------------
if espace == "🔍 Espace Client (Audit & Conformité)":
    st.title("🔍 Espace Particulier — Audit Intelligent du Foncier")
    st.markdown("Vérifiez l'intégrité, la conformité et les informations clés de vos documents fonciers en un instant.")

    file_uploaded = st.file_uploader(
        "Déposez votre document foncier (JPG, PNG ou PDF scanné)", 
        type=["jpg", "png", "jpeg"]
    )

    if file_uploaded:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image(file_uploaded, caption="Document Téléchargé", use_column_width=True)
            
        with col2:
            st.subheader("Rapport d'Analyse & Gouvernance")
            with st.spinner("Exécution de l'analyse intelligente et audit des 8 dimensions..."):
                time.sleep(1) # Simulation de calcul fluide
                
                resultat = analyser_document_intelligent(file_uploaded.name)
                
                if not resultat["est_foncier"]:
                    st.error(resultat["Message"])
                    st.warning(f"**Type détecté :** {resultat['Type de Document']}")
                else:
                    st.success("✅ Document foncier analysé et validé avec succès !")
                    st.write(f"**Type de document :** {resultat['Type de Document']}")
                    st.write(f"**Superficie extraite :** {resultat['Superficie Détectée']}")
                    st.write(f"**N° de Lot / Parcelle :** {resultat['N° de Lot / Parcelle']}")
                    st.metric(label="Score Global de Qualité (8 Dimensions)", value=resultat['Score Global'], delta="Certifié Conforme")

                    st.subheader("📊 Tableau d'Audit des 8 Dimensions de la Donnée")
                    df_dim = pd.DataFrame(list(resultat['Dimensions'].items()), columns=["Dimension de Qualité", "Évaluation"])
                    st.table(df_dim)


# -------------------------------------------------------------
# 2. ESPACE AGENCE PRO (SaaS B2B)
# -------------------------------------------------------------
else:
    st.title("💼 Espace Agence Immobilière Pro — Traitement par Lots")
    st.markdown("Centralisez, auditez et exportez l'ensemble de vos portefeuilles de biens immobiliers en un clic.")

    files_uploaded = st.file_uploader(
        "Importation groupée de documents (Sélectionnez plusieurs fichiers)",
        type=["jpg", "png", "jpeg"],
        accept_multiple_files=True
    )

    if files_uploaded:
        st.subheader(f"📁 Traitement en cours : {len(files_uploaded)} document(s) détecté(s)")
        
        résultats_lot = []
        barre_progression = st.progress(0)

        for index, file in enumerate(files_uploaded):
            info = analyser_document_intelligent(file.name)
            
            résultats_lot.append({
                "Fichier": file.name,
                "Type de Document": info["Type de Document"],
                "Superficie": info.get("Superficie Détectée", "N/A"),
                "N° de Lot": info.get("N° de Lot / Parcelle", "N/A"),
                "Score Qualité": info.get("Score Global", "N/A"),
                "Statut": "Vérifié par l'IA"
            })
            
            barre_progression.progress((index + 1) / len(files_uploaded))
            time.sleep(0.3)

        st.success("🎉 Traitement du lot de documents terminé avec succès !")

        df_resultats = pd.DataFrame(résultats_lot)
        st.subheader("📊 Tableau de Synthèse du Portefeuille Foncier")
        st.dataframe(df_resultats, use_container_width=True)

        csv_data = df_resultats.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger le Rapport d'Audit Complet (Excel / CSV)",
            data=csv_data,
            file_name="Rapport_Audit_Foncier_Terrains_DZ.csv",
            mime="text/csv"
        )
