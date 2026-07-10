from core.models import RepeatMode
from ui.controls_widget import ControlsWidget


def test_repeat_button_cycles_through_modes_and_emits_signal(qapp, qtbot):
    controls = ControlsWidget()
    qtbot.addWidget(controls)

    assert controls.repeat_button.text() == "Répéter: Off"

    with qtbot.waitSignal(controls.repeat_mode_changed) as blocker:
        controls.repeat_button.click()
    assert blocker.args == [RepeatMode.TRACK]
    assert controls.repeat_button.text() == "Répéter: 1"

    with qtbot.waitSignal(controls.repeat_mode_changed) as blocker:
        controls.repeat_button.click()
    assert blocker.args == [RepeatMode.PLAYLIST]
    assert controls.repeat_button.text() == "Répéter: Tout"

    with qtbot.waitSignal(controls.repeat_mode_changed) as blocker:
        controls.repeat_button.click()
    assert blocker.args == [RepeatMode.NONE]
    assert controls.repeat_button.text() == "Répéter: Off"
