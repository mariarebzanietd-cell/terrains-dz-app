import streamlit as st
import pandas as pd
import re
import time

# -------------------------------------------------------------
# Configuration de la page Streamlit
# -------------------------------------------------------------
st.set_page_config(
    page_title="Terrains DZ - Solution PropTech Foncère",
    page_icon="🇩🇿",
    layout="wide"
)

# -------------------------------------------------------------
# Barre latérale : Navigation & Modèle SaaS
# -------------------------------------------------------------
st.sidebar.image("https://img.icons8.com/color/96/real-estate.png", width=70)
st.sidebar.title("Terrains DZ")
st.sidebar.caption("Numérisation & Validation Foncère Intelligente")

espace = st.sidebar.radio(
    "Sélectionnez votre espace :",
    ["🔍 Espace Client (Particulier)", "💼 Espace Agence Pro (SaaS)"]
)

st.sidebar.markdown("---")
st.sidebar.info("💡 **Abonnement SaaS Agence**\n- Analyse par lots illimitée\n- Exportation Excel/CSV\n- Score Qualité (8 Dimensions)")


# -------------------------------------------------------------
# Fonction d'extraction automatique (Simulateur Regex + OCR)
# -------------------------------------------------------------
def extraire_donnees_foncieres(nom_fichier, texte_simule):
    """
    Utilise Regex pour extraire les informations clés du texte (Arabe / Français).
    """
    # Recherche de la superficie (ex: 250 m2, 250m², 250 مساحة)
    superficie_match = re.search(r'(\d+\s*(m2|m²|mètres carrés|م2|متر مربع))', texte_simule, re.IGNORECASE)
    superficie = superficie_match.group(0) if superficie_match else "Non détectée"

    # Recherche du numéro de lot ou de parcelle
    lot_match = re.search(r'(lot|parcelle|قطعة|رقم)\s*[:№#]?\s*(\d+)', texte_simule, re.IGNORECASE)
    num_lot = lot_match.group(2) if lot_match else "Non renseigné"

    # Type de document détecté
    if "livret" in texte_simule.lower() or "دفتر" in texte_simule:
        type_doc = "Livret Foncier (دفتر عقاري)"
    elif "acte" in texte_simule.lower() or "عقد" in texte_simule:
        type_doc = "Acte de Propriété (عقد ملكية)"
    else:
        type_doc = "Document Administratif"

    return {
        "Fichier": nom_fichier,
        "Type de Document": type_doc,
        "Superficie Détectée": superficie,
        "N° de Lot / Parcelle": num_lot,
        "Score Conformité": "95% (Conforme)",
        "Statut OCR": "Traité avec succès"
    }


# -------------------------------------------------------------
# 1. ESPACE CLIENT (PARTICULIER)
# -------------------------------------------------------------
if espace == "🔍 Espace Client (Particulier)":
    st.title("🔍 Espace Particulier — Vérification Foncère")
    st.markdown("Vérifiez rapidement la lisibilité et la conformité de votre acte de propriété ou livret foncier.")

    file_uploaded = st.file_uploader(
        "Déposez votre document foncier (JPG, PNG ou PDF scanné)", 
        type=["jpg", "png", "jpeg"]
    )

    if file_uploaded:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image(file_uploaded, caption="Document Téléchargé", use_column_width=True)
            
        with col2:
            st.subheader("Analyse de conformité instantanée")
            with st.spinner("Analyse OCR et vérification des 8 dimensions de qualité..."):
                time.sleep(1) # Simulation du temps de calcul
                
                # Simulation de texte extrait par OCR
                texte_extrait_ocr = "Acte de propriété rédigé à Koléa, parcelle lot #45 de superficie 250 m2."
                resultat = extraire_donnees_foncieres(file_uploaded.name, texte_extrait_ocr)
                
                st.success("✅ Document lisible et conforme !")
                st.write(f"**Type de document :** {resultat['Type de Document']}")
                st.write(f"**Superficie extraite :** {resultat['Superficie Détectée']}")
                st.write(f"**N° de Lot :** {resultat['N° de Lot / Parcelle']}")
                st.metric(label="Qualité globale du document", value="95%", delta="Très Élevée")


# -------------------------------------------------------------
# 2. ESPACE AGENCE PRO (SaaS B2B)
# -------------------------------------------------------------
else:
    st.title("💼 Espace Agence Immobilière Pro — Traitement par Lots")
    st.markdown("Centralisez, numérisez et exportez l'ensemble de vos dossiers clients en un clic.")

    files_uploaded = st.file_uploader(
        "Importation groupée de documents (Sélectionnez plusieurs fichiers)",
        type=["jpg", "png", "jpeg"],
        accept_multiple_files=True
    )

    if files_uploaded:
        st.subheader(f"📁 Traitement en cours : {len(files_uploaded)} document(s) détecté(s)")
        
        résultats_lot = []
        barre_progression = st.progress(0)

        # 🔄 UTILISATION D'UNE BOUCLE FOR POUR LE TRAITEMENT PAR LOT
        for index, file in enumerate(files_uploaded):
            # Simulation d'un texte extrait par l'OCR pour chaque document du lot
            texte_factice = f"Document foncier concernant le lot #{100 + index} d'une superficie de {180 + index * 20} m2 - دفتر عقاري."
            
            # Extraction des données
            info = extraire_donnees_foncieres(file.name, texte_factice)
            résultats_lot.append(info)
            
            # Mise à jour de la barre de progression
            barre_progression.progress((index + 1) / len(files_uploaded))
            time.sleep(0.3)

        st.success("🎉 Traitement du lot terminé avec succès !")

        # Transformation des résultats en DataFrame Pandas
        df_resultats = pd.DataFrame(résultats_lot)

        # Affichage du tableau de bord
        st.subheader("📊 Tableau de Synthèse du Portefeuille")
        st.dataframe(df_resultats, use_container_width=True)

        # Bouton d'exportation Excel/CSV pour l'Agence
        csv_data = df_resultats.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger le Rapport Excel / CSV pour l'Agence",
            data=csv_data,
            file_name="Rapport_Foncier_Terrains_DZ.csv",
            mime="text/csv"
        )
