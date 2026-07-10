from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QPushButton, QWidget

from core.models import RepeatMode

PLAYBACK_RATE_STEPS = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0)
DEFAULT_PLAYBACK_RATE = 1.0

# Cycle affiché par le bouton "Répéter". Le libellé fait office d'icône
# différenciée en l'absence d'un pipeline d'assets icônes dans ce projet.
REPEAT_MODE_CYCLE = (RepeatMode.NONE, RepeatMode.TRACK, RepeatMode.PLAYLIST)
REPEAT_MODE_LABELS = {
    RepeatMode.NONE: "Répéter: Off",
    RepeatMode.TRACK: "Répéter: 1",
    RepeatMode.PLAYLIST: "Répéter: Tout",
}


class ControlsWidget(QWidget):
    play_requested = pyqtSignal()
    pause_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    previous_requested = pyqtSignal()
    next_requested = pyqtSignal()
    playback_rate_changed = pyqtSignal(float)
    repeat_mode_changed = pyqtSignal(RepeatMode)
    shuffle_enabled_changed = pyqtSignal(bool)

    def __init__(self) -> None:
        super().__init__()

        self._repeat_mode = RepeatMode.NONE

        self.previous_button = QPushButton("Précédent")
        self.play_button = QPushButton("Play")
        self.pause_button = QPushButton("Pause")
        self.stop_button = QPushButton("Stop")
        self.next_button = QPushButton("Suivant")
        self.repeat_button = QPushButton(REPEAT_MODE_LABELS[self._repeat_mode])
        self.shuffle_button = QPushButton("Aléatoire: Off")
        self.shuffle_button.setCheckable(True)

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
        self.repeat_button.clicked.connect(self._cycle_repeat_mode)
        self.shuffle_button.toggled.connect(self._on_shuffle_toggled)

        layout = QHBoxLayout(self)
        layout.addWidget(self.previous_button)
        layout.addWidget(self.play_button)
        layout.addWidget(self.pause_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.next_button)
        layout.addWidget(self.playback_rate_combo)
        layout.addWidget(self.repeat_button)
        layout.addWidget(self.shuffle_button)

    def _on_playback_rate_index_changed(self, index: int) -> None:
        self.playback_rate_changed.emit(self.playback_rate_combo.itemData(index))

    def _cycle_repeat_mode(self) -> None:
        next_position = (REPEAT_MODE_CYCLE.index(self._repeat_mode) + 1) % len(REPEAT_MODE_CYCLE)
        self._repeat_mode = REPEAT_MODE_CYCLE[next_position]
        self.repeat_button.setText(REPEAT_MODE_LABELS[self._repeat_mode])
        self.repeat_mode_changed.emit(self._repeat_mode)

    def _on_shuffle_toggled(self, checked: bool) -> None:
        self.shuffle_button.setText(f"Aléatoire: {'On' if checked else 'Off'}")
        self.shuffle_enabled_changed.emit(checked)
