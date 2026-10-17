import streamlit as st
import pandas as pd
import time
import re
import PyPDF2
from PIL import Image
import pytesseract
import io

# --- NOUVEAUX IMPORTS NLP ---
import spacy
from langdetect import detect, DetectorFactory

# Pour que langdetect soit toujours stable
DetectorFactory.seed = 0

# -------------------------------------------------------------
# CHARGEMENT DU MODÈLE NLP (Mis en cache pour ne pas ralentir l'app)
# -------------------------------------------------------------
@st.cache_resource
def charger_modele_nlp():
    try:
        # Chargement du modèle français de spaCy
        nlp = spacy.load("fr_core_news_sm")
        return nlp
    except Exception as e:
        st.error(f"Erreur de chargement du modèle NLP : {e}")
        return None

nlp = charger_modele_nlp()

# -------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------
st.set_page_config(page_title="Terrains DZ - Scanner Intelligent", page_icon="🇩🇿", layout="wide")

# -------------------------------------------------------------
# FONCTION OCR (Lecture de fichier)
# -------------------------------------------------------------
def extraire_texte(fichier):
    texte = ""
    if fichier.type == "application/pdf":
        pdf_reader = PyPDF2.PdfReader(fichier)
        for page in pdf_reader.pages:
            texte += page.extract_text() + "\n"
    elif fichier.type in ["image/jpeg", "image/png", "image/jpg"]:
        image = Image.open(fichier)
        texte = pytesseract.image_to_string(image, lang='fra')
    return texte

# -------------------------------------------------------------
# FONCTION NLP & ML (Analyse intelligente)
# -------------------------------------------------------------
def analyser_avec_nlp(texte, nom_fichier, taille_ko):
    resultats = {
        "Nom du fichier": nom_fichier,
        "Taille (Ko)": taille_ko,
        "Langue détectée": "Inconnue",
        "Type de document": "📄 Document Général",
        "Noms (Personnes)": "Aucun",
        "Dates trouvées": "Aucune",
        "Montants (DZD)": "Aucun",
        "Organisations": "Aucune",
        "Synthèse NLP": "Aucune analyse disponible."
    }

    if not texte.strip():
        return resultats

    # 1. Détection de la langue (NLP de base)
    try:
        langue = detect(texte)
        langues_noms = {'fr': 'Français', 'ar': 'Arabe', 'en': 'Anglais'}
        resultats["Langue détectée"] = langues_noms.get(langue, langue)
    except:
        pass

    # 2. Analyse avec spaCy (Machine Learning / NLP)
    if nlp:
        doc = nlp(texte)
        
        # Extraction des entités nommées (NER)
        noms = [ent.text for ent in doc.ents if ent.label_ == "PER"]
        dates = [ent.text for ent in doc.ents if ent.label_ == "DATE"]
        montants = [ent.text for ent in doc.ents if ent.label_ == "MONEY"]
        organisations = [ent.text for ent in doc.ents if ent.label_ == "ORG"]

        # Nettoyage et formatage
        resultats["Noms (Personnes)"] = ", ".join(list(set(noms))[:5]) if noms else "Aucun"
        resultats["Dates trouvées"] = ", ".join(list(set(dates))[:5]) if dates else "Aucune"
        resultats["Montants (DZD)"] = ", ".join(list(set(montants))[:5]) if montants else "Aucun"
        resultats["Organisations"] = ", ".join(list(set(organisations))[:5]) if organisations else "Aucune"

        # 3. Classification ML (Simulée par des règles NLP avancées)
        texte_lower = texte.lower()
        if "acte" in texte_lower or "foncier" in texte_lower or "parcelle" in texte_lower:
            resultats["Type de document"] = "🏠 Document Foncier / Immobilier"
            resultats["Synthèse NLP"] = "Termes immobiliers et cadastraux détectés par le modèle."
        elif "facture" in texte_lower or "montant" in texte_lower or "dinars" in texte_lower:
            resultats["Type de document"] = "🧾 Document Financier"
            resultats["Synthèse NLP"] = "Structure financière et montants détectés."
        elif "carte" in texte_lower or "étudiant" in texte_lower:
            resultats["Type de document"] = "🎓 Document Académique"
            resultats["Synthèse NLP"] = "Vocabulaire académique identifié."
        else:
            resultats["Synthèse NLP"] = "Analyse NLP terminée. Aucun motif spécifique fort détecté."

    return resultats

