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
