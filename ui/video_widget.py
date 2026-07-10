from PyQt6.QtCore import Qt
from PyQt6.QtMultimediaWidgets import QVideoWidget

from ui.subtitle_overlay import SubtitleOverlay


class VideoWidget(QVideoWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        self.subtitle_overlay = SubtitleOverlay(self)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.subtitle_overlay.reposition()
