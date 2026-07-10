from pathlib import Path

from PyQt6.QtCore import Qt

from core.models import MediaItem, PlaybackState
from core.player_engine import PlayerEngine
from ui.controls_widget import ControlsWidget
from viewmodels.player_viewmodel import PlayerViewModel

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample.mp3"


def test_click_play_starts_playback(qapp, qtbot):
    viewmodel = PlayerViewModel(PlayerEngine())
    controls = ControlsWidget()
    qtbot.addWidget(controls)

    controls.play_requested.connect(viewmodel.play)
    controls.pause_requested.connect(viewmodel.pause)
    controls.stop_requested.connect(viewmodel.stop)

    viewmodel.load(MediaItem(file_path=FIXTURE_PATH, display_name="sample.mp3"))

    with qtbot.waitSignal(viewmodel.state_changed, timeout=2000):
        qtbot.mouseClick(controls.play_button, Qt.MouseButton.LeftButton)

    assert viewmodel.state == PlaybackState.PLAYING

    # Cf. tests/test_player_engine.py : ramener explicitement à STOPPED avant
    # que le PlayerEngine sous-jacent ne sorte de portée (destruction pendant
    # PlayingState bloque indéfiniment sur ce backend).
    viewmodel.stop()
    qtbot.wait(200)


def test_click_next_advances_playlist_and_keeps_playing(qapp, qtbot):
    viewmodel = PlayerViewModel(PlayerEngine())
    controls = ControlsWidget()
    qtbot.addWidget(controls)

    controls.previous_requested.connect(viewmodel.previous_track)
    controls.next_requested.connect(viewmodel.next_track)

    viewmodel.add_to_playlist(MediaItem(file_path=FIXTURE_PATH, display_name="a.mp3"))
    viewmodel.add_to_playlist(MediaItem(file_path=FIXTURE_PATH, display_name="b.mp3"))

    with qtbot.waitSignal(viewmodel.state_changed, timeout=2000):
        viewmodel.play_at(0)

    # Cf. tests/test_player_engine.py : qtbot.waitUntil() (busy-poll via
    # QTest.qWait) bloque indéfiniment avec ce backend Qt 6.11 FFmpeg pendant
    # une lecture en cours — on utilise waitSignal comme partout ailleurs.
    with qtbot.waitSignal(viewmodel.state_changed, timeout=2000):
        qtbot.mouseClick(controls.next_button, Qt.MouseButton.LeftButton)

    assert viewmodel.current_index == 1
    assert viewmodel.state == PlaybackState.PLAYING

    viewmodel.stop()
    qtbot.wait(200)
