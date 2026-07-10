"""Spike exploratoire : valide que QMediaPlayer + QVideoWidget lisent un MP4 local.

Usage: python spike/video_spike.py chemin/vers/fichier.mp4

Script jetable, isolé du reste du projet (pas d'architecture MVVM, pas de tests).
"""

import os
import sys

from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QApplication, QMainWindow


def log_active_backend() -> None:
    backend = os.environ.get("QT_MEDIA_BACKEND")
    if backend:
        print(f"Backend Qt Multimedia actif (QT_MEDIA_BACKEND) : {backend}")
    else:
        print("Backend Qt Multimedia actif : backend par défaut")


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python spike/video_spike.py chemin/vers/fichier.mp4")
        sys.exit(1)

    video_path = sys.argv[1]

    app = QApplication(sys.argv)

    log_active_backend()

    window = QMainWindow()
    window.setWindowTitle("Video Spike")
    window.resize(960, 540)

    video_widget = QVideoWidget()
    window.setCentralWidget(video_widget)

    player = QMediaPlayer()
    player.setVideoOutput(video_widget)
    player.setSource(QUrl.fromLocalFile(video_path))

    window.show()
    player.play()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
