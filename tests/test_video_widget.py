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


def test_set_overlay_controls_centers_widget_over_video(qapp, qtbot):
    widget = VideoWidget()
    qtbot.addWidget(widget)
    widget.show()
    widget.resize(400, 300)

    controls = QPushButton("Controls")
    widget.set_overlay_controls(controls)

    expected_x = (widget.width() - controls.width()) // 2
    expected_y = (widget.height() - controls.height()) // 2
    assert controls.x() == max(0, expected_x)
    assert controls.y() == max(0, expected_y)


def test_resizing_video_widget_repositions_overlay_controls(qapp, qtbot):
    widget = VideoWidget()
    qtbot.addWidget(widget)
    widget.show()
    widget.resize(400, 300)

    controls = QPushButton("Controls")
    widget.set_overlay_controls(controls)
    initial_position = (controls.x(), controls.y())

    widget.resize(800, 600)
    qapp.processEvents()

    assert (controls.x(), controls.y()) != initial_position


def test_set_overlay_controls_none_stops_repositioning(qapp, qtbot):
    widget = VideoWidget()
    qtbot.addWidget(widget)
    widget.show()
    widget.resize(400, 300)

    controls = QPushButton("Controls")
    widget.set_overlay_controls(controls)
    widget.set_overlay_controls(None)
    position_before_resize = (controls.x(), controls.y())

    widget.resize(800, 600)
    qapp.processEvents()

    # Plus de référence à ce widget : aucun repositionnement automatique.
    assert (controls.x(), controls.y()) == position_before_resize
