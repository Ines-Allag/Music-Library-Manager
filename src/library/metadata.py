"""Lecture des métadonnées (tags) d'un fichier MP3 ou FLAC avec mutagen."""
import os

import mutagen

# Tags lus dans le fichier. Avec easy=True, les noms sont identiques
# pour le MP3 (ID3) et le FLAC (Vorbis comment).
TAGS = ["title", "artist", "album", "date", "genre", "tracknumber"]

# Classes renvoyées par mutagen.File(..., easy=True) -> nom du format
FORMATS = {"EasyMP3": "MP3", "FLAC": "FLAC"}

UNKNOWN = "Inconnu"


def read_metadata(path):
    """Lit un fichier MP3 ou FLAC et renvoie ses métadonnées dans un dictionnaire.

    Clés du dictionnaire : path, format, title, artist, album, date, genre,
    tracknumber, duration (secondes), bitrate (kbit/s).
    Un tag absent vaut "Inconnu".

    Lève FileNotFoundError si le fichier n'existe pas,
    et ValueError s'il n'est pas un MP3/FLAC lisible.
    Cette fonction n'affiche rien : l'affichage est fait par l'appelant.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Fichier introuvable : {path}")

    try:
        audio = mutagen.File(path, easy=True)
    except mutagen.MutagenError as error:
        raise ValueError(f"Fichier audio illisible : {path} ({error})")

    audio_format = FORMATS.get(type(audio).__name__) if audio is not None else None
    if audio_format is None:
        raise ValueError(f"Format non supporté (MP3 ou FLAC attendu) : {path}")

    metadata = {"path": path, "format": audio_format}

    for tag in TAGS:
        values = audio.get(tag)  # mutagen renvoie une liste, ex. ["Beyoncé"]
        metadata[tag] = values[0] if values else UNKNOWN

    metadata["duration"] = audio.info.length
    metadata["bitrate"] = audio.info.bitrate // 1000

    return metadata
