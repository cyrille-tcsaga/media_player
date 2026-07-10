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
