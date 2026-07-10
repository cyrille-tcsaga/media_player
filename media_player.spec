# -*- mode: python ; coding: utf-8 -*-
#
# US-060 : build via `pyinstaller media_player.spec`.
# Les hooks PyInstaller pour PyQt6 embarquent automatiquement le plugin
# QtMultimedia FFmpeg (Qt6/plugins/multimedia/ffmpegmediaplugin.dll sur
# Windows, .dylib équivalent sur macOS) : vérifier après build qu'il est
# bien présent dans le dossier `dist/` généré, et pas seulement sur la
# machine de build (sur macOS, `otool -L` sur le binaire final).
#
# US-110 : bundle aussi le binaire CLI `ffmpeg` (distinct du plugin
# QtMultimedia ci-dessus) via `binaries=[...]`, requis par
# core/thumbnail_generator.py (US-111) qui l'invoque en sous-processus pour
# extraire une frame de prévisualisation — indépendamment de la lecture Qt.
# Résolu dynamiquement via le PATH de la machine de build (shutil.which)
# plutôt que codé en dur, pour rester portable ; à défaut, définir la
# variable d'environnement FFMPEG_BINARY_PATH avant de lancer pyinstaller.
import os
import shutil
import sys

ffmpeg_path = os.environ.get("FFMPEG_BINARY_PATH") or shutil.which("ffmpeg")
if ffmpeg_path:
    binaries = [(ffmpeg_path, ".")]
else:
    print(
        "AVERTISSEMENT (US-110) : binaire ffmpeg introuvable (ni sur le PATH, "
        "ni via FFMPEG_BINARY_PATH) — l'exécutable packagé n'embarquera pas "
        "ffmpeg, et la génération de miniatures (US-111) échouera à l'exécution.",
        file=sys.stderr,
    )
    binaries = []

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='media_player',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='media_player',
)

if sys.platform == "darwin":
    # PyInstaller n'ajoute ce bloc automatiquement que lorsqu'il génère un
    # spec par défaut sur macOS ; comme ce fichier est versionné et réutilisé
    # tel quel sur toutes les plateformes, on le garde explicite ici.
    app = BUNDLE(
        coll,
        name="media_player.app",
        icon=None,
        bundle_identifier="com.cyrilletoumi.media-player",
    )
