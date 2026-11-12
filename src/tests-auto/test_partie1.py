"""Tests automatiques simples du projet (lancer : python3 -m pytest src/tests-auto)."""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from library.metadata import read_metadata
from library.playlist import creerPlaylist, dureeMs, numeroPiste, sauvPlaylist
from library.verification import est_musique


# ---------- verification.py : est-ce un vrai MP3/FLAC ? ----------

def test_faux_mp3_est_refuse(tmp_path):
    """Un fichier texte renommé en .mp3 n'est pas une musique."""
    faux = tmp_path / "faux.mp3"
    faux.write_text("ceci est du texte")
    assert est_musique(str(faux)) is False


def test_extension_non_supportee_est_refusee(tmp_path):
    """Un fichier .txt n'est pas une musique."""
    fichier = tmp_path / "notes.txt"
    fichier.write_text("bonjour")
    assert est_musique(str(fichier)) is False


def test_flac_avec_bonne_signature_est_accepte(tmp_path):
    """Un fichier .flac qui commence par 'fLaC' passe les contrôles."""
    flac = tmp_path / "test.flac"
    flac.write_bytes(b"fLaC" + b"\x00" * 10)
    assert est_musique(str(flac)) is True


# ---------- metadata.py ----------

def test_fichier_inexistant_leve_une_erreur():
    """Lire un fichier qui n'existe pas lève FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        read_metadata("fichier_qui_n_existe_pas.mp3")


# ---------- playlist.py ----------

def test_numero_piste_avec_total():
    """"3/12" donne 3."""
    assert numeroPiste({"tracknumber": "3/12"}) == 3


def test_numero_piste_inconnu():
    """Un numéro "Inconnu" donne None."""
    assert numeroPiste({"tracknumber": "Inconnu"}) is None


def test_duree_en_millisecondes():
    """185.4 secondes donnent 185400 millisecondes."""
    assert dureeMs({"duration": 185.4}) == 185400


def test_playlist_vide_leve_une_erreur():
    """Une playlist sans musique lève ValueError."""
    with pytest.raises(ValueError):
        creerPlaylist([])


def test_playlist_xspf_est_bien_creee(tmp_path):
    """La playlist est enregistrée en .xspf et contient la musique."""
    musique = {"path": "musique.mp3", "title": "Titre", "artist": "Artiste",
               "album": "Album", "tracknumber": "1", "duration": 60.0}
    sortie = tmp_path / "ma_playlist.xspf"
    chemin = sauvPlaylist([musique], sortie, "Test")

    assert Path(chemin).is_file()
    racine = ET.parse(chemin).getroot()
    titres = [t.text for t in racine.iter("{http://xspf.org/ns/0/}title")]
    assert "Test" in titres and "Titre" in titres