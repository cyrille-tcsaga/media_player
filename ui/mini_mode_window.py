from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from ui.video_widget import VideoWidget
from viewmodels.player_viewmodel import PlayerViewModel


class MiniModeWindow(QWidget):
    closed = pyqtSignal()

    def __init__(self, viewmodel: PlayerViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Lecteur Média — Mini-mode")
        # Widget rendu comme une fenêtre indépendante (même avec un parent, pour
        # un nettoyage Qt propre à la destruction) et toujours au premier plan.
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        self.resize(320, 220)

        # S'abonne au PlayerViewModel de MainWindow : aucune nouvelle instance
        # de PlayerEngine n'est créée (cf. US-100), seule la cible de rendu
        # vidéo change (set_video_output), pour rester cohérent avec le
        # pattern MVVM du PRD V1.
        self.viewmodel = viewmodel

        self.video_widget = VideoWidget()
        self.play_button = QPushButton("Play")
        self.pause_button = QPushButton("Pause")
        self.close_button = QPushButton("Retour")

        self.play_button.clicked.connect(self.viewmodel.play)
        self.pause_button.clicked.connect(self.viewmodel.pause)
        self.close_button.clicked.connect(self.closed)

        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.pause_button)
        controls_layout.addWidget(self.close_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.video_widget, stretch=1)
        layout.addLayout(controls_layout)

    def closeEvent(self, event) -> None:
        self.closed.emit()
        super().closeEvent(event)
