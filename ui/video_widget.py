from PyQt6.QtCore import Qt
from PyQt6.QtMultimediaWidgets import QVideoWidget


class VideoWidget(QVideoWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
