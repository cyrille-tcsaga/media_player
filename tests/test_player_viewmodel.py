from pathlib import Path

from core.models import MediaItem, PlaybackState, RepeatMode
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


def test_next_track_reloads_same_track_when_repeat_mode_is_track(qapp, qtbot):
    viewmodel = PlayerViewModel(PlayerEngine())
    viewmodel.add_to_playlist(MediaItem(file_path=FIXTURE_PATH, display_name="a.mp3"))
    viewmodel.add_to_playlist(MediaItem(file_path=FIXTURE_PATH, display_name="b.mp3"))
    viewmodel.set_repeat_mode(RepeatMode.TRACK)

    with qtbot.waitSignal(viewmodel.state_changed, timeout=2000):
        viewmodel.play_at(0)

    # RepeatMode.TRACK : next() renvoie volontairement le même index (US-091) ;
    # _navigate() doit quand même recharger au lieu de traiter ça comme un
    # blocage de bord de playlist (cf. le fix apporté dans cette story).
    with qtbot.waitSignal(viewmodel.playlist_changed, timeout=1000):
        viewmodel.next_track()

    assert viewmodel.current_index == 0
    assert viewmodel.state == PlaybackState.PLAYING

    viewmodel.stop()
    qtbot.wait(200)


def test_media_finished_restarts_same_track_when_repeat_mode_is_track(qapp, qtbot):
    engine = PlayerEngine()
    viewmodel = PlayerViewModel(engine)
    viewmodel.add_to_playlist(MediaItem(file_path=FIXTURE_PATH, display_name="a.mp3"))
    viewmodel.set_repeat_mode(RepeatMode.TRACK)

    with qtbot.waitSignal(viewmodel.state_changed, timeout=2000):
        viewmodel.play_at(0)

    with qtbot.waitSignal(viewmodel.playlist_changed, timeout=1000):
        engine.media_finished.emit()

    assert viewmodel.current_index == 0
    assert viewmodel.state == PlaybackState.PLAYING

    viewmodel.stop()
    qtbot.wait(200)


def test_load_subtitles_emits_true_for_valid_file(qapp, qtbot, tmp_path):
    srt_path = tmp_path / "subs.srt"
    srt_path.write_text("1\n00:00:00,000 --> 00:00:01,000\nHello\n", encoding="utf-8")
    viewmodel = PlayerViewModel(PlayerEngine())

    with qtbot.waitSignal(viewmodel.subtitles_loaded) as blocker:
        viewmodel.load_subtitles(srt_path)

    assert blocker.args == [True]


def test_load_subtitles_emits_false_for_malformed_file(qapp, qtbot, tmp_path):
    srt_path = tmp_path / "broken.srt"
    srt_path.write_text("not a valid srt file", encoding="utf-8")
    viewmodel = PlayerViewModel(PlayerEngine())

    with qtbot.waitSignal(viewmodel.subtitles_loaded) as blocker:
        viewmodel.load_subtitles(srt_path)

    assert blocker.args == [False]


def test_subtitle_text_follows_position_progression(qapp, qtbot, tmp_path):
    srt_path = tmp_path / "subs.srt"
    srt_path.write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nFirst\n\n2\n00:00:02,000 --> 00:00:03,000\nSecond\n",
        encoding="utf-8",
    )
    viewmodel = PlayerViewModel(PlayerEngine())
    captured = []
    viewmodel.subtitle_text_changed.connect(captured.append)

    # load_subtitles() synchronise immédiatement l'overlay avec la position
    # courante (utile si des sous-titres sont chargés en cours de lecture) :
    # se connecter au signal avant l'appel, comme le fait MainWindow.__init__
    # en usage réel, pour ne pas manquer cette émission initiale.
    viewmodel.load_subtitles(srt_path)

    viewmodel._on_position_changed(500)
    assert captured[-1] == "First"

    viewmodel._on_position_changed(1500)
    assert captured[-1] == ""

    viewmodel._on_position_changed(2500)
    assert captured[-1] == "Second"
