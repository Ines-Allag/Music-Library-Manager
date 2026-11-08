"""Génération et sauvegarde de playlists au format XSPF.

Le module reçoit la liste de dictionnaires produite par Scanner (clés : path,
title, artist, album, tracknumber, duration...) et produit un fichier .xspf.
Il n'affiche rien : l'affichage est fait par l'appelant (CLI ou GUI).
"""
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

NAMESPACE = "http://xspf.org/ns/0/"
UNKNOWN = "Inconnu" 
DEFAULT_OUTPUT = "default_playlist.xspf"


def _texte(musique, cle):
    """Retourne la valeur texte d'une clé, ou None si absente/vide/"Inconnu"."""
    valeur = musique.get(cle)
    if valeur is None:
        return None
    valeur = str(valeur).strip()
    if valeur == "" or valeur == UNKNOWN:
        return None
    return valeur


def _numero_piste(musique):
    """Convertit le tag tracknumber en entier ("3/12" -> 3). None si invalide."""
    valeur = _texte(musique, "tracknumber")
    if valeur is None:
        return None
    try:
        numero = int(valeur.split("/")[0])
    except ValueError:
        return None
    return numero if numero > 0 else None


def _duree_ms(musique):
    """Convertit la durée (secondes) en millisecondes entières. None si invalide."""
    try:
        millisecondes = int(round(float(musique.get("duration")) * 1000))
    except (TypeError, ValueError):
        return None
    return millisecondes if millisecondes > 0 else None


def _location(musique):
    """Retourne l'URI file:// du fichier (obligatoire en XSPF), ou None."""
    chemin = musique.get("path")
    if not chemin:
        return None
    return Path(chemin).resolve().as_uri() 


def _ajouter_element(parent, nom, valeur):
    """Ajoute <nom>valeur</nom> à parent, sauf si valeur est None."""
    if valeur is not None:
        ET.SubElement(parent, nom).text = str(valeur)


def creer_playlist(musiques, titre="Playlist"):
    """Construit l'arbre XML XSPF à partir d'une liste de musiques.

    Une musique sans chemin est ignorée. Les métadonnées absentes ou
    invalides sont simplement omises (tous ces éléments sont optionnels).

    Retourne un ET.ElementTree.
    Lève ValueError si aucune musique exploitable n'est fournie.
    """
    if not musiques:
        raise ValueError("Aucune musique à ajouter à la playlist.")

    racine = ET.Element("playlist", {"version": "1", "xmlns": NAMESPACE})
    ET.SubElement(racine, "title").text = titre
    ET.SubElement(racine, "date").text = datetime.now().astimezone().isoformat(timespec="seconds")
    liste_pistes = ET.SubElement(racine, "trackList")

    nb_pistes = 0
    for musique in musiques:
        location = _location(musique)
        if location is None:
            continue
        piste = ET.SubElement(liste_pistes, "track")
        _ajouter_element(piste, "location", location)
        _ajouter_element(piste, "title", _texte(musique, "title"))
        _ajouter_element(piste, "creator", _texte(musique, "artist"))
        _ajouter_element(piste, "album", _texte(musique, "album"))
        _ajouter_element(piste, "trackNum", _numero_piste(musique))
        _ajouter_element(piste, "duration", _duree_ms(musique))
        nb_pistes += 1

    if nb_pistes == 0:
        raise ValueError("Aucune musique exploitable (chemin manquant).")

    ET.indent(racine)
    return ET.ElementTree(racine)


def sauvegarder_playlist(musiques, chemin=DEFAULT_OUTPUT, titre="Playlist"):
    """Génère la playlist XSPF et l'enregistre dans un fichier.

    Paramètres :
        musiques : liste de dictionnaires (voir Scanner.scan).
        chemin : fichier de sortie (".xspf" ajouté s'il manque).
        titre : titre de la playlist.

    Retourne le chemin du fichier créé.
    Lève ValueError si la liste est vide, OSError si l'écriture échoue.
    """
    arbre = creer_playlist(musiques, titre)

    chemin = Path(chemin)
    if chemin.suffix.lower() != ".xspf":
        chemin = chemin.with_suffix(".xspf")

    try:
        arbre.write(chemin, encoding="utf-8", xml_declaration=True)
    except OSError as erreur:
        raise OSError(f"Impossible d'écrire la playlist : {chemin} ({erreur})")
    return chemin