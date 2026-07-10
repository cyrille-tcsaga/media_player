from PyQt6.QtWidgets import QWidget

from ui.subtitle_overlay import SubtitleOverlay


def test_set_text_shows_widget_with_given_text(qapp, qtbot):
    parent = QWidget()
    parent.resize(400, 300)
    qtbot.addWidget(parent)
    parent.show()
    overlay = SubtitleOverlay(parent)

    overlay.set_text("Hello world")

    assert overlay.text() == "Hello world"
    assert overlay.isVisible()


def test_clear_hides_widget_and_empties_text(qapp, qtbot):
    parent = QWidget()
    parent.resize(400, 300)
    qtbot.addWidget(parent)
    parent.show()
    overlay = SubtitleOverlay(parent)
    overlay.set_text("Hello world")

    overlay.clear()

    assert overlay.text() == ""
    assert not overlay.isVisible()


def test_reposition_places_overlay_in_lower_third_of_parent(qapp, qtbot):
    parent = QWidget()
    parent.resize(400, 300)
    qtbot.addWidget(parent)
    parent.show()
    overlay = SubtitleOverlay(parent)

    overlay.set_text("Hello world")

    assert overlay.y() > parent.height() * 0.6
    assert overlay.y() + overlay.height() <= parent.height()
