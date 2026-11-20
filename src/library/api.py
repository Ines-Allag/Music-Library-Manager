"""Recherche d'informations musicales via des API web.

Ce module complète les métadonnées d'un fichier MP3/FLAC :
    - chercher_album : infos complètes d'un album (titre, année, pistes, pochette)
      avec l'API publique de Deezer (sans clé) ;
    - chercher_paroles : paroles d'un morceau avec l'API lyrics.ovh (sans clé) ;
    - album_complet : album + paroles de toutes les pistes ;
    - telecharger_image : télécharge la pochette (utilisée surtout par le GUI).

Le module n'affiche rien : l'affichage est fait par l'appelant (CLI ou GUI).
Il renvoie des données, ou lève une exception :
    - ValueError : paramètre invalide, album ou paroles introuvables ;
    - ConnectionError : problème réseau ou réponse inattendue de l'API.
"""
import unicodedata
from pathlib import Path

import requests

DEEZER_URL = "https://api.deezer.com"
LYRICS_URL = "https://api.lyrics.ovh/v1"
TIMEOUT = 15  # secondes d'attente maximum par requête
ESSAIS = 3  # nombre de tentatives si le serveur est lent ou injoignable
UNKNOWN = "Inconnu"  # même valeur que dans metadata.py


def _valide(valeur, nom):
    """Vérifie qu'un paramètre de recherche est utilisable et le nettoie.

    Lève ValueError s'il est vide ou vaut "Inconnu" (tag manquant).
    """
    valeur = str(valeur or "").strip()
    if valeur == "" or valeur == UNKNOWN:
        raise ValueError(f"{nom} manquant : impossible de lancer la recherche.")
    return valeur


def _normalise(texte):
    """Met un texte en minuscules sans accents pour comparer deux noms."""
    texte = unicodedata.normalize("NFD", str(texte).lower())
    return "".join(c for c in texte if unicodedata.category(c) != "Mn").strip()


def _meilleur_resultat(resultats, artiste, album):
    """Choisit dans les résultats Deezer l'album qui correspond vraiment.

    Garde seulement les albums du bon artiste (sinon on pourrait renvoyer la
    reprise ou la version instrumentale d'un autre artiste), puis préfère le
    titre identique, et évite les versions "instrumental" non demandées.

    Retourne le résultat choisi, ou None si aucun ne correspond.
    """
    artiste_n = _normalise(artiste)
    album_n = _normalise(album)

    candidats = []
    for resultat in resultats:
        nom = _normalise(resultat.get("artist", {}).get("name", ""))
        if nom == artiste_n or artiste_n in nom or nom in artiste_n and nom:
            candidats.append(resultat)
    if not candidats:
        return None

    def score(resultat):
        titre = _normalise(resultat.get("title", ""))
        meme_titre = titre == album_n
        instrumental = "instrumental" in titre and "instrumental" not in album_n
        return (meme_titre, not instrumental)

    return max(candidats, key=score)


def _get_json(url, params=None):
    """Envoie une requête GET et renvoie la réponse JSON (dictionnaire).

    Si le serveur est lent ou injoignable (timeout, coupure), la requête est
    retentée jusqu'à ESSAIS fois avant d'abandonner.

    Lève ConnectionError si internet est indisponible, si le serveur répond
    avec une erreur, ou si la réponse n'est pas du JSON.
    """
    derniere_erreur = None
    for _ in range(ESSAIS):
        try:
            reponse = requests.get(url, params=params, timeout=TIMEOUT)
            reponse.raise_for_status()
            return reponse.json()
        except (requests.exceptions.Timeout,
                requests.exceptions.ConnectionError) as erreur:
            derniere_erreur = erreur  # problème temporaire : on réessaie
        except requests.exceptions.RequestException as erreur:
            raise ConnectionError(f"Erreur de connexion à l'API : {erreur}")
        except ValueError:
            raise ConnectionError("Réponse inattendue de l'API (JSON invalide).")
    raise ConnectionError(f"Erreur de connexion à l'API : {derniere_erreur}")


