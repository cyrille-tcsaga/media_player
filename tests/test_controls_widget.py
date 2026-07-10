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


def test_shuffle_button_toggles_and_emits_signal(qapp, qtbot):
    controls = ControlsWidget()
    qtbot.addWidget(controls)

    assert controls.shuffle_button.text() == "Aléatoire: Off"
    assert not controls.shuffle_button.isChecked()

    with qtbot.waitSignal(controls.shuffle_enabled_changed) as blocker:
        controls.shuffle_button.click()
    assert blocker.args == [True]
    assert controls.shuffle_button.text() == "Aléatoire: On"

    with qtbot.waitSignal(controls.shuffle_enabled_changed) as blocker:
        controls.shuffle_button.click()
    assert blocker.args == [False]
    assert controls.shuffle_button.text() == "Aléatoire: Off"
