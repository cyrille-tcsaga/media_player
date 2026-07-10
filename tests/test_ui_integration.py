from pathlib import Path

from PyQt6.QtCore import Qt

from core.models import MediaItem, PlaybackState
from core.player_engine import PlayerEngine
from ui.controls_widget import ControlsWidget
from ui.main_window import MainWindow
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


def test_mini_mode_action_updates_state_visible_from_main_window(qapp, qtbot, tmp_path):
    # US-101 : MiniModeWindow et MainWindow s'abonnent au même PlayerViewModel
    # (pas de PlayerEngine séparé) — une action côté mini-mode doit donc être
    # immédiatement visible via le même viewmodel, sans câblage supplémentaire.
    window = MainWindow(
        playlist_path=tmp_path / "playlist.json",
        settings_path=tmp_path / "settings.json",
        thumbnail_cache_dir=tmp_path / "thumbnails",
    )
    qtbot.addWidget(window)
    window.viewmodel.load(MediaItem(file_path=FIXTURE_PATH, display_name="a.mp3"))

    window._enter_mini_mode()

    with qtbot.waitSignal(window.viewmodel.state_changed, timeout=2000):
        qtbot.mouseClick(window.mini_mode_window.play_button, Qt.MouseButton.LeftButton)

    assert window.viewmodel.state == PlaybackState.PLAYING

    window.viewmodel.stop()
    qtbot.wait(200)


def test_subtitle_overlay_follows_position_progression(qapp, qtbot, tmp_path):
    # US-122 : simule une progression de position (sans lecture réelle, cf.
    # notes sur qtbot.waitUntil ailleurs dans ce fichier) et vérifie que le
    # texte affiché par SubtitleOverlay correspond à l'entrée SRT attendue à
    # différents instants.
    srt_path = tmp_path / "subs.srt"
    srt_path.write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nFirst\n\n2\n00:00:02,000 --> 00:00:03,000\nSecond\n",
        encoding="utf-8",
    )
    window = MainWindow(
        playlist_path=tmp_path / "playlist.json",
        settings_path=tmp_path / "settings.json",
        thumbnail_cache_dir=tmp_path / "thumbnails",
    )
    qtbot.addWidget(window)

    window.viewmodel.load_subtitles(srt_path)

    window.viewmodel._on_position_changed(500)
    assert window.video_widget.subtitle_overlay.text() == "First"

    window.viewmodel._on_position_changed(1500)
    assert window.video_widget.subtitle_overlay.text() == ""

    window.viewmodel._on_position_changed(2500)
    assert window.video_widget.subtitle_overlay.text() == "Second"
