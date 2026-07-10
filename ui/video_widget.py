from PyQt6.QtCore import Qt
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import QWidget

from ui.subtitle_overlay import SubtitleOverlay


class VideoWidget(QVideoWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        self.subtitle_overlay = SubtitleOverlay(self)
        self._overlay_controls: QWidget | None = None

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.subtitle_overlay.reposition()
        self._reposition_overlay_controls()

    def set_overlay_controls(self, controls_widget: QWidget | None) -> None:
        # US-130 : centre par-dessus la vidéo le ControlsWidget existant,
        # reparenté ici par MainWindow plutôt que dupliqué dans un second
        # widget (cf. note de la story). None retire la référence une fois
        # que l'appelant a reparenté le widget ailleurs (sortie du plein écran).
        self._overlay_controls = controls_widget
        self._reposition_overlay_controls()

    def _reposition_overlay_controls(self) -> None:
        widget = self._overlay_controls
        if widget is None:
            return
        widget.adjustSize()
        x = (self.width() - widget.width()) // 2
        y = (self.height() - widget.height()) // 2
        widget.move(max(0, x), max(0, y))
