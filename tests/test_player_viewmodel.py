from pathlib import Path

from core.models import MediaItem, PlaybackState
from core.player_engine import PlayerEngine
from viewmodels.player_viewmodel import PlayerViewModel

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample.mp3"


def test_add_to_playlist_appends_item_and_emits_playlist_changed(qapp, qtbot):
    viewmodel = PlayerViewModel(PlayerEngine())

    with qtbot.waitSignal(viewmodel.playlist_changed, timeout=1000):
        viewmodel.add_to_playlist(MediaItem(file_path=FIXTURE_PATH, display_name="a.mp3"))

    assert [item.display_name for item in viewmodel.playlist_items] == ["a.mp3"]
    assert viewmodel.current_index == 0


def test_remove_from_playlist_removes_item(qapp, qtbot):
    viewmodel = PlayerViewModel(PlayerEngine())
    viewmodel.add_to_playlist(MediaItem(file_path=FIXTURE_PATH, display_name="a.mp3"))

    with qtbot.waitSignal(viewmodel.playlist_changed, timeout=1000):
        viewmodel.remove_from_playlist(0)

    assert viewmodel.playlist_items == []


def test_play_at_invalid_index_is_noop(qapp):
    viewmodel = PlayerViewModel(PlayerEngine())

    viewmodel.play_at(0)

    assert viewmodel.state == PlaybackState.STOPPED


def test_next_track_resumes_playback_when_was_playing(qapp, qtbot):
    viewmodel = PlayerViewModel(PlayerEngine())
    viewmodel.add_to_playlist(MediaItem(file_path=FIXTURE_PATH, display_name="a.mp3"))
    viewmodel.add_to_playlist(MediaItem(file_path=FIXTURE_PATH, display_name="b.mp3"))

    with qtbot.waitSignal(viewmodel.state_changed, timeout=2000):
        viewmodel.play_at(0)

    # Cf. tests/test_player_engine.py : qtbot.waitUntil() (busy-poll via
    # QTest.qWait) bloque indéfiniment avec ce backend Qt 6.11 FFmpeg pendant
    # une lecture en cours — on utilise waitSignal comme partout ailleurs.
    with qtbot.waitSignal(viewmodel.state_changed, timeout=2000):
        viewmodel.next_track()

    assert viewmodel.current_index == 1
    assert viewmodel.state == PlaybackState.PLAYING

    viewmodel.stop()
    qtbot.wait(200)


def test_next_track_does_not_resume_playback_when_was_paused(qapp, qtbot):
    viewmodel = PlayerViewModel(PlayerEngine())
    viewmodel.add_to_playlist(MediaItem(file_path=FIXTURE_PATH, display_name="a.mp3"))
    viewmodel.add_to_playlist(MediaItem(file_path=FIXTURE_PATH, display_name="b.mp3"))

    with qtbot.waitSignal(viewmodel.state_changed, timeout=2000):
        viewmodel.play_at(0)
    with qtbot.waitSignal(viewmodel.state_changed, timeout=2000):
        viewmodel.pause()

    # load() appelle stop() avant de changer de source (cf. player_engine.py),
    # ce qui émet déjà state_changed : pas besoin de relancer play().
    with qtbot.waitSignal(viewmodel.state_changed, timeout=2000):
        viewmodel.next_track()

    assert viewmodel.current_index == 1
    assert viewmodel.state != PlaybackState.PLAYING

    viewmodel.stop()
    qtbot.wait(200)


def test_next_track_at_last_item_is_noop(qapp, qtbot):
    viewmodel = PlayerViewModel(PlayerEngine())
    viewmodel.add_to_playlist(MediaItem(file_path=FIXTURE_PATH, display_name="a.mp3"))
    viewmodel.add_to_playlist(MediaItem(file_path=FIXTURE_PATH, display_name="b.mp3"))

    with qtbot.waitSignal(viewmodel.state_changed, timeout=2000):
        viewmodel.play_at(1)

    viewmodel.next_track()
    qtbot.wait(200)

    assert viewmodel.current_index == 1
    assert viewmodel.state == PlaybackState.PLAYING

    viewmodel.stop()
    qtbot.wait(200)


def test_previous_track_at_first_item_is_noop(qapp):
    viewmodel = PlayerViewModel(PlayerEngine())
    viewmodel.add_to_playlist(MediaItem(file_path=FIXTURE_PATH, display_name="a.mp3"))

    viewmodel.previous_track()

    assert viewmodel.current_index == 0
    assert viewmodel.state == PlaybackState.STOPPED


def test_next_track_on_empty_playlist_is_noop(qapp):
    viewmodel = PlayerViewModel(PlayerEngine())

    viewmodel.next_track()

    assert viewmodel.current_index is None
    assert viewmodel.state == PlaybackState.STOPPED


def test_media_finished_auto_advances_to_next_track(qapp, qtbot):
    # On simule directement le signal PlayerEngine.media_finished plutôt que
    # d'attendre la fin réelle des ~2s du fixture : laisser tourner une boucle
    # d'événements imbriquée pendant plusieurs secondes de décodage réel bloque
    # indéfiniment ce backend Qt 6.11 FFmpeg (même famille que les autres
    # blocages déjà documentés dans ce fichier et player_engine.py).
    engine = PlayerEngine()
    viewmodel = PlayerViewModel(engine)
    viewmodel.add_to_playlist(MediaItem(file_path=FIXTURE_PATH, display_name="a.mp3"))
    viewmodel.add_to_playlist(MediaItem(file_path=FIXTURE_PATH, display_name="b.mp3"))

    with qtbot.waitSignal(viewmodel.state_changed, timeout=2000):
        viewmodel.play_at(0)

    with qtbot.waitSignal(viewmodel.playlist_changed, timeout=1000):
        engine.media_finished.emit()

    assert viewmodel.current_index == 1
    assert viewmodel.state == PlaybackState.PLAYING

    viewmodel.stop()
    qtbot.wait(200)


def test_media_finished_on_last_track_stops_without_looping(qapp, qtbot):
    engine = PlayerEngine()
    viewmodel = PlayerViewModel(engine)
    viewmodel.add_to_playlist(MediaItem(file_path=FIXTURE_PATH, display_name="a.mp3"))

    with qtbot.waitSignal(viewmodel.state_changed, timeout=2000):
        viewmodel.play_at(0)

    # Dernier (et unique) morceau : pas de bouclage (cohérent avec US-040), donc
    # aucun rechargement ni relance de lecture ne doit se produire ici.
    engine.media_finished.emit()

    assert viewmodel.current_index == 0

    # Cf. tests/test_player_engine.py : ramener explicitement à STOPPED avant
    # que le PlayerEngine sous-jacent ne sorte de portée (destruction pendant
    # PlayingState bloque indéfiniment sur ce backend).
    viewmodel.stop()
    qtbot.wait(200)
