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
