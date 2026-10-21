app.py (point d'entrée)
"""Terrains DZ — Recherche de terrains, scanner intelligent et espace agence.

Lancement : python -m streamlit run app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

RACINE = Path(__file__).resolve().parent
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

import catalogue  # noqa: E402

st.set_page_config(
    page_title="Terrains DZ — Recherche & Scanner",
    page_icon="🏞️",
    layout="wide",
)

catalogue.init_db()
catalogue.semer_annonces()

with st.sidebar:
    st.image("https://img.icons8.com/color/96/real-estate.png", width=64)
    st.markdown("### Terrains DZ")
    st.caption("Recherche, scanner intelligent & audit")

navigation = st.navigation([
    st.Page("app_pages/recherche.py", title="Recherche de terrains",
            icon=":material/search:", default=True),
    st.Page("app_pages/scanner.py", title="Scanner intelligent (NLP)",
            icon=":material/document_scanner:"),
    st.Page("app_pages/agence.py", title="Espace agence pro",
            icon=":material/business:"),
])
navigation.run()
app_pages/recherche.py (le client cherche son besoin)
"""Espace client : recherche d'un terrain (type, wilaya, ville)."""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

RACINE = Path(__file__).resolve().parent.parent
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

import catalogue  # noqa: E402
import data_communes as dc  # noqa: E402
import helpers  # noqa: E402

helpers.init_state()

st.title("Rechercher un terrain")
st.markdown(
    "Filtrez par **type de terrain**, **wilaya** et **ville** : "
    "les communes de chaque wilaya sont disponibles dans le menu déroulant."
)

annonces = helpers.charger_annonces()
if not annonces:
    st.warning("Aucune annonce publiée pour le moment.")
    st.stop()

# --- 1. Type de terrain (sélection multiple) --------------------------------
st.subheader("1. Quel type de terrain recherchez-vous ?")
version = st.session_state["filtre_version"]
types = st.pills(
    "Type de terrain",
    catalogue.TYPES_TERRAIN,
    selection_mode="multi",
    key=f"filtre_types_{version}",
    label_visibility="collapsed",
)

# --- Filtres complémentaires (barre latérale) -------------------------------
with st.sidebar:
    st.header("Filtres de recherche")
    wilayas = dc.wilayas()
    libelles = ["Toutes les wilayas"] + [f"{nom} ({code})" for code, nom in wilayas]
    choix_wilaya = st.selectbox("Wilaya", libelles, key=f"filtre_wilaya_{version}",
        help="Les communes se mettent à jour automatiquement selon la wilaya choisie.")
    code_wilaya = nom_wilaya = None
    if choix_wilaya != "Toutes les wilayas":
        code_wilaya = choix_wilaya.split("(")[-1].replace(")", "")
        nom_wilaya = dc.nom_wilaya(code_wilaya)

    communes = dc.communes(code_wilaya)
    choix_commune = st.selectbox("Ville / commune",
        ["Toutes les communes"] + communes,
        key=f"filtre_commune_{code_wilaya or 'all'}_{version}")
    commune = None if choix_commune == "Toutes les communes" else choix_commune

    mot_cle = st.text_input("Mot-clé (quartier, référence foncière…)",
        key=f"filtre_mot_cle_{version}", placeholder="Ex: bord de mer, LF-42/10432")
    budget_max = st.number_input("Budget maximum (DZD)", min_value=0, value=0,
        step=500_000, key=f"filtre_budget_{version}", help="0 = pas de limite de budget.")
    superficie_min = st.number_input("Superficie minimale (m²)", min_value=0, value=0,
        step=100, key=f"filtre_surface_{version}", help="0 = pas de minimum.")
    tri = st.selectbox("Trier par",
        ["Pertinence (plus récent)", "Prix croissant", "Prix décroissant",
         "Superficie décroissante", "Wilaya puis commune"], key=f"filtre_tri_{version}")
    if st.button("Réinitialiser les filtres", width="stretch"):
        st.session_state["filtre_version"] = version + 1
        st.rerun()

criteres = {
    "types": types or [], "wilaya": nom_wilaya, "commune": commune,
    "mot_cle": mot_cle, "budget_max": budget_max or None,
    "superficie_min": superficie_min or None, "tri": tri,
}
resultats = helpers.filtrer_annonces(annonces, criteres)

# --- 2. Résultats -----------------------------------------------------------
st.subheader("2. Terrains correspondants")
if not resultats:
    st.info("Aucun terrain ne correspond à ces critères. Élargissez votre recherche "
            "ou enregistrez votre besoin : l'agence vous contactera.")
else:
    prix = [a["prix_dzd"] for a in resultats if a.get("prix_dzd")]
    surfaces = [a["superficie_m2"] for a in resultats if a.get("superficie_m2")]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Terrains trouvés", len(resultats))
    c2.metric("Prix minimum", helpers.formater_prix(min(prix) if prix else None))
    c3.metric("Prix maximum", helpers.formater_prix(max(prix) if prix else None))
    c4.metric("Superficie moyenne",
        f"{sum(surfaces)/len(surfaces):,.0f} m²".replace(",", " ") if surfaces else "—")

for index, annonce in enumerate(resultats):
    with st.container(border=True):
        gauche, droite = st.columns([1, 2])
        with gauche:
            chemin = helpers.image_annonce(annonce)
            if chemin:
                st.image(str(chemin), alt=annonce["titre"], width="stretch")
            else:
                st.markdown("🗺️ *Photo à venir*")
            st.caption(f"Réf. {annonce.get('reference_fonciere') or '—'}")
        with droite:
            st.markdown(f"**{annonce['titre']}**")
            st.caption(f"{annonce['type_terrain']} · {annonce.get('commune','')} "
                       f"({annonce.get('wilaya','')}) · {annonce.get('statut','')}")
            st.markdown(f"💰 **{helpers.formater_prix(annonce.get('prix_dzd'))}**")
            st.markdown(f"📐 {helpers.formater_surface(annonce.get('superficie_m2'))}")
            if annonce.get("description"):
                st.caption(annonce["description"])
            st.markdown(f"📞 {annonce.get('telephone') or 'Contact sur demande'}")
            if st.button("Je suis intéressé", key=f"interesse_{annonce['id']}_{index}",
                type="primary" if st.session_state["annonce_selection"] == annonce["id"]
                        else "secondary"):
                st.session_state["annonce_selection"] = annonce["id"]
                st.session_state["demande_type"] = annonce["type_terrain"]
                st.session_state["demande_wilaya"] = annonce.get("wilaya", "")
                st.session_state[f"demande_commune_{annonce.get('wilaya','')}"] = \
                    annonce.get("commune", "")
                st.session_state["demande_budget"] = annonce.get("prix_dzd") or 0
                st.session_state["demande_surface"] = annonce.get("superficie_m2") or 0

if resultats:
    with st.expander("🗺️ Voir les résultats sur la carte"):
        helpers.afficher_carte(resultats)

# --- 3. Expression du besoin ------------------------------------------------
st.subheader("3. Vous ne trouvez pas votre terrain ? Décrivez votre besoin")

liste_wilayas = dc.wilayas()
colonne_wilaya, colonne_info = st.columns([1, 2])
wilaya = colonne_wilaya.selectbox("Wilaya souhaitée",
    ["(toutes)"] + [nom for _, nom in liste_wilayas], key="demande_wilaya")
code_wilaya = next((c for c, n in liste_wilayas if n == wilaya), None)
communes_demande = dc.communes(code_wilaya)
with colonne_info:
    st.caption(f"{len(communes_demande)} communes disponibles dans la wilaya {wilaya}. "
               "Choisissez une ville pour affiner la recherche.")

with st.form("formulaire_demande", clear_on_submit=False):
    c1, c2, c3 = st.columns(3)
    nom = c1.text_input("Nom et prénom", key="demande_nom")
    telephone = c2.text_input("Téléphone", key="demande_tel")
    email = c3.text_input("E-mail", key="demande_email")

    c1, c2 = st.columns(2)
    type_terrain = c1.selectbox("Type de terrain recherché",
        ["(indifférent)"] + catalogue.TYPES_TERRAIN, key="demande_type")
    commune = c2.selectbox("Ville / commune souhaitée",
        ["(toutes)"] + communes_demande, key=f"demande_commune_{wilaya}")

    c1, c2 = st.columns(2)
    budget = c1.number_input("Budget maximum (DZD)", min_value=0, step=500_000,
        key="demande_budget")
    surface = c2.number_input("Superficie minimale (m²)", min_value=0, step=100,
        key="demande_surface")

    notes = st.text_area("Précisions (orientation, accès, délai de location…)",
        key="demande_notes",
        placeholder="Ex: terrain plat, à 500 m de la plage, titres en ordre…")

    if st.form_submit_button("Enregistrer ma demande", type="primary"):
        if not telephone and not email:
            st.error("Renseignez au moins un téléphone ou un e-mail.")
        else:
            besoin = {
                "nom": nom, "telephone": telephone, "email": email,
                "type_terrain": "" if type_terrain == "(indifférent)" else type_terrain,
                "wilaya": "" if wilaya == "(toutes)" else wilaya,
                "commune": "" if commune == "(toutes)" else commune,
                "budget_max": budget or None, "superficie_min": surface or None,
                "notes": notes,
            }
            identifiant = catalogue.enregistrer_demande(besoin)
            st.session_state["demande_envoyee"] = identifiant
            st.success(f"Demande n° {identifiant} enregistrée : l'agence vous recontacte "
                       "rapidement.")
            suggestions = catalogue.correspondances(besoin, helpers.charger_annonces())
            if suggestions:
                st.markdown("**Terrains du catalogue correspondant à votre besoin :**")
                for s in suggestions[:5]:
                    st.markdown(f"- {s['titre']} — {s['commune']} ({s['wilaya']}) — "
                                f"{helpers.formater_prix(s['prix_dzd'])}")
app_pages/scanner.py (ton code NLP/OCR, conservé)
"""Scanner intelligent : OCR + NLP."""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

RACINE = Path(__file__).resolve().parent.parent
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

import catalogue  # noqa: E402
import data_communes as dc  # noqa: E402
import helpers  # noqa: E402
import nlp_scanner  # noqa: E402

helpers.init_state()

st.title("Scanner intelligent de documents")
st.markdown("Importez un document (PDF ou image) : l'IA lit le texte, détecte la langue "
            "et extrait les entités (noms, dates, montants).")

manquantes = nlp_scanner.dependances_manquantes()
if manquantes:
    st.info("Fonctionnalités optionnelles absentes : " + ", ".join(manquantes) +
            ". Installation : `pip install pypdf pytesseract langdetect spacy` puis "
            "`python -m spacy download fr_core_news_sm`.")

fichier = st.file_uploader("Déposez votre document ici",
    type=["pdf", "jpg", "png", "jpeg"], key="scan_fichier")
if not fichier:
    st.stop()

col1, col2 = st.columns([1, 2])
with col1:
    if fichier.type == "application/pdf":
        st.info("📄 Fichier PDF chargé")
    else:
        st.image(fichier, alt=f"Fichier {fichier.name}", width="stretch")
with col2:
    st.subheader("Rapport d'analyse NLP")
    with st.spinner("Extraction du texte et analyse NLP en cours…"):
        texte_extrait = nlp_scanner.extraire_texte(fichier)
        resultats = nlp_scanner.analyser_avec_nlp(texte_extrait, fichier.name,
                                                  round(fichier.size / 1024, 1))
        st.session_state["scan_resultat"] = {"texte": texte_extrait, "resultats": resultats}
    if not texte_extrait.strip():
        st.warning("Aucun texte exploitable n'a pu être extrait (PDF scanné sans OCR ?).")
    else:
        st.success("✅ Analyse NLP terminée avec succès !")
    st.subheader("📊 Résultats de l'extraction intelligente")
    st.dataframe(pd.DataFrame(list(resultats.items()),
        columns=["Critère", "Valeur extraite"]), width="stretch", hide_index=True)
    with st.expander("📝 Voir le texte brut extrait du document"):
        st.text_area("Contenu extrait", texte_extrait, height=220, disabled=True)

# --- Publication directe dans le catalogue ----------------------------------
prix, surface = nlp_scanner.extraire_prix_surface(texte_extrait)
st.subheader("📝 Créer une annonce à partir du document")

liste_wilayas = dc.wilayas()
noms_wilaya = [nom for _, nom in liste_wilayas]
c1, c2 = st.columns(2)
wilaya = c1.selectbox("Wilaya", noms_wilaya,
    index=noms_wilaya.index("Tipaza") if "Tipaza" in noms_wilaya else 0, key="scan_wilaya")
communes = dc.communes(next((c for c, n in liste_wilayas if n == wilaya), None))
commune = c2.selectbox("Ville / commune", communes, key="scan_commune")

with st.form("form_annonce_scanner", clear_on_submit=False):
    c1, c2 = st.columns(2)
    titre = c1.text_input("Titre de l'annonce", value=f"Terrain - {fichier.name}")
    type_terrain = c2.selectbox("Type de terrain", catalogue.TYPES_TERRAIN)
    c1, c2, c3 = st.columns(3)
    superficie = c1.number_input("Superficie (m²)", min_value=0, value=int(surface or 0), step=50)
    prix_saisi = c2.number_input("Prix (DZD)", min_value=0, value=int(prix or 0), step=100_000)
    telephone = c3.text_input("Téléphone")
    reference = st.text_input("Référence foncière")
    description = st.text_area("Description", value=texte_extrait[:500])
    if st.form_submit_button("Publier dans le catalogue", type="primary"):
        identifiant = f"TER-{wilaya[:3].upper()}-{datetime.now().strftime('%H%M%S')}"
        catalogue.ajouter_annonce({
            "id": identifiant, "titre": titre, "type_terrain": type_terrain,
            "wilaya_code": next((c for c, n in liste_wilayas if n == wilaya), ""),
            "wilaya": wilaya, "commune": commune, "superficie_m2": superficie or None,
            "prix_dzd": prix_saisi or None, "statut": "Disponible",
            "reference_fonciere": reference, "description": description, "image": "",
            "latitude": None, "longitude": None, "telephone": telephone})
        helpers.invalider_cache_annonces()
        st.success(f"Annonce {identifiant} publiée dans le catalogue.")
app_pages/agence.py
"""Espace agence pro : annonces, demandes clients, audit par lot."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

RACINE = Path(__file__).resolve().parent.parent
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

import catalogue  # noqa: E402
import data_communes as dc  # noqa: E402
import helpers  # noqa: E402
import nlp_scanner  # noqa: E402

helpers.init_state()

st.title("Espace agence pro")
st.markdown("Gérez les annonces publiées, traitez les demandes clients et auditez vos documents.")

onglet_annonces, onglet_demandes, onglet_lots = st.tabs(
    ["📋 Annonces", "📥 Demandes clients", "🧠 Analyse par lot (NLP)"])

with onglet_annonces:
    annonces = helpers.charger_annonces()
    if annonces:
        st.dataframe(pd.DataFrame(annonces).drop(columns=["image", "date_creation"]),
                     width="stretch", hide_index=True)
        csv = pd.DataFrame(annonces).drop(columns=["image"]).to_csv(index=False).encode("utf-8")
        st.download_button("Télécharger le catalogue (CSV)", data=csv,
                           file_name="Catalogue_Terrains_DZ.csv", mime="text/csv")
    else:
        st.info("Aucune annonce publiée.")

    with st.expander("➕ Publier une nouvelle annonce"):
        liste_wilayas = dc.wilayas()
        noms_wilaya = [n for _, n in liste_wilayas]
        c1, c2 = st.columns(2)
        wilaya = c1.selectbox("Wilaya", noms_wilaya, key="ag_wilaya")
        communes = dc.communes(next((c for c, n in liste_wilayas if n == wilaya), None))
        commune = c2.selectbox("Ville / commune", communes, key="ag_commune")
        with st.form("form_annonce_agence"):
            c1, c2 = st.columns(2)
            identifiant = c1.text_input("Identifiant (ex: TER-TIP-020)")
            titre = c2.text_input("Titre de l'annonce")
            type_terrain = c1.selectbox("Type de terrain", catalogue.TYPES_TERRAIN, key="ag_type")
            statut = c2.selectbox("Statut", catalogue.STATUTS, key="ag_statut")
            c1, c2, c3 = st.columns(3)
            superficie = c1.number_input("Superficie (m²)", min_value=0, step=50, key="ag_surface")
            prix = c2.number_input("Prix (DZD)", min_value=0, step=100_000, key="ag_prix")
            telephone = c3.text_input("Téléphone", key="ag_tel")
            reference = st.text_input("Référence foncière", key="ag_ref")
            description = st.text_area("Description", key="ag_desc")
            if st.form_submit_button("Publier", type="primary"):
                if not identifiant or not titre:
                    st.error("L'identifiant et le titre sont obligatoires.")
                else:
                    catalogue.ajouter_annonce({
                        "id": identifiant, "titre": titre, "type_terrain": type_terrain,
                        "wilaya_code": next((c for c, n in liste_wilayas if n == wilaya), ""),
                        "wilaya": wilaya, "commune": commune,
                        "superficie_m2": superficie or None, "prix_dzd": prix or None,
                        "statut": statut, "reference_fonciere": reference,
                        "description": description, "image": "", "latitude": None,
                        "longitude": None, "telephone": telephone})
                    helpers.invalider_cache_annonces()
                    st.success(f"Annonce {identifiant} publiée.")

with onglet_demandes:
    demandes = catalogue.lister_demandes()
    if not demandes:
        st.info("Aucune demande enregistrée pour le moment.")
    else:
        for demande in demandes:
            with st.container(border=True):
                st.markdown(f"**Demande n° {demande['id']}** — {demande['date']} "
                            f"· statut : *{demande['statut']}*")
                st.write(f"{demande['nom'] or 'Client anonyme'} · "
                         f"{demande['telephone'] or '—'} · {demande['email'] or '—'}")
                st.write(f"Recherche : {demande['type_terrain'] or 'tous types'} · "
                         f"{demande['commune'] or 'toutes communes'} "
                         f"({demande['wilaya'] or 'toutes wilayas'}) · "
                         f"budget {helpers.formater_prix(demande['budget_max'])} · "
                         f"surface min {helpers.formater_surface(demande['superficie_min'])}")
                if demande["notes"]:
                    st.caption(demande["notes"])
                suggestions = catalogue.correspondances(demande, helpers.charger_annonces())
                if suggestions:
                    st.markdown("**Annonces correspondantes :**")
                    for s in suggestions[:3]:
                        st.markdown(f"- {s['titre']} — {s['commune']} ({s['wilaya']}) — "
                                    f"{helpers.formater_prix(s['prix_dzd'])} — score {s['score']}")
                else:
                    st.caption("Aucune annonce ne correspond encore à cette demande.")
                statuts = ["Nouvelle", "Contactée", "Terrain proposé", "Classée"]
                c1, c2 = st.columns(2)
                nouveau_statut = c1.selectbox("Statut", statuts,
                    index=statuts.index(demande["statut"]) if demande["statut"] in statuts else 0,
                    key=f"statut_{demande['id']}", label_visibility="collapsed")
                if c1.button("Mettre à jour", key=f"maj_{demande['id']}"):
                    catalogue.maj_statut_demande(demande["id"], nouveau_statut)
                    st.rerun()
                if c2.button("Supprimer", key=f"sup_{demande['id']}"):
                    catalogue.supprimer_demande(demande["id"])
                    st.rerun()
        csv = pd.DataFrame(demandes).to_csv(index=False).encode("utf-8")
        st.download_button("Télécharger les demandes (CSV)", data=csv,
                           file_name="Demandes_Clients_Terrains_DZ.csv", mime="text/csv")

with onglet_lots:
    st.markdown("Importez plusieurs documents pour un audit global.")
    if nlp_scanner.dependances_manquantes():
        st.info("L'analyse par lot nécessite les dépendances du scanner.")
    else:
        fichiers = st.file_uploader("Importation groupée", type=["pdf", "jpg", "png", "jpeg"],
                                    accept_multiple_files=True, key="lot_fichiers")
        if fichiers and st.button("Lancer l'analyse du lot", type="primary"):
            resultats_lot, barre = [], st.progress(0.0)
            for index, fichier in enumerate(fichiers):
                texte = nlp_scanner.extraire_texte(fichier)
                res = nlp_scanner.analyser_avec_nlp(texte, fichier.name,
                                                    round(fichier.size / 1024, 1))
                resultats_lot.append({"Fichier": fichier.name,
                    "Langue": res["Langue détectée"], "Type détecté": res["Type de document"],
                    "Noms": res["Noms (Personnes)"], "Montants": res["Montants (DZD)"],
                    "Statut": "Analysé par NLP"})
                barre.progress((index + 1) / len(fichiers))
            st.success("🎉 Traitement NLP du lot terminé !")
            tableau = pd.DataFrame(resultats_lot)
            st.dataframe(tableau, width="stretch", hide_index=True)
            st.download_button("Télécharger le rapport global (CSV)",
                data=tableau.to_csv(index=False).encode("utf-8"),
                file_name="Rapport_NLP_Terrains_DZ.csv", mime="text/csv")
nlp_scanner.py (ton moteur NLP/OCR, rendu optionnel)
"""Moteur OCR / NLP (dépendances optionnelles : pypdf, pytesseract, langdetect, spacy)."""
from __future__ import annotations

import re

import streamlit as st

try:
    import PyPDF2
    PDF_DISPO = True
except ImportError:
    PDF_DISPO = False

try:
    import pytesseract
    from PIL import Image
    OCR_DISPO = True
except ImportError:
    OCR_DISPO = False

try:
    from langdetect import DetectorFactory, detect
    DetectorFactory.seed = 0
    LANGUE_DISPO = True
except ImportError:
    LANGUE_DISPO = False

try:
    import spacy
    NLP_DISPO = True
except ImportError:
    NLP_DISPO = False


@st.cache_resource(show_spinner=False)
def charger_modele_nlp():
    if not NLP_DISPO:
        return None
    try:
        return spacy.load("fr_core_news_sm")
    except Exception as exc:
        st.warning(f"Modèle NLP non chargé : {exc}")
        return None


def extraire_texte(fichier) -> str:
    texte = ""
    if getattr(fichier, "type", "") == "application/pdf":
        if not PDF_DISPO:
            return ""
        for page in PyPDF2.PdfReader(fichier).pages:
            texte += (page.extract_text() or "") + "\n"
    elif getattr(fichier, "type", "") in ["image/jpeg", "image/png", "image/jpg"]:
        if not OCR_DISPO:
            return ""
        texte = pytesseract.image_to_string(Image.open(fichier), lang="fra")
    return texte


def analyser_avec_nlp(texte: str, nom_fichier: str, taille_ko: float) -> dict:
    resultats = {
        "Nom du fichier": nom_fichier, "Taille (Ko)": taille_ko,
        "Langue détectée": "Inconnue", "Type de document": "📄 Document Général",
        "Noms (Personnes)": "Aucun", "Dates trouvées": "Aucune",
        "Montants (DZD)": "Aucun", "Organisations": "Aucune",
        "Synthèse NLP": "Aucune analyse disponible.",
    }
    if not texte.strip():
        return resultats

    if LANGUE_DISPO:
        try:
            resultats["Langue détectée"] = {"fr": "Français", "ar": "Arabe",
                "en": "Anglais"}.get(detect(texte), detect(texte))
        except Exception:
            pass

    nlp = charger_modele_nlp()
    if nlp is not None:
        doc = nlp(texte)
        for cle, label in (("Noms (Personnes)", "PER"), ("Dates trouvées", "DATE"),
                           ("Montants (DZD)", "MONEY"), ("Organisations", "ORG")):
            vals = list(dict.fromkeys([e.text for e in doc.ents if e.label_ == label]))[:5]
            vide = "Aucune" if label != "PER" else "Aucun"
            resultats[cle] = ", ".join(vals) if vals else vide

        bas = texte.lower()
        if "acte" in bas or "foncier" in bas or "parcelle" in bas:
            resultats["Type de document"] = "🏠 Document Foncier / Immobilier"
            resultats["Synthèse NLP"] = "Termes immobiliers et cadastraux détectés par le modèle."
        elif "facture" in bas or "montant" in bas or "dinars" in bas:
            resultats["Type de document"] = "🧾 Document Financier"
            resultats["Synthèse NLP"] = "Structure financière et montants détectés."
        elif "carte" in bas or "étudiant" in bas:
            resultats["Type de document"] = "🎓 Document Académique"
            resultats["Synthèse NLP"] = "Vocabulaire académique identifié."
        else:
            resultats["Synthèse NLP"] = "Analyse NLP terminée. Aucun motif spécifique fort détecté."
    elif LANGUE_DISPO:
        resultats["Synthèse NLP"] = ("Analyse linguistique partielle : installez spaCy et "
                                     "fr_core_news_sm pour l'extraction des entités nommées.")
    return resultats


def extraire_prix_surface(texte: str):
    prix = None
    for motif in (r"([\d\s.,]{5,})\s*(?:dzd|dinars?)",
                  r"(?:prix|montant)\s*[:=]?\s*([\d\s.,]{5,})"):
        t = re.search(motif, texte, re.IGNORECASE)
        if t:
            chiffres = re.sub(r"[^\d]", "", t.group(1))
            if chiffres and len(chiffres) >= 5:
                prix = int(chiffres)
                break
    surface = None
    t = re.search(r"([\d\s.,]{2,10})\s*(m[²2]|hectares?|ha)\b", texte, re.IGNORECASE)
    if t:
        chiffres = re.sub(r"[^\d]", "", t.group(1))
        if chiffres:
            v = float(chiffres)
            surface = v * 10_000 if t.group(2).lower().startswith(("ha", "hectare")) else v
    return prix, surface


def dependances_manquantes() -> list[str]:
    manquantes = []
    if not PDF_DISPO:
        manquantes.append("pypdf")
    if not OCR_DISPO:
        manquantes.append("pytesseract et Pillow")
    if not LANGUE_DISPO:
        manquantes.append("langdetect")
    if not NLP_DISPO:
        manquantes.append("spacy et fr_core_news_sm")
    return manquantes
helpers.py (filtres, formatage, carte)
"""Fonctions partagées par les pages."""
from __future__ import annotations

from pathlib import Path

import streamlit as st

import catalogue

DOSSIER_IMAGES = Path(__file__).resolve().parent / "images_terrains"


def init_state() -> None:
    st.session_state.setdefault("annonce_selection", None)
    st.session_state.setdefault("demande_envoyee", None)
    st.session_state.setdefault("scan_resultat", None)
    st.session_state.setdefault("filtre_version", 0)


def formater_prix(montant) -> str:
    if montant in (None, ""):
        return "Prix sur demande"
    return f"{int(montant):,} DZD".replace(",", " ")


def formater_surface(m2) -> str:
    if not m2:
        return "Superficie non précisée"
    if float(m2) >= 10_000:
        return f"{float(m2)/10_000:.2f} ha ({int(m2):,} m²)".replace(",", " ")
    return f"{int(m2):,} m²".replace(",", " ")


def image_annonce(annonce: dict):
    nom = (annonce.get("image") or "").strip()
    if not nom:
        return None
    chemin = DOSSIER_IMAGES / nom
    if not chemin.exists():
        return None
    try:
        from PIL import Image
        with Image.open(chemin) as v:
            v.verify()
    except Exception:
        return None
    return chemin


@st.cache_data(show_spinner=False)
def _annonces_cache() -> list[dict]:
    return catalogue.lister_annonces()


def charger_annonces() -> list[dict]:
    return _annonces_cache()


def invalider_cache_annonces() -> None:
    _annonces_cache.clear()


def filtrer_annonces(annonces: list[dict], criteres: dict) -> list[dict]:
    resultat = annonces
    if criteres["types"]:
        resultat = [a for a in resultat if a["type_terrain"] in criteres["types"]]
    if criteres["wilaya"]:
        resultat = [a for a in resultat if a["wilaya"] == criteres["wilaya"]]
    if criteres["commune"]:
        resultat = [a for a in resultat if a["commune"] == criteres["commune"]]
    if criteres["mot_cle"]:
        motif = criteres["mot_cle"].strip().lower()
        resultat = [a for a in resultat if motif in " ".join(str(a.get(c, "")) for c in
                   ("titre", "description", "commune", "reference_fonciere")).lower()]
    if criteres["budget_max"]:
        resultat = [a for a in resultat if (a.get("prix_dzd") or 0) <= criteres["budget_max"]]
    if criteres["superficie_min"]:
        resultat = [a for a in resultat if (a.get("superficie_m2") or 0) >= criteres["superficie_min"]]
    tri = criteres["tri"]
    if tri == "Prix croissant":
        resultat = sorted(resultat, key=lambda a: a.get("prix_dzd") or 0)
    elif tri == "Prix décroissant":
        resultat = sorted(resultat, key=lambda a: -(a.get("prix_dzd") or 0))
    elif tri == "Superficie décroissante":
        resultat = sorted(resultat, key=lambda a: -(a.get("superficie_m2") or 0))
    elif tri == "Wilaya puis commune":
        resultat = sorted(resultat, key=lambda a: (a.get("wilaya", ""), a.get("commune", "")))
    return resultat


def afficher_carte(resultats: list[dict]) -> None:
    try:
        import folium
        from streamlit_folium import st_folium
    except ImportError:
        st.info("La carte interactive nécessite `folium` et `streamlit-folium`.")
        return
    latitudes = [a["latitude"] for a in resultats if a.get("latitude")]
    longitudes = [a["longitude"] for a in resultats if a.get("longitude")]
    if not latitudes:
        st.info("Aucune coordonnée GPS disponible pour ces annonces.")
        return
    carte = folium.Map(location=[sum(latitudes)/len(latitudes), sum(longitudes)/len(longitudes)],
                        zoom_start=9)
    for annonce in resultats:
        if not annonce.get("latitude"):
            continue
        popup = folium.Popup(f"<b>{annonce['titre']}</b><br>{annonce['type_terrain']}<br>"
                             f"{annonce.get('commune','')} ({annonce.get('wilaya','')})<br>"
                             f"{formater_prix(annonce.get('prix_dzd'))}<br>"
                             f"{formater_surface(annonce.get('superficie_m2'))}", max_width=280)
        folium.Marker(location=[annonce["latitude"], annonce["longitude"]], popup=popup,
                      tooltip=annonce["titre"],
                      icon=folium.Icon(color="green", icon="home", prefix="fa")).add_to(carte)
    st_folium(carte, width=None, height=480)
data_communes.py (wilayas + communes)
"""Wilayas et communes d'Algérie (data/communes_algerie.json)."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

FICHIER = Path(__file__).resolve().parent / "data" / "communes_algerie.json"

_TIPAZA_REPLI = [
    ("Tipaza", "4201", 25225), ("Menaceur", "4202", 25480), ("Larhat", "4203", 7359),
    ("Douaouda", "4204", 22408), ("Bourkika", "4205", 22118), ("Khemisti", "4206", 15128),
    ("Aghbal", "4210", 7122), ("Hadjout", "4212", 61523), ("Sidi Amar", "4213", 13332),
    ("Gouraya", "4214", 20144), ("Nador", "4215", 9588), ("Chaiba", "4216", 20427),
    ("Aïn Tagourait", "4217", 10411), ("Cherchell", "4222", 48056), ("Damous", "4223", 17111),
    ("Merad", "4224", 19916), ("Fouka", "4225", 48959), ("Bou Ismaïl", "4226", 41684),
    ("Ahmar El Aïn", "4227", 29566), ("Bouharoun", "4230", 9922), ("Sidi Ghiles", "4232", 15281),
    ("Messelmoun", "4233", 7564), ("Sidi Rached", "4234", 11062), ("Koléa", "4235", 54401),
    ("Attatba", "4236", 27059), ("Sidi Semiane", "4240", 2930), ("Beni Milleuk", "4241", 8045),
    ("Hadjeret Ennous", "4242", 2150),
]

_CHEF_LIEU = [
    ("44", "Aïn Defla", "Aïn Defla", "4401"), ("63", "El Aricha", "El Aricha", "6301"),
    ("64", "Ksar Chellala", "Ksar Chellala", "6401"), ("65", "Aïn Oussara", "Aïn Oussara", "6501"),
    ("66", "Messaâd", "Messaâd", "6601"), ("67", "Ksar El Boukhari", "Ksar El Boukhari", "6701"),
    ("68", "Bou Saâda", "Bou Saâda", "6801"),
    ("69", "El Abiodh Sidi Cheikh", "El Abiodh Sidi Cheikh", "6901"),
]

REPLI = {"42": {"wilaya": "Tipaza", "communes": [
    {"nom": n, "code": c, "pop": p} for n, c, p in _TIPAZA_REPLI]}}
for _code, _wilaya, _chef, _ons in _CHEF_LIEU:
    REPLI[_code] = {"wilaya": _wilaya,
                    "communes": [{"nom": _chef, "code": _ons, "pop": None}]}


@lru_cache(maxsize=1)
def _donnees() -> dict:
    try:
        with open(FICHIER, encoding="utf-8") as f:
            donnees = json.load(f)
    except (OSError, json.JSONDecodeError):
        donnees = {}
    for code, repli in REPLI.items():
        if not donnees.get(code, {}).get("communes"):
            donnees[code] = repli
    return donnees


def wilayas() -> list[tuple[str, str]]:
    return sorted(((c, d["wilaya"]) for c, d in _donnees().items()), key=lambda i: i[0])


def nom_wilaya(code: str) -> str:
    return _donnees().get(code, {}).get("wilaya", "Wilaya " + str(code))


def communes(code_wilaya: str | None) -> list[str]:
    if not code_wilaya:
        return []
    return [c["nom"] for c in _donnees().get(code_wilaya, {}).get("communes", [])]


def communes_detaillees(code_wilaya: str | None) -> list[dict]:
    if not code_wilaya:
        return []
    return list(_donnees().get(code_wilaya, {}).get("communes", []))


def population(code_wilaya: str | None, commune: str | None) -> int | None:
    for item in communes_detaillees(code_wilaya):
        if item["nom"] == commune:
            return item.get("pop")
    return None


def rechercher_communes(texte: str, code_wilaya: str | None = None) -> list[str]:
    if not texte:
        return []
    motif = texte.strip().lower()
    codes = [code_wilaya] if code_wilaya else list(_donnees())
    return [i["nom"] for c in codes for i in communes_detaillees(c)
            if motif in i["nom"].lower()]


def total_communes() -> int:
    return sum(len(v["communes"]) for v in _donnees().values())
catalogue.py (SQLite : annonces + demandes)
"""Catalogue des annonces + demandes clients (SQLite : terrains_rbz.db)."""
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent / "terrains_rbz.db"

TYPES_TERRAIN = ["Terrain à bâtir", "Terrain résidentiel", "Terrain commercial",
    "Terrain industriel", "Terrain agricole", "Terrain viticole", "Terrain forestier",
    "Terrain de lotissement", "Terrain de plage", "Terrain à minerai"]

STATUTS = ["Disponible", "Négociable", "Réservé", "Vendu"]

SCHEMA_ANNONCES = """CREATE TABLE IF NOT EXISTS annonces (
    id TEXT PRIMARY KEY, titre TEXT NOT NULL, type_terrain TEXT NOT NULL,
    wilaya_code TEXT, wilaya TEXT, commune TEXT, superficie_m2 REAL, prix_dzd INTEGER,
    statut TEXT DEFAULT 'Disponible', reference_fonciere TEXT, description TEXT,
    image TEXT, latitude REAL, longitude REAL, telephone TEXT, date_creation TEXT)"""

SCHEMA_DEMANDES = """CREATE TABLE IF NOT EXISTS demandes (
    id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, nom TEXT, telephone TEXT, email TEXT,
    type_terrain TEXT, wilaya TEXT, commune TEXT, budget_max INTEGER, superficie_min REAL,
    notes TEXT, statut TEXT DEFAULT 'Nouvelle')"""

ANNONCES_DEMO = [
    # (id, titre, type, code_wilaya, wilaya, commune, m², prix, statut, réf, desc, img, lat, lon, tel)
    ("TER-TIP-001", "Terrain à bâtir vue panoramique", "Terrain à bâtir", "42", "Tipaza", "Tipaza", 400, 12_500_000, "Disponible", "LF-42/10432", "Terrain résidentiel de 400 m² à 300 m de la mer, papier foncier en ordre.", "plan_cadastral.jpg", 36.5892, 2.4483, "0550 12 34 56"),
    ("TER-TIP-002", "Terrain résidentiel Koléa centre", "Terrain résidentiel", "42", "Tipaza", "Koléa", 500, 4_500_000, "Négociable", "LF-42/20871", "Parcelle de 500 m² près du centre-ville, réseaux disponibles.", "", 36.6340, 2.4490, "0661 45 78 90"),
    ("TER-TIP-003", "Terrain à bâtir Cherchell centre-ville", "Terrain à bâtir", "42", "Tipaza", "Cherchell", 1000, 8_000_000, "Disponible", "LF-42/31007", "1000 m², idéal pour un projet résidentiel ou un petit immeuble.", "", 36.6050, 2.1900, "0770 11 22 33"),
    ("TER-TIP-004", "Terrain agricole irrigué Sidi Amar", "Terrain agricole", "42", "Tipaza", "Sidi Amar", 20_000, 3_000_000, "Négociable", "LF-42/44120", "2 hectares près des périmètres irrigués.", "", 36.6000, 2.2000, "0555 09 88 77"),
    ("TER-TIP-005", "Terrain de lotissement Bou Ismaïl", "Terrain de lotissement", "42", "Tipaza", "Bou Ismaïl", 450, 3_800_000, "Disponible", "LF-42/51983", "Lotissement autorisé, division possible en deux lots.", "", 36.7390, 2.4750, "0699 34 56 78"),
    ("TER-TIP-006", "Terrain commercial Fouka axe principal", "Terrain commercial", "42", "Tipaza", "Fouka", 300, 9_000_000, "Disponible", "LF-42/62014", "300 m² sur l'axe principal, forte visibilité.", "", 36.5750, 2.3200, "0771 65 43 21"),
    ("TER-TIP-007", "Terrain agricole Merad - vergers", "Terrain agricole", "42", "Tipaza", "Merad", 50_000, 7_500_000, "Disponible", "LF-42/73145", "5 ha d'arbres fruitiers, étude de sol disponible.", "", 36.6300, 2.3300, "0663 21 54 87"),
    ("TER-TIP-008", "Terrain forestier Gouraya", "Terrain forestier", "42", "Tipaza", "Gouraya", 100_000, 5_000_000, "Négociable", "LF-42/84522", "10 ha boisés au pied du Chenoua, projet d'écotourisme.", "", 36.6200, 2.1600, "0555 33 77 12"),
    ("TER-TIP-009", "Terrain industriel Hadjout zone d'activité", "Terrain industriel", "42", "Tipaza", "Hadjout", 2000, 18_000_000, "Disponible", "LF-42/91330", "2000 m² en zone d'activité, triphasé.", "", 36.6400, 2.4100, "0772 90 14 63"),
    ("TER-TIP-010", "Terrain résidentiel Attatba", "Terrain résidentiel", "42", "Tipaza", "Attatba", 250, 2_600_000, "Disponible", "LF-42/15640", "250 m², quartier calme, mur de clôture existant.", "", 36.5900, 2.5400, "0662 47 38 05"),
    ("TER-TIP-011", "Terrain à bâtir Douaouda", "Terrain à bâtir", "42", "Tipaza", "Douaouda", 600, 5_200_000, "Négociable", "LF-42/16712", "600 m² plat, orientation optimale, bornage effectué.", "", 36.6700, 2.5600, "0698 12 44 90"),
    ("TER-TIP-012", "Terrain viticole Sidi Ghiles", "Terrain viticole", "42", "Tipaza", "Sidi Ghiles", 15_000, 4_200_000, "Disponible", "LF-42/27891", "1,5 ha de vigne en production.", "", 36.5300, 2.8800, "0667 58 33 21"),
    ("TER-TIP-013", "Terrain à bâtir Ahmar El Aïn", "Terrain à bâtir", "42", "Tipaza", "Ahmar El Aïn", 350, 3_100_000, "Disponible", "LF-42/38904", "350 m² près de la zone urbaine, idéal pour une villa R+1.", "", 36.7400, 2.1100, "0556 71 09 33"),
    ("TER-TIP-014", "Terrain de plage Nador", "Terrain de plage", "42", "Tipaza", "Nador", 800, 15_000_000, "Négociable", "LF-42/49015", "800 m² avec accès direct à la plage.", "", 36.5700, 2.1300, "0773 22 88 40"),
    ("TER-TIP-015", "Terrain à bâtir Menaceur", "Terrain à bâtir", "42", "Tipaza", "Menaceur", 450, 4_100_000, "Disponible", "LF-42/50126", "450 m² à 5 min de Koléa, terrain plat.", "", 36.6500, 2.4800, "0699 17 65 28"),
    ("TER-TIP-016", "Terrain agricole Larhat", "Terrain agricole", "42", "Tipaza", "Larhat", 30_000, 4_800_000, "Disponible", "LF-42/61237", "3 ha de terre arable en Mitidja.", "", 36.7000, 2.3800, "0661 84 09 72"),
    # ... + 18 annonces dans les autres wilayas (Alger, Blida, Boumerdès, Tizi Ouzou, Béjaïa, Oran…)
]


def _connexion() -> sqlite3.Connection:
    conn = sqlite3.connect(BASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connexion() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS terrains (id TEXT PRIMARY KEY,
            titulaire TEXT, superficie TEXT, statut TEXT, prix TEXT, gps TEXT, telephone TEXT)""")
        conn.execute(SCHEMA_ANNONCES)
        conn.execute(SCHEMA_DEMANDES)


def semer_annonces() -> int:
    init_db()
    with _connexion() as conn:
        if conn.execute("SELECT COUNT(*) FROM annonces").fetchone()[0]:
            return 0
        maintenant = datetime.now().strftime("%Y-%m-%d %H:%M")
        conn.executemany("""INSERT OR IGNORE INTO annonces (id, titre, type_terrain,
            wilaya_code, wilaya, commune, superficie_m2, prix_dzd, statut, reference_fonciere,
            description, image, latitude, longitude, telephone, date_creation)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", [a + (maintenant,) for a in ANNONCES_DEMO])
    return len(ANNONCES_DEMO)


def lister_annonces() -> list[dict]:
    init_db()
    with _connexion() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM annonces ORDER BY date_creation DESC, id").fetchall()]


def ajouter_annonce(donnees: dict) -> None:
    init_db()
    champs = ("id", "titre", "type_terrain", "wilaya_code", "wilaya", "commune",
        "superficie_m2", "prix_dzd", "statut", "reference_fonciere", "description",
        "image", "latitude", "longitude", "telephone", "date_creation")
    valeurs = [donnees.get(c) for c in champs]
    if not valeurs[0]:
        raise ValueError("L'identifiant de l'annonce est obligatoire.")
    if not valeurs[-1]:
        valeurs[-1] = datetime.now().strftime("%Y-%m-%d %H:%M")
    with _connexion() as conn:
        conn.execute(f"INSERT OR REPLACE INTO annonces ({','.join(champs)}) "
                     f"VALUES ({','.join('?' * len(champs))})", valeurs)


def supprimer_annonce(identifiant: str) -> None:
    with _connexion() as conn:
        conn.execute("DELETE FROM annonces WHERE id = ?", (identifiant,))


def enregistrer_demande(donnees: dict) -> int:
    init_db()
    with _connexion() as conn:
        cur = conn.execute("""INSERT INTO demandes (date, nom, telephone, email, type_terrain,
            wilaya, commune, budget_max, superficie_min, notes, statut)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (datetime.now().strftime("%Y-%m-%d %H:%M"), donnees.get("nom", ""),
             donnees.get("telephone", ""), donnees.get("email", ""), donnees.get("type_terrain", ""),
             donnees.get("wilaya", ""), donnees.get("commune", ""), donnees.get("budget_max"),
             donnees.get("superficie_min"), donnees.get("notes", ""), "Nouvelle"))
        return int(cur.lastrowid)


def lister_demandes() -> list[dict]:
    init_db()
    with _connexion() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM demandes ORDER BY id DESC").fetchall()]


def maj_statut_demande(identifiant: int, statut: str) -> None:
    with _connexion() as conn:
        conn.execute("UPDATE demandes SET statut = ? WHERE id = ?", (statut, identifiant))


def supprimer_demande(identifiant: int) -> None:
    with _connexion() as conn:
        conn.execute("DELETE FROM demandes WHERE id = ?", (identifiant,))


def correspondances(demande: dict, annonces: list[dict]) -> list[dict]:
    """Annonces correspondant à une demande (score)."""
    resultat = []
    for a in annonces:
        score = 0
        if demande.get("type_terrain") and a["type_terrain"] == demande["type_terrain"]:
            score += 40
        if demande.get("wilaya") and a["wilaya"] == demande["wilaya"]:
            score += 25
        if demande.get("commune") and a["commune"] == demande["commune"]:
            score += 20
        if demande.get("budget_max"):
            score += 10 if (a["prix_dzd"] or 0) <= demande["budget_max"] else -15
        if demande.get("superficie_min") and (a["superficie_m2"] or 0) >= demande["superficie_min"]:
            score += 5
        if score >= 30:
            resultat.append({**a, "score": score})
    return sorted(resultat, key=lambda a: a["score"], reverse=True)