def chercher_album(artiste, album, titre=None):
    """Cherche un album sur Deezer et renvoie ses informations complètes.

    Paramètres :
        artiste : nom de l'artiste (ex. "Beyoncé").
        album : titre de l'album (ex. "Lemonade").
        titre : titre du morceau (facultatif). Sert de recours si l'album
            n'est pas trouvé : on cherche alors le morceau, puis son album
            (utile pour un single dont le tag "album" est le titre du morceau).

    Retourne un dictionnaire avec les clés : title, artist, date (ex.
    "2016-04-23"), genres (liste), cover_url (URL de la pochette, ou None)
    et tracks (liste de dictionnaires : number, title, duration en secondes).

    Lève ValueError si un paramètre est vide/"Inconnu" ou si l'album est
    introuvable, et ConnectionError en cas de problème réseau.
    """
    artiste = _valide(artiste, "Artiste")
    album = _valide(album, "Album")

    # 1) Recherche d'album : d'abord stricte, puis plus large.
    #    On garde le résultat du bon artiste qui correspond le mieux.
    resultat = None
    for requete in (f'artist:"{artiste}" album:"{album}"', f"{artiste} {album}"):
        recherche = _get_json(f"{DEEZER_URL}/search/album", {"q": requete})
        resultat = _meilleur_resultat(recherche.get("data") or [], artiste, album)
        if resultat is not None:
            break

    # 2) Recours : on cherche le morceau, puis on prend son album
    titre = str(titre or "").strip()
    if resultat is None and titre and titre != UNKNOWN:
        recherche = _get_json(
            f"{DEEZER_URL}/search/track",
            {"q": f'artist:"{artiste}" track:"{titre}"'},
        )
        piste = _meilleur_resultat(recherche.get("data") or [], artiste, titre)
        if piste is not None and piste.get("album", {}).get("id"):
            resultat = {"id": piste["album"]["id"]}

    if resultat is None:
        raise ValueError(f"Album introuvable : {artiste} - {album}")

    # 3) Détail de l'album : liste des pistes, date, genres
    details = _get_json(f"{DEEZER_URL}/album/{resultat['id']}")
    if "error" in details:
        raise ValueError(f"Album introuvable : {artiste} - {album}")

    pistes = []
    for numero, piste in enumerate(details.get("tracks", {}).get("data", []), 1):
        pistes.append({
            "number": numero,
            "title": piste.get("title", UNKNOWN),
            "duration": piste.get("duration", 0),
        })

    genres = [g["name"] for g in details.get("genres", {}).get("data", [])]
    cover = (details.get("cover_xl") or details.get("cover_big")
             or details.get("cover_medium"))

    return {
        "title": details.get("title", album),
        "artist": details.get("artist", {}).get("name", artiste),
        "date": details.get("release_date", UNKNOWN),
        "genres": genres,
        "cover_url": cover or None,
        "tracks": pistes,
    }


def chercher_paroles(artiste, titre):
    """Cherche les paroles d'un morceau sur lyrics.ovh.

    Paramètres :
        artiste : nom de l'artiste.
        titre : titre du morceau.

    Retourne les paroles (texte brut).
    Lève ValueError si un paramètre est invalide ou si les paroles sont
    introuvables, et ConnectionError en cas de problème réseau.
    """
    artiste = _valide(artiste, "Artiste")
    titre = _valide(titre, "Titre")

    # requests encode les caractères spéciaux (espaces, accents, "/"...) pour nous
    url = f"{LYRICS_URL}/{requests.utils.quote(artiste, safe='')}/" \
          f"{requests.utils.quote(titre, safe='')}"
    try:
        reponse = requests.get(url, timeout=TIMEOUT)
    except requests.exceptions.RequestException as erreur:
        raise ConnectionError(f"Erreur de connexion à l'API : {erreur}")

    if reponse.status_code == 404:
        raise ValueError(f"Paroles introuvables : {artiste} - {titre}")
    try:
        reponse.raise_for_status()
        paroles = reponse.json().get("lyrics", "").strip()
    except (requests.exceptions.RequestException, ValueError) as erreur:
        raise ConnectionError(f"Réponse inattendue de l'API : {erreur}")

    if not paroles:
        raise ValueError(f"Paroles introuvables : {artiste} - {titre}")
    return paroles


def album_complet(artiste, album, titre=None):
    """Renvoie les infos d'un album avec les paroles de chaque piste.

    Même dictionnaire que chercher_album, mais chaque piste a une clé
    supplémentaire "lyrics" : le texte des paroles, ou None si elles sont
    introuvables (une piste sans paroles n'interrompt pas la recherche).

    Lève ValueError / ConnectionError comme chercher_album. Une erreur
    réseau sur les paroles d'une piste est aussi traitée comme "pas de
    paroles", pour que l'album s'affiche quand même.
    """
    infos = chercher_album(artiste, album, titre)
    for piste in infos["tracks"]:
        try:
            piste["lyrics"] = chercher_paroles(artiste, piste["title"])
        except (ValueError, ConnectionError):
            piste["lyrics"] = None
    return infos


def telecharger_image(url, chemin):
    """Télécharge une image (pochette) et l'enregistre dans un fichier.

    Paramètres :
        url : adresse de l'image (ex. infos["cover_url"]).
        chemin : fichier de destination (ex. "dossier_album/cover.jpg").
            Les dossiers manquants sont créés.

    Retourne le chemin (Path) du fichier créé.
    Lève ValueError si l'URL est vide, ConnectionError en cas de problème
    réseau, OSError si l'écriture échoue.
    """
    if not url:
        raise ValueError("Aucune URL de pochette à télécharger.")

    try:
        reponse = requests.get(url, timeout=TIMEOUT)
        reponse.raise_for_status()
    except requests.exceptions.RequestException as erreur:
        raise ConnectionError(f"Téléchargement impossible : {erreur}")

    chemin = Path(chemin)
    try:
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_bytes(reponse.content)
    except OSError as erreur:
        raise OSError(f"Impossible d'écrire l'image : {chemin} ({erreur})")
    return chemin