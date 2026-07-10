from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QPushButton, QWidget

PLAYBACK_RATE_STEPS = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0)
DEFAULT_PLAYBACK_RATE = 1.0


class ControlsWidget(QWidget):
    play_requested = pyqtSignal()
    pause_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    previous_requested = pyqtSignal()
    next_requested = pyqtSignal()
    playback_rate_changed = pyqtSignal(float)

    def __init__(self) -> None:
        super().__init__()

        self.previous_button = QPushButton("Précédent")
        self.play_button = QPushButton("Play")
        self.pause_button = QPushButton("Pause")
        self.stop_button = QPushButton("Stop")
        self.next_button = QPushButton("Suivant")

        self.playback_rate_combo = QComboBox()
        for rate in PLAYBACK_RATE_STEPS:
            self.playback_rate_combo.addItem(f"{rate:g}x", rate)
        self.playback_rate_combo.setCurrentIndex(PLAYBACK_RATE_STEPS.index(DEFAULT_PLAYBACK_RATE))

        self.previous_button.clicked.connect(self.previous_requested)
        self.play_button.clicked.connect(self.play_requested)
        self.pause_button.clicked.connect(self.pause_requested)
        self.stop_button.clicked.connect(self.stop_requested)
        self.next_button.clicked.connect(self.next_requested)
        self.playback_rate_combo.currentIndexChanged.connect(self._on_playback_rate_index_changed)

        layout = QHBoxLayout(self)
        layout.addWidget(self.previous_button)
        layout.addWidget(self.play_button)
        layout.addWidget(self.pause_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.next_button)
        layout.addWidget(self.playback_rate_combo)

    def _on_playback_rate_index_changed(self, index: int) -> None:
        self.playback_rate_changed.emit(self.playback_rate_combo.itemData(index))
