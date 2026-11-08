# Music Library Project

*L3 I - Python 2026-2027*

Small Python app to read MP3/FLAC metadata, explore folders, and generate XSPF playlists.

## Team

| Last name | First name |
|-----------|------------|
| Allag     | Ines       |
| Lazri     | Aris       |
| Arezki    | Youcef     |

## Install

```
pip install -r requirements.txt
```

## Usage (CLI)

```
python3 src/cli/cli.py -h
python3 src/cli/cli.py -f music.mp3
python3 src/cli/cli.py -d ./music/
python3 src/cli/cli.py -d ./music/ -o playlist.xspf
```

## Tests

```
python3 -m pytest src/tests-auto
```