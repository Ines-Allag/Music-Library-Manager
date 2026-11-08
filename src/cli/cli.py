"""Point d'entrée en ligne de commande (CLI).

Exemples :
    python3 src/cli/cli.py -h
    python3 src/cli/cli.py -f samples/Classical.mp3
"""
import argparse
import sys
from pathlib import Path
BLEU = "\033[94m"
RESET = "\033[0m"
# Permet d'importer le dossier src/library depuis src/cli
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from library.metadata import read_metadata  # noqa: E402
from library.scanner import  Scanner

def build_parser():
    """Définit les options de la ligne de commande."""
    parser = argparse.ArgumentParser(
        description="Lit les métadonnées de fichiers MP3/FLAC et génère des playlists XSPF."
    )

    # -f et -d sont exclusives : on ne peut pas utiliser les deux en même temps
    source = parser.add_mutually_exclusive_group()
    source.add_argument("-f", "--file", help="fichier MP3 ou FLAC à analyser")
    source.add_argument("-d", "--directory", help="dossier à explorer (pas encore implémenté)")

    parser.add_argument("-o", "--output", help="fichier XSPF de sortie (pas encore implémenté)")
    return parser


def format_duration(seconds):
    """Transforme des secondes en 'minutes:secondes' (ex. 185.4 -> 3:05)."""
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes}:{secs:02d}"


def display_metadata(metadata):
    """Affiche les métadonnées dans la console."""
    print(f"Fichier   : {metadata['path']}")
    print(f"Format    : {metadata['format']}")
    print(f"Titre     : {metadata['title']}")
    print(f"Artiste   : {metadata['artist']}")
    print(f"Album     : {metadata['album']}")
    print(f"Date      : {metadata['date']}")
    print(f"Genre     : {metadata['genre']}")
    print(f"Piste n°  : {metadata['tracknumber']}")
    print(f"Durée     : {format_duration(metadata['duration'])}")
    print(f"Débit     : {metadata['bitrate']} kbit/s")

def display_musiques(musiques):
    """Affiche la liste des musiques trouvées dans un dossier."""
    print(f"{len(musiques)} musique(s) trouvée(s) :")
    for musique in musiques:
        duree = format_duration(musique["duration"])
        print(f"- {musique['artist']} - {musique['title']} ({duree})")
        print(f"  {musique['path']}")
        print(f"{BLEU}  {musique['format']} {RESET}")


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.file and not args.directory:
        print("Erreur : aucun paramètre. Tapez -h (ou --help) pour obtenir de l'aide.")
        sys.exit(1)

    if args.file:
        try:
            metadata = read_metadata(args.file)
        except (FileNotFoundError, ValueError) as error:
            print(f"Erreur : {error}")
            sys.exit(1)
        display_metadata(metadata)


    elif args.directory:
        if not Path(args.directory).is_dir():
            print(f"Erreur : dossier introuvable : {args.directory}")
            sys.exit(1)
        musiques = Scanner(args.directory).scan()
        display_musiques(musiques)



if __name__ == "__main__":
    main()