# -------------------------------------------------------------
# BARRE LATÉRALE
# -------------------------------------------------------------
st.sidebar.image("https://img.icons8.com/color/96/real-estate.png", width=70)
st.sidebar.title("Terrains DZ")
st.sidebar.caption("Scanner & Audit Intelligent (NLP Activé)")

espace = st.sidebar.radio(
    "Sélectionnez votre espace :",
    ["🔍 Scanner & Analyseur Universel", "💼 Espace Agence Pro (SaaS Batch)"]
)

# -------------------------------------------------------------
# 1. ESPACE SCANNER
# -------------------------------------------------------------
if espace == "🔍 Scanner & Analyseur Universel":
    st.title("🔍 Scanner Universel de Documents (IA & NLP)")
    st.markdown("Importez un document (PDF, Image). L'IA lit le texte, détecte la langue et extrait les entités (Noms, Dates, Montants).")

    file_uploaded = st.file_uploader("Déposez votre document ici", type=["pdf", "jpg", "png", "jpeg"])

    if file_uploaded:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if file_uploaded.type == "application/pdf":
                st.info("📄 Fichier PDF chargé")
            else:
                st.image(file_uploaded, caption=f"Fichier : {file_uploaded.name}", use_column_width=True)
            
        with col2:
            st.subheader("Rapport d'Analyse NLP")
            with st.spinner("Extraction du texte et analyse NLP en cours..."):
                time.sleep(1)
                
                texte_extrait = extraire_texte(file_uploaded)
                taille_Ko = round(file_uploaded.size / 1024, 1)
                
                # Appel de la nouvelle fonction NLP
                resultats = analyser_avec_nlp(texte_extrait, file_uploaded.name, taille_Ko)
                
                st.success("✅ Analyse NLP terminée avec succès !")
                
                # Affichage des résultats dans un tableau
                st.subheader("📊 Résultats de l'Extraction Intelligente")
                df_resultats = pd.DataFrame(list(resultats.items()), columns=["Critère", "Valeur Extraite"])
                st.table(df_resultats)
                
                # Texte brut
                with st.expander("📝 Voir le texte brut extrait du document"):
                    st.text_area("Contenu extrait :", texte_extrait, height=200)

# -------------------------------------------------------------
# 2. ESPACE AGENCE PRO
# -------------------------------------------------------------
else:
    st.title("💼 Espace Agence Pro — Traitement par Lots")
    st.markdown("Importez plusieurs documents en même temps pour un audit global.")

    files_uploaded = st.file_uploader("Importation groupée", type=["pdf", "jpg", "png", "jpeg"], accept_multiple_files=True)

    if files_uploaded:
        st.subheader(f"📁 Traitement en cours : {len(files_uploaded)} document(s)")
        
        résultats_lot = []
        barre_progression = st.progress(0)

        for index, file in enumerate(files_uploaded):
            texte = extraire_texte(file)
            taille = round(file.size / 1024, 1)
            
            # On réutilise notre fonction NLP pour chaque fichier
            res = analyser_avec_nlp(texte, file.name, taille)
            
            résultats_lot.append({
                "Fichier": file.name,
                "Langue": res["Langue détectée"],
                "Type détecté": res["Type de document"],
                "Noms": res["Noms (Personnes)"],
                "Statut": "Analysé par NLP"
            })
            barre_progression.progress((index + 1) / len(files_uploaded))
            time.sleep(0.2)

        st.success("🎉 Traitement NLP du lot terminé !")

        df_resultats = pd.DataFrame(résultats_lot)
        st.dataframe(df_resultats, use_container_width=True)

        csv_data = df_resultats.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger le Rapport Global (CSV)",
            data=csv_data,
            file_name="Rapport_NLP_Terrains_DZ.csv",
            mime="text/csv"
        )
