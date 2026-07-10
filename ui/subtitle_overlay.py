from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QWidget

# Marge basse relative à la hauteur du parent, pour rester dans le tiers
# inférieur de la zone vidéo sans coller au bord.
BOTTOM_MARGIN_RATIO = 0.08
MIN_BOTTOM_MARGIN_PX = 8


class SubtitleOverlay(QLabel):
    # Ce widget ne connaît rien du contenu des sous-titres ni de la
    # synchronisation temporelle (cf. US-121) : il expose uniquement une API
    # d'affichage de texte. La logique de synchronisation vit dans
    # PlayerViewModel (US-122).

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
        # Fond semi-transparent derrière le texte pour rester lisible sur un
        # fond vidéo variable (plutôt qu'un contour/ombre portée sur le texte).
        self.setStyleSheet(
            "QLabel {"
            "  color: white;"
            "  background-color: rgba(0, 0, 0, 160);"
            "  padding: 6px 12px;"
            "  border-radius: 4px;"
            "  font-size: 16px;"
            "}"
        )
        self.hide()

    def set_text(self, text: str) -> None:
        self.setText(text)
        self.adjustSize()
        self.reposition()
        self.show()
        self.raise_()

    def clear(self) -> None:
        super().clear()
        self.hide()

    def reposition(self) -> None:
        parent = self.parentWidget()
        if parent is None:
            return

        margin_bottom = max(MIN_BOTTOM_MARGIN_PX, int(parent.height() * BOTTOM_MARGIN_RATIO))
        x = (parent.width() - self.width()) // 2
        y = parent.height() - self.height() - margin_bottom
        self.move(max(0, x), max(0, y))
