"""Exploration récursive d'un dossier pour en extraire les musiques MP3/FLAC.

Le Scanner parcourt un dossier et tous ses sous-dossiers, garde uniquement les
fichiers MP3/FLAC valides, et lit leurs métadonnées. Il n'affiche rien : l'affichage
est fait par l'appelant (CLI ou GUI).
"""
import os

from library.verification import est_musique
from library.metadata import read_metadata


class Scanner:
    """Explore un dossier et ses sous-dossiers, et garde les musiques."""

    def __init__(self, dossier):
        """Crée un scanner pour un dossier.

        Paramètre :
            dossier : chemin du dossier à explorer.
        """
        self.dossier = dossier

    def scan(self):
        """Parcourt le dossier récursivement et retourne les musiques trouvées.

        Pour chaque fichier, vérifie avec est_musique qu'il s'agit d'un MP3/FLAC
        valide, puis lit ses métadonnées avec read_metadata. Un fichier musical
        dont les métadonnées sont illisibles (ValueError) est ignoré, pour ne
        pas interrompre tout le parcours.

        Retourne une liste de dictionnaires, un par musique (clés : path, format,
        title, artist, album, date, genre, tracknumber, duration, bitrate).
        La liste est vide si aucune musique n'est trouvée.
        """
        musiques = []
        for racine, sous_dossiers, noms in os.walk(self.dossier):
            for nom in noms:
                chemin = os.path.join(racine, nom)
                if est_musique(chemin):
                    try:
                        musiques.append(read_metadata(chemin))
                    except ValueError:
                        pass  # métadonnées illisibles : on ignore ce fichier
        return musiques