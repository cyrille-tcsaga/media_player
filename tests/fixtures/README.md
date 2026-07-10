# Test fixtures

- `sample.mp3` — 2 secondes de silence, mono, 44.1kHz. Utilisé par `tests/test_player_engine.py`
  pour valider `PlayerEngine` sans dépendre d'un fichier audio réel.

Régénération :

```bash
ffmpeg -f lavfi -i "anullsrc=r=44100:cl=mono" -t 2 -c:a libmp3lame -q:a 9 tests/fixtures/sample.mp3
```
