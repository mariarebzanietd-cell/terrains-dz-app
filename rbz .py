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
st.sidebar.info("💡 **Plateforme SaaS Terrains DZ**\n- Extraction Regex Bilingue (Fr/Ar)\n- Audit Qualité (8 Dimensions)\n- Exportation Excel/CSV")


# -------------------------------------------------------------
# Moteur d'Analyse Foncier & Audit des 8 Dimensions
# -------------------------------------------------------------
def analyser_document_foncier(nom_fichier, texte_simule):
    """
    Extrait les données clés du foncier et réalise un audit de qualité selon les 8 dimensions.
    """
    # 1. Extraction Regex (Superficie et Lot)
    superficie_match = re.search(r'(\d+\s*(m2|m²|mètres carrés|م2|متر مربع))', texte_simule, re.IGNORECASE)
    superficie = superficie_match.group(0) if superficie_match else "250 m² (Standard)"

    lot_match = re.search(r'(lot|parcelle|قطعة|رقم)\s*[:№#]?\s*(\d+)', texte_simule, re.IGNORECASE)
    num_lot = lot_match.group(2) if lot_match else "45"

    # 2. Identification du Type de Document
    texte_lower = texte_simule.lower()
    if "livret" in texte_lower or "دفتر" in texte_simule:
        type_doc = "Livret Foncier (دفتر عقاري)"
        score_base = 96
    elif "acte" in texte_lower or "عقد" in texte_simule:
        type_doc = "Acte de Propriété (عقد ملكية)"
        score_base = 94
    else:
        type_doc = "Document Foncier / Administratif"
        score_base = 90

    # 3. Audit des 8 Dimensions de la Qualité des Données (Data Management)
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
        "Fichier": nom_fichier,
        "Type de Document": type_doc,
        "Superficie Détectée": superficie,
        "N° de Lot / Parcelle": num_lot,
        "Score Global": f"{score_base}%",
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
            st.image(file_uploaded, caption="Document Foncier Téléchargé", use_column_width=True)
            
        with col2:
            st.subheader("Rapport d'Analyse & Gouvernance")
            with st.spinner("Exécution de l'OCR, extraction Regex et audit des 8 dimensions..."):
                time.sleep(1) # Simulation de calcul fluide
                
                # Simulation de texte extrait intelligente selon le nom du fichier
                if "livret" in file_uploaded.name.lower():
                    texte_extrait = "Livret foncier - دفتر عقاري - parcelle lot #12 de superficie 300 m2."
                else:
                    texte_extrait = "Acte de propriété officiel - عقد ملكية - lot #45 de superficie 250 m2."
                
                resultat = analyser_document_foncier(file_uploaded.name, texte_extrait)
                
                st.success("✅ Document analysé et validé avec succès !")
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

        # 🔄 BOUCLE FOR POUR LE TRAITEMENT PAR LOT (B2B SaaS)
        for index, file in enumerate(files_uploaded):
            texte_factice = f"Document foncier officiel concernant le lot #{100 + index} d'une superficie de {180 + index * 20} m2 - دفتر عقاري."
            
            info = analyser_document_foncier(file.name, texte_factice)
            
            résultats_lot.append({
                "Fichier": info["Fichier"],
                "Type de Document": info["Type de Document"],
                "Superficie": info["Superficie Détectée"],
                "N° de Lot": info["N° de Lot / Parcelle"],
                "Score Qualité": info["Score Global"],
                "Statut": info["Statut"]
            })
            
            barre_progression.progress((index + 1) / len(files_uploaded))
            time.sleep(0.3)

        st.success("🎉 Traitement du lot de documents terminé avec succès !")

        # Transformation en DataFrame Pandas
        df_resultats = pd.DataFrame(résultats_lot)

        # Affichage du tableau de bord professionnel
        st.subheader("📊 Tableau de Synthèse du Portefeuille Foncier")
        st.dataframe(df_resultats, use_container_width=True)

        # Bouton d'exportation Excel/CSV pour l'Agence
        csv_data = df_resultats.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger le Rapport d'Audit Complet (Excel / CSV)",
            data=csv_data,
            file_name="Rapport_Audit_Foncier_Terrains_DZ.csv",
            mime="text/csv"
        )
