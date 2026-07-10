# Test fixtures

- `sample.mp3` — 2 secondes de silence, mono, 44.1kHz. Utilisé par `tests/test_player_engine.py`
  pour valider `PlayerEngine` sans dépendre d'un fichier audio réel.
- `sample.mp4` — 2 secondes de mire de test (`testsrc`), 160x120, 5 fps. Utilisé par
  `tests/test_thumbnail_generator.py` pour valider `generate_thumbnail()` sur une vraie
  vidéo sans dépendre d'un fichier réel volumineux.

Régénération :

```bash
ffmpeg -f lavfi -i "anullsrc=r=44100:cl=mono" -t 2 -c:a libmp3lame -q:a 9 tests/fixtures/sample.mp3
ffmpeg -f lavfi -i "testsrc=duration=2:size=160x120:rate=5" -pix_fmt yuv420p -c:v libx264 -y tests/fixtures/sample.mp4
```
