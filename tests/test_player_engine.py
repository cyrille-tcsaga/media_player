from pathlib import Path

from core.models import MediaItem, PlaybackState
from core.player_engine import PlayerEngine

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample.mp3"


def test_load_then_play_sets_state_to_playing(qapp, qtbot):
    engine = PlayerEngine()
    engine.load(MediaItem(file_path=FIXTURE_PATH, display_name="sample.mp3"))

    with qtbot.waitSignal(engine.state_changed, timeout=2000):
        engine.play()

    assert engine.state == PlaybackState.PLAYING

    # Un QMediaPlayer détruit (fin de test / GC) alors qu'il est encore en
    # PlayingState bloque indéfiniment sur ce backend (Qt 6.11 FFmpeg/macOS) :
    # on le ramène explicitement à STOPPED et on laisse la boucle d'événements
    # traiter la transition avant que l'objet ne sorte de portée.
    engine.stop()
    qtbot.wait(200)


def test_pause_after_play_sets_state_to_paused(qapp, qtbot):
    engine = PlayerEngine()
    engine.load(MediaItem(file_path=FIXTURE_PATH, display_name="sample.mp3"))

    with qtbot.waitSignal(engine.state_changed, timeout=2000):
        engine.play()

    with qtbot.waitSignal(engine.state_changed, timeout=2000):
        engine.pause()

    assert engine.state == PlaybackState.PAUSED

    engine.stop()
    qtbot.wait(200)


def test_set_position_seeks_and_emits_position_changed(qapp, qtbot):
    engine = PlayerEngine()
    engine.load(MediaItem(file_path=FIXTURE_PATH, display_name="sample.mp3"))

    # setPosition() sur un média jamais joué n'émet pas positionChanged sur ce
    # backend : il faut d'abord amorcer la lecture.
    with qtbot.waitSignal(engine.state_changed, timeout=2000):
        engine.play()

    with qtbot.waitSignal(engine.position_changed, timeout=2000) as blocker:
        engine.set_position(1000)

    assert blocker.args == [1000]

    engine.stop()
    qtbot.wait(200)


def test_set_volume_updates_volume_property(qapp):
    engine = PlayerEngine()

    engine.set_volume(0.5)

    assert engine.volume == 0.5


def test_set_playback_rate_updates_playback_rate_property(qapp):
    engine = PlayerEngine()

    engine.set_playback_rate(1.5)

    assert engine.playback_rate == 1.5


def test_set_playback_rate_clamps_out_of_range_values(qapp):
    engine = PlayerEngine()

    engine.set_playback_rate(10.0)
    assert engine.playback_rate == 2.0

    engine.set_playback_rate(0.1)
    assert engine.playback_rate == 0.5


def test_load_nonexistent_file_emits_error_and_returns_to_stopped(qapp, qtbot):
    missing_path = Path(__file__).parent / "fixtures" / "does_not_exist.mp3"
    engine = PlayerEngine()

    with qtbot.waitSignal(engine.error_occurred, timeout=2000):
        engine.load(MediaItem(file_path=missing_path, display_name="does_not_exist.mp3"))
        engine.play()

    assert engine.state == PlaybackState.STOPPED


def test_media_finished_emitted_at_end_of_track(qapp, qtbot):
    engine = PlayerEngine()
    engine.load(MediaItem(file_path=FIXTURE_PATH, display_name="sample.mp3"))

    # Le fixture dure ~2s : on attend la fin réelle de la lecture pour vérifier
    # le câblage mediaStatusChanged -> media_finished bout en bout.
    with qtbot.waitSignal(engine.media_finished, timeout=5000):
        engine.play()

    engine.stop()
    qtbot.wait(200)
