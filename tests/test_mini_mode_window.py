from pathlib import Path

from PyQt6.QtCore import Qt

from core.models import MediaItem, PlaybackState
from core.player_engine import PlayerEngine
from ui.mini_mode_window import MiniModeWindow
from viewmodels.player_viewmodel import PlayerViewModel

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample.mp3"


def test_stays_on_top_window_flag_is_set(qapp):
    viewmodel = PlayerViewModel(PlayerEngine())
    window = MiniModeWindow(viewmodel)

    assert bool(window.windowFlags() & Qt.WindowType.WindowStaysOnTopHint)


def test_play_button_calls_viewmodel_play(qapp, qtbot):
    viewmodel = PlayerViewModel(PlayerEngine())
    viewmodel.load(MediaItem(file_path=FIXTURE_PATH, display_name="sample.mp3"))
    window = MiniModeWindow(viewmodel)
    qtbot.addWidget(window)

    with qtbot.waitSignal(viewmodel.state_changed, timeout=2000):
        qtbot.mouseClick(window.play_button, Qt.MouseButton.LeftButton)

    assert viewmodel.state == PlaybackState.PLAYING

    viewmodel.stop()
    qtbot.wait(200)


def test_pause_button_calls_viewmodel_pause(qapp, qtbot):
    viewmodel = PlayerViewModel(PlayerEngine())
    viewmodel.load(MediaItem(file_path=FIXTURE_PATH, display_name="sample.mp3"))
    window = MiniModeWindow(viewmodel)
    qtbot.addWidget(window)

    with qtbot.waitSignal(viewmodel.state_changed, timeout=2000):
        viewmodel.play()
    with qtbot.waitSignal(viewmodel.state_changed, timeout=2000):
        qtbot.mouseClick(window.pause_button, Qt.MouseButton.LeftButton)

    assert viewmodel.state == PlaybackState.PAUSED

    viewmodel.stop()
    qtbot.wait(200)


def test_close_button_emits_closed_signal(qapp, qtbot):
    viewmodel = PlayerViewModel(PlayerEngine())
    window = MiniModeWindow(viewmodel)
    qtbot.addWidget(window)

    with qtbot.waitSignal(window.closed, timeout=1000):
        qtbot.mouseClick(window.close_button, Qt.MouseButton.LeftButton)
