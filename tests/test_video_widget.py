from PyQt6.QtWidgets import QPushButton

from ui.video_widget import VideoWidget


def test_video_widget_creates_subtitle_overlay(qapp, qtbot):
    widget = VideoWidget()
    qtbot.addWidget(widget)

    assert widget.subtitle_overlay.parentWidget() is widget


def test_resizing_video_widget_repositions_subtitle_overlay(qapp, qtbot):
    widget = VideoWidget()
    qtbot.addWidget(widget)
    widget.show()
    widget.resize(400, 300)
    widget.subtitle_overlay.set_text("Hello")
    initial_y = widget.subtitle_overlay.y()

    widget.resize(400, 600)
    qapp.processEvents()

    assert widget.subtitle_overlay.y() != initial_y


def test_set_overlay_panel_anchors_full_width_at_bottom(qapp, qtbot):
    widget = VideoWidget()
    qtbot.addWidget(widget)
    widget.show()
    widget.resize(400, 300)

    panel = QPushButton("Panel")
    widget.set_overlay_panel(panel)

    assert panel.x() == 0
    assert panel.width() == widget.width()
    assert panel.y() + panel.height() == widget.height()
    assert panel.height() <= widget.height()


def test_resizing_video_widget_repositions_overlay_panel(qapp, qtbot):
    widget = VideoWidget()
    qtbot.addWidget(widget)
    widget.show()
    widget.resize(400, 300)

    panel = QPushButton("Panel")
    widget.set_overlay_panel(panel)
    initial_position = (panel.x(), panel.y(), panel.width(), panel.height())

    widget.resize(800, 600)
    qapp.processEvents()

    assert (panel.x(), panel.y(), panel.width(), panel.height()) != initial_position
    assert panel.width() == widget.width()
    assert panel.y() + panel.height() == widget.height()


def test_set_overlay_panel_none_stops_repositioning(qapp, qtbot):
    widget = VideoWidget()
    qtbot.addWidget(widget)
    widget.show()
    widget.resize(400, 300)

    panel = QPushButton("Panel")
    widget.set_overlay_panel(panel)
    widget.set_overlay_panel(None)
    position_before_resize = (panel.x(), panel.y(), panel.width(), panel.height())

    widget.resize(800, 600)
    qapp.processEvents()

    # Plus de référence à ce widget : aucun repositionnement automatique.
    assert (panel.x(), panel.y(), panel.width(), panel.height()) == position_before_resize
