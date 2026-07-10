# Lecteur Média PyQt6

![CI](https://github.com/OWNER/REPO/actions/workflows/ci.yml/badge.svg)

Lecteur audio/vidéo local, mono-utilisateur, construit avec Python et PyQt6/QtMultimedia.

## Prérequis

- Python 3.11+ (testé avec Python 3.12)

## Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Packaging

Un exécutable autonome (sans installation Python requise) peut être généré avec [PyInstaller](https://pyinstaller.org/) :

```bash
pip install -r requirements-dev.txt
pyinstaller media_player.spec
```

L'exécutable est produit dans `dist/media_player/` :
- **Windows** : `dist/media_player/media_player.exe`
- **macOS** : `dist/media_player/media_player.app`
- **Linux** : `dist/media_player/media_player`

`media_player.spec` est unique et partagé entre les trois plateformes (le bloc `BUNDLE` qui produit le `.app` macOS ne s'active que si le build tourne sur `darwin`).

**Point de vigilance FFmpeg (cf. PRD section 10) :** QtMultimedia dépend d'un plugin FFmpeg chargé dynamiquement à l'exécution (`Qt6/plugins/multimedia/ffmpegmediaplugin`). Les hooks PyInstaller pour PyQt6 l'embarquent automatiquement, mais il faut le vérifier après chaque build plutôt que de supposer que la présence de FFmpeg sur la machine de build suffit :
- **Windows/Linux** : vérifier que `ffmpegmediaplugin.dll` (ou `.so`) est bien présent sous `dist/media_player/_internal/PyQt6/Qt6/plugins/multimedia/` (ou équivalent selon le mode `--onefile`/`--onedir`).
- **macOS** : lancer `otool -L` sur le binaire final (`dist/media_player/media_player.app/Contents/MacOS/media_player`) pour confirmer que les bibliothèques FFmpeg sont liées depuis l'intérieur du bundle `.app`, pas depuis un chemin de la machine de build.

**Limite de vérification actuelle :** ce build a été généré et testé (lancement de l'exécutable, présence de `ffmpegmediaplugin.dll`) sur Windows uniquement — l'environnement de développement de ce projet ne dispose pas d'une machine macOS. La vérification `otool -L` du bundle `.app` reste à faire sur macOS avant packaging final.

## Documentation

Voir `docs/PRD_Lecteur_Media_PyQt6.md` et `docs/USER_STORIES_Lecteur_Media_PyQt6.md` pour les spécifications et le backlog du projet.
