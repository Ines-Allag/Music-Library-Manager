"""Vérification qu'un fichier est bien un MP3 ou un FLAC.

Trois contrôles successifs : le fichier existe, son extension et son type MIME
sont ceux d'un MP3/FLAC, et ses premiers octets (sa signature) correspondent
au format annoncé.
"""
import os
import mimetypes

# Extension -> types MIME acceptés pour cette extension
FORMATS = {
    ".mp3": ["audio/mpeg"],
    ".flac": ["audio/flac", "audio/x-flac"],
}


def signature_valide(chemin, extension):
    """Vérifie que les premiers octets du fichier correspondent à son format.

    Un FLAC commence par "fLaC". Un MP3 commence par "ID3" (s'il contient des
    métadonnées) ou par l'octet 0xFF (s'il n'en contient pas). Cette vérification
    simplifiée détecte un PDF ou une image renommés en .mp3.

    Paramètres :
        chemin : chemin du fichier à lire.
        extension : extension en minuscules, ".mp3" ou ".flac".

    Retourne True si la signature est correcte, False sinon.
    """
    with open(chemin, "rb") as fichier:
        debut = fichier.read(4)

    if extension == ".flac":
        return debut == b"fLaC"
    if extension == ".mp3":
        return debut[:3] == b"ID3" or debut[:1] == b"\xff"
    return False


def est_musique(chemin):
    """Indique si le fichier est un MP3 ou un FLAC valide.

    Contrôles effectués, dans l'ordre : le chemin est un fichier existant,
    l'extension est .mp3 ou .flac, le type MIME correspond à l'extension,
    et la signature du contenu est correcte (voir signature_valide).

    Paramètre :
        chemin : chemin du fichier à tester.

    Retourne True si les trois contrôles passent, False sinon.
    Cette fonction n'affiche rien.
    """
    if not os.path.isfile(chemin):
        return False

    extension = os.path.splitext(chemin)[1].lower()
    if extension not in FORMATS:
        return False

    type_mime = mimetypes.guess_type(chemin)[0]
    if type_mime not in FORMATS[extension]:
        return False

    return signature_valide(chemin, extension)