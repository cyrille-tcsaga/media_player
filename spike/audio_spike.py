"""Spike exploratoire : valide la lecture audio MP3 et détecte le backend Qt Multimedia actif.

Usage: python spike/audio_spike.py chemin/vers/fichier.mp3 [chemin/vers/fichier_h265.mkv]

Sans interface graphique : QMediaPlayer + QAudioOutput, boucle d'événements minimale.
Le second argument (optionnel) est un fichier MKV/H.265 dont le résultat de lecture
(succès ou QMediaPlayer.Error) est simplement noté en console.

Script jetable, isolé du reste du projet (pas d'architecture MVVM, pas de tests).
"""

import os
import sys

from PyQt6.QtCore import QCoreApplication, QTimer, QUrl
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer

PLAYBACK_TIMEOUT_MS = 4000

# Garde une référence sur chaque QMediaPlayer/QAudioOutput pour toute la durée du
# script : les détruire (GC ou fin de fonction) pendant qu'une piste vidéo est en
# cours de décodage sans QVideoWidget attaché bloque indéfiniment sur ce backend
# (Qt 6.11 FFmpeg/macOS) — cf. spike/BACKEND_NOTES.md.
_KEEP_ALIVE = []


def log_active_backend() -> None:
    backend = os.environ.get("QT_MEDIA_BACKEND")
    if backend:
        print(f"Backend Qt Multimedia actif (QT_MEDIA_BACKEND) : {backend}")
    else:
        print("Backend Qt Multimedia actif : backend par défaut")


def try_play(app: QCoreApplication, media_path: str, label: str) -> str:
    """Joue le fichier pendant PLAYBACK_TIMEOUT_MS et renvoie 'succès' ou le message d'erreur."""
    result = {"status": "succès"}

    player = QMediaPlayer()
    audio_output = QAudioOutput()
    player.setAudioOutput(audio_output)
    _KEEP_ALIVE.append((player, audio_output))

    def on_error(error, error_string):
        result["status"] = f"échec ({error.name}: {error_string})"
        app.quit()

    player.errorOccurred.connect(on_error)
    player.mediaStatusChanged.connect(
        lambda status: print(f"[{label}] mediaStatusChanged: {status.name}")
    )

    player.setSource(QUrl.fromLocalFile(media_path))
    player.play()

    QTimer.singleShot(PLAYBACK_TIMEOUT_MS, app.quit)
    app.exec()

    # Ne pas appeler player.stop() ici : sur ce backend (Qt 6.11 FFmpeg/macOS),
    # stop() bloque indéfiniment quand la source a une piste vidéo sans QVideoWidget
    # attaché (cf. spike/BACKEND_NOTES.md). Laisser le GC/la fin de process nettoyer.
    return result["status"]


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python spike/audio_spike.py chemin/vers/fichier.mp3 [chemin/vers/fichier_h265.mkv]")
        sys.exit(1)

    mp3_path = sys.argv[1]
    mkv_path = sys.argv[2] if len(sys.argv) > 2 else None

    app = QCoreApplication(sys.argv)

    log_active_backend()

    print(f"Test MP3 : {mp3_path}")
    mp3_result = try_play(app, mp3_path, "MP3")
    print(f"Résultat MP3 : {mp3_result}")

    if mkv_path:
        print(f"Test MKV/H.265 : {mkv_path}")
        mkv_result = try_play(app, mkv_path, "MKV/H.265")
        print(f"Résultat MKV/H.265 : {mkv_result}")
    else:
        print("Aucun fichier MKV/H.265 fourni — test ignoré.")


if __name__ == "__main__":
    main()
