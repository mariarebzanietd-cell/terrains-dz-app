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
