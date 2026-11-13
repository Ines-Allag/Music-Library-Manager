"""Modification des tags (métadonnées) d'un fichier MP3 ou FLAC avec mutagen."""
import os

import mutagen

EDITABLE_TAGS = ["title", "artist", "album", "date", "genre", "tracknumber"]

SUPPORTED = ("EasyMP3", "FLAC")


def modify_tags(path, changes):
    """Modifie des tags d'un fichier MP3 ou FLAC et sauvegarde le fichier.

    Paramètres :
        path : chemin du fichier audio.
        changes : dictionnaire {tag: nouvelle valeur}, par exemple
            {"title": "Nouveau titre", "artist": "Artiste"}.
            Les tags autorisés sont ceux de EDITABLE_TAGS.

    Lève FileNotFoundError si le fichier n'existe pas, et ValueError si le
    fichier n'est pas un MP3/FLAC lisible, si aucune modification n'est
    donnée, ou si un tag n'est pas autorisé.
    Cette fonction n'affiche rien : l'affichage est fait par l'appelant.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Fichier introuvable : {path}")
    if not changes:
        raise ValueError("Aucune modification demandée.")
    for tag in changes:
        if tag not in EDITABLE_TAGS:
            raise ValueError(
                f"Tag non modifiable : {tag} (autorisés : {', '.join(EDITABLE_TAGS)})"
            )

    try:
        audio = mutagen.File(path, easy=True)
    except mutagen.MutagenError as error:
        raise ValueError(f"Fichier audio illisible : {path} ({error})")
    if audio is None or type(audio).__name__ not in SUPPORTED:
        raise ValueError(f"Format non supporté (MP3 ou FLAC attendu) : {path}")

    for tag, value in changes.items():
        audio[tag] = value

    audio.save()