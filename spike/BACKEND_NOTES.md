# Backend Notes — Qt Multimedia (spikes US-001 / US-002)

Résultats réels obtenus en exécutant `spike/video_spike.py` et `spike/audio_spike.py`
sur la machine de développement. Aucun résultat n'est supposé : tout ce qui suit a été
observé en exécutant les scripts.

## Environnement

- macOS 15.7.3 (build 24G419)
- Python 3.12.13
- PyQt6 6.11.0 / Qt 6.11.0 (`PyQt6-Qt6==6.11.1`, `PyQt6_sip==13.11.1`)
- FFmpeg (fourni par Qt Multimedia) : 7.1.3

## Backend actif

`QT_MEDIA_BACKEND` n'est pas défini par défaut sur cette machine. Au démarrage, Qt
logge :

```
qt.multimedia.ffmpeg: Using Qt multimedia with FFmpeg version 7.1.3 LGPL version 2.1 or later
```

→ **le backend actif par défaut sur macOS est le backend FFmpeg** (confirmé par ce
log, cohérent avec le comportement documenté de Qt ≥ 6.5 sur macOS). Le backend
natif macOS (`darwin`) n'a pas été testé explicitement (nécessiterait de forcer
`QT_MEDIA_BACKEND=darwin`, non fait ici).

## Formats testés

| Format | Fichier de test | Résultat | Détails |
|---|---|---|---|
| MP4 / H.264 + AAC (vidéo) | clip synthétique 320x240, 3s (`ffmpeg -f lavfi testsrc`) | **Succès** | `spike/video_spike.py` : fenêtre affichée, lecture auto, progression de `position` conforme au temps réel, aucune erreur (`errorOccurred` jamais déclenché) |
| MP4 / AV1 + Opus (vidéo) | fichier réel fourni (`docs/naza.mp4`, 190s) | **Échec (hors scope)** | Pas de décodage matériel AV1 sur cette machine (pas de puce Apple Silicon récente avec accélération AV1) ; le fallback logiciel du backend FFmpeg de Qt échoue en boucle : `Failed to get pixel format` / `Get current frame error`. AV1 n'est pas un format requis par le PRD — noté comme limitation plateforme, pas comme bug. |
| MP3 | ton sinusoïdal synthétique, 3s (`ffmpeg -f lavfi sine`) | **Succès** | `spike/audio_spike.py` : `LoadingMedia → LoadedMedia → BufferingMedia → BufferedMedia → EndOfMedia`, aucune erreur |
| MKV / H.265 (HEVC) + AAC | fichier réel remuxé sans ré-encodage depuis `docs/test.mp4` (1080x1920, 14s) | **Succès** (avec réserve, voir ci-dessous) | `spike/audio_spike.py` : média chargé et bufferisé sans erreur (`LoadingMedia → LoadedMedia → BufferingMedia → BufferedMedia`) |

## Anomalie observée (et contournée) : blocage à la destruction de `QMediaPlayer`

En testant le fichier MKV/H.265 avec `spike/audio_spike.py` (script headless,
`QCoreApplication` sans `QVideoWidget` — volontaire, car le spike audio ne doit pas
afficher d'image), la lecture audio/vidéo se déroule normalement, mais **le
processus ne se termine jamais** si l'objet `QMediaPlayer` est détruit (que ce soit
via un appel explicite à `.stop()` ou simplement parce que la variable Python sort
de portée et est garbage-collectée) pendant qu'une piste vidéo est toujours en cours
de décodage sans qu'aucun `QVideoWidget` ne lui ait été attaché.

Reproduit de façon fiable sur plusieurs exécutions consécutives (isolé via des
scripts de debug jetables, timing instrumenté). Le blocage se situe précisément
entre le retour de `app.exec()` et l'appel suivant — jamais pendant la lecture
elle-même (chargement/bufferisation/lecture se terminent tous en < 1s).

**Contournement appliqué dans `spike/audio_spike.py`** : conserver une référence
vivante sur chaque `QMediaPlayer`/`QAudioOutput` créé (liste module-level
`_KEEP_ALIVE`) jusqu'à la fin du script, et ne jamais appeler `.stop()`
explicitement. Avec ce contournement, les deux formats (MP3 et MKV/H.265)
s'exécutent proprement et le script se termine avec le code de sortie `0`.

**Implication pour la suite du projet** : à partir de la Phase 2
(`core/player_engine.py`), toujours attacher un `QVideoWidget` réel via
`setVideoOutput()` avant de lire un média contenant une piste vidéo — ne pas
reproduire le pattern « lecture vidéo sans sink attaché » utilisé ici uniquement
pour garder le spike audio headless. Si un cas d'usage nécessite un
`QMediaPlayer` réellement headless sur un fichier vidéo (peu probable dans ce
projet), prévoir de garder une référence forte sur l'objet et éviter tout arrêt
prématuré tant que la piste vidéo est active.

## Limite de l'environnement d'exécution (Claude Code)

L'affichage effectif de l'image vidéo (`video_spike.py`) n'a pas pu être vérifié
visuellement par capture d'écran dans l'environnement sandboxé de Claude Code : les
captures d'écran ne montrent que le fond d'écran, sans fenêtre ni Dock, ce qui est
cohérent avec une absence de permission macOS "Enregistrement de l'écran" pour le
shell utilisé — pas un défaut du script. La lecture réelle a été confirmée
autrement, via les signaux Qt (`window.isVisible() == True`, `mediaStatusChanged`
progressant jusqu'à `BufferedMedia`/`PlayingState`, `position` avançant en temps
réel, aucune `errorOccurred`).
