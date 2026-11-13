"""Point d'entrée en ligne de commande (CLI).

Exemples :
    python3 src/cli/cli.py -h
    python3 src/cli/cli.py -f samples/musique_test/sousDossier1/Classical.mp3
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
from library.playlist import sauvPlaylist, DEFAULT_OUTPUT
from library.tags import modify_tags

def build_parser():
    """Définit les options de la ligne de commande."""
    parser = argparse.ArgumentParser(
        description="Lit les métadonnées de fichiers MP3/FLAC, explore des dossiers "
                    "et génère des playlists XSPF.",
        epilog="exemples :\n"
               "  python3 src/cli/cli.py -f music.mp3\n"
               "  python3 src/cli/cli.py -d ./music/\n"
               "  python3 src/cli/cli.py -d ./music/ -o playlist.xspf",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # -f et -d sont exclusives : on ne peut pas utiliser les deux en même temps
    source = parser.add_mutually_exclusive_group()
    source.add_argument("-f", "--file",
                        help="fichier MP3 ou FLAC dont on affiche les métadonnées")
    source.add_argument("-d", "--directory",
                        help="dossier à explorer avec ses sous-dossiers : "
                             "affiche les fichiers MP3/FLAC trouvés")

    parser.add_argument(
        "-o", "--output", nargs="?", const=DEFAULT_OUTPUT,
        help=f"enregistre le résultat dans une playlist XSPF "
             f"(nom du fichier facultatif, défaut : {DEFAULT_OUTPUT})"
    )
    parser.add_argument(
        "--set", action="append", metavar="TAG=VALEUR",
        help="modifie un tag du fichier donné avec -f (option répétable), "  
             "ex. --set \"title=Mon titre\" --set \"artist=Mon artiste\""
    )

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


def generer_playlist(musiques, sortie, titre):
    """Sauvegarde la playlist XSPF et affiche le résultat."""
    try:
        chemin = sauvPlaylist(musiques, sortie, titre)
    except (ValueError, OSError) as error:
        print(f"Erreur : {error}")
        sys.exit(1)
    print(f"Playlist enregistrée : {chemin}")

def parse_changes(pairs):
    """Transforme ["title=Mon titre", ...] en {"title": "Mon titre"}."""
    changes = {}
    for pair in pairs:
        if "=" not in pair:
            print(f"Erreur : '{pair}' n'est pas de la forme TAG=VALEUR.")
            sys.exit(1)
        tag, value = pair.split("=", 1)
        changes[tag.strip().lower()] = value
    return changes

def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.file and not args.directory:
        print("Erreur : aucun paramètre. Tapez -h (ou --help) pour obtenir de l'aide.")
        sys.exit(1)

    if args.set and not args.file:  # <<< AJOUTE
        print("Erreur : --set s'utilise avec -f (un fichier).")  # <<< AJOUTE
        sys.exit(1)

    if args.file:
        if args.set:  # <<< AJOUTE
            try:  # <<< AJOUTE
                modify_tags(args.file, parse_changes(args.set))  # <<< AJOUTE
            except (FileNotFoundError, ValueError) as error:  # <<< AJOUTE
                print(f"Erreur : {error}")  # <<< AJOUTE
                sys.exit(1)  # <<< AJOUTE
            print("Tags modifiés.")
        try:
            metadata = read_metadata(args.file)
        except (FileNotFoundError, ValueError) as error:
            print(f"Erreur : {error}")
            sys.exit(1)
        display_metadata(metadata)
        if args.output:
            generer_playlist([metadata], args.output, Path(args.file).stem)



    elif args.directory:
        if not Path(args.directory).is_dir():
            print(f"Erreur : dossier introuvable : {args.directory}")
            sys.exit(1)
        musiques = Scanner(args.directory).scan()
        display_musiques(musiques)


        if args.output:
            generer_playlist(musiques, args.output, Path(args.directory).name)



if __name__ == "__main__":
    main()