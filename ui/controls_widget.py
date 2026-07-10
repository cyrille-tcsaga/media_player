from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QWidget


class ControlsWidget(QWidget):
    play_requested = pyqtSignal()
    pause_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    previous_requested = pyqtSignal()
    next_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()

        self.previous_button = QPushButton("Précédent")
        self.play_button = QPushButton("Play")
        self.pause_button = QPushButton("Pause")
        self.stop_button = QPushButton("Stop")
        self.next_button = QPushButton("Suivant")

        self.previous_button.clicked.connect(self.previous_requested)
        self.play_button.clicked.connect(self.play_requested)
        self.pause_button.clicked.connect(self.pause_requested)
        self.stop_button.clicked.connect(self.stop_requested)
        self.next_button.clicked.connect(self.next_requested)

        layout = QHBoxLayout(self)
        layout.addWidget(self.previous_button)
        layout.addWidget(self.play_button)
        layout.addWidget(self.pause_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.next_button)
