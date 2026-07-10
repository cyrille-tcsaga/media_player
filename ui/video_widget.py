from PyQt6.QtCore import Qt
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import QWidget

from ui.subtitle_overlay import SubtitleOverlay

# Hauteur maximale (proportion de la vidéo) occupée par le panneau overlay
# (progress/controls/volume/playlist) en plein écran, pour ne pas laisser la
# playlist envahir tout l'écran.
OVERLAY_PANEL_HEIGHT_RATIO = 0.45


class VideoWidget(QVideoWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        self.subtitle_overlay = SubtitleOverlay(self)
        self._overlay_panel: QWidget | None = None

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.subtitle_overlay.reposition()
        self._reposition_overlay_panel()

    def set_overlay_panel(self, panel: QWidget | None) -> None:
        # Ancre par-dessus la vidéo le panneau existant (progress/controls/
        # volume/playlist), reparenté ici par MainWindow plutôt que dupliqué
        # dans de nouveaux widgets. None retire la référence une fois que
        # l'appelant a reparenté le panneau ailleurs (sortie du plein écran).
        self._overlay_panel = panel
        self._reposition_overlay_panel()

    def _reposition_overlay_panel(self) -> None:
        panel = self._overlay_panel
        if panel is None:
            return
        height = max(1, int(self.height() * OVERLAY_PANEL_HEIGHT_RATIO))
        panel.resize(self.width(), height)
        panel.move(0, self.height() - height)
