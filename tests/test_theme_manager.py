from PyQt6.QtCore import Qt

from ui.theme_manager import Theme, apply_theme, detect_system_theme, load_stylesheet


def test_load_stylesheet_returns_non_empty_content_for_each_theme():
    assert load_stylesheet(Theme.DARK).strip()
    assert load_stylesheet(Theme.LIGHT).strip()


def test_apply_theme_sets_application_stylesheet(qapp):
    apply_theme(qapp, Theme.DARK)
    assert qapp.styleSheet() == load_stylesheet(Theme.DARK)

    apply_theme(qapp, Theme.LIGHT)
    assert qapp.styleSheet() == load_stylesheet(Theme.LIGHT)


def test_detect_system_theme_reflects_light_color_scheme(qapp, monkeypatch):
    monkeypatch.setattr(qapp.styleHints(), "colorScheme", lambda: Qt.ColorScheme.Light)
    assert detect_system_theme() == Theme.LIGHT


def test_detect_system_theme_reflects_dark_color_scheme(qapp, monkeypatch):
    monkeypatch.setattr(qapp.styleHints(), "colorScheme", lambda: Qt.ColorScheme.Dark)
    assert detect_system_theme() == Theme.DARK


def test_detect_system_theme_defaults_to_dark_for_unknown_color_scheme(qapp, monkeypatch):
    monkeypatch.setattr(qapp.styleHints(), "colorScheme", lambda: Qt.ColorScheme.Unknown)
    assert detect_system_theme() == Theme.DARK
