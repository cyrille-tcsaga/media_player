from enum import Enum
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

RESOURCES_DIR = Path(__file__).parent / "resources"


class Theme(Enum):
    DARK = "dark"
    LIGHT = "light"


def detect_system_theme() -> Theme:
    # QStyleHints.colorScheme() (Qt >= 6.5) rapporte la préférence sombre/claire
    # du système de façon cross-platform (Windows, macOS, certains
    # environnements Linux) — pas seulement macOS comme suggéré initialement.
    # Vérifié empiriquement sur cette machine de dev (Windows) : reflète bien
    # le réglage clair/sombre du système. Repli sur DARK si l'API ne rapporte
    # rien d'exploitable (ColorScheme.Unknown) ou si aucune QApplication
    # n'existe encore.
    app = QApplication.instance()
    if app is None:
        return Theme.DARK

    color_scheme = app.styleHints().colorScheme()
    if color_scheme == Qt.ColorScheme.Light:
        return Theme.LIGHT
    return Theme.DARK


def load_stylesheet(theme: Theme) -> str:
    path = RESOURCES_DIR / f"{theme.value}.qss"
    return path.read_text(encoding="utf-8")


def apply_theme(app: QApplication, theme: Theme) -> None:
    app.setStyleSheet(load_stylesheet(theme))
