from PyQt6.QtCore import QEvent, QPointF
from PyQt6.QtGui import QEnterEvent

from ui.overlay_panel import OverlayPanel


def test_set_overlay_mode_toggles_dynamic_property(qapp, qtbot):
    panel = OverlayPanel()
    qtbot.addWidget(panel)

    assert panel.property("overlayMode") in (None, False)

    panel.set_overlay_mode(True)
    assert panel.property("overlayMode") is True

    panel.set_overlay_mode(False)
    assert panel.property("overlayMode") is False


def test_enter_and_leave_emit_hover_signals(qapp, qtbot):
    panel = OverlayPanel()
    qtbot.addWidget(panel)

    with qtbot.waitSignal(panel.mouse_entered, timeout=1000):
        enter_event = QEnterEvent(QPointF(0, 0), QPointF(0, 0), QPointF(0, 0))
        qapp.sendEvent(panel, enter_event)

    with qtbot.waitSignal(panel.mouse_left, timeout=1000):
        leave_event = QEvent(QEvent.Type.Leave)
        qapp.sendEvent(panel, leave_event)
