from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QVBoxLayout, QWidget


class OverlayPanel(QWidget):
    # Regroupe progress/controls/volume/playlist en un seul bloc, capable de
    # basculer entre ancrage normal (bas de la fenêtre) et superposition
    # semi-transparente sur la vidéo en plein écran (même instances de
    # widgets, jamais dupliquées — seul le parent/positionnement change).
    mouse_entered = pyqtSignal()
    mouse_left = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(0, 0, 0, 0)

    def set_overlay_mode(self, enabled: bool) -> None:
        # unpolish()/polish() requis pour que Qt réévalue le sélecteur QSS basé
        # sur la propriété dynamique après setProperty() (cf. ui/resources/*.qss).
        self.setProperty("overlayMode", enabled)
        self.style().unpolish(self)
        self.style().polish(self)

    def enterEvent(self, event) -> None:
        super().enterEvent(event)
        self.mouse_entered.emit()

    def leaveEvent(self, event) -> None:
        super().leaveEvent(event)
        self.mouse_left.emit()
