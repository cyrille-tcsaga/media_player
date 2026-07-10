from pathlib import Path

from PyQt6.QtCore import Qt

import ui.playlist_widget as playlist_widget_module
from core.models import MediaItem, PlaybackState
from core.player_engine import PlayerEngine
from ui.playlist_widget import PlaylistWidget
from viewmodels.player_viewmodel import PlayerViewModel

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample.mp3"
VIDEO_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample.mp4"


def test_double_click_loads_and_plays_selected_item(qapp, qtbot):
    viewmodel = PlayerViewModel(PlayerEngine())
    widget = PlaylistWidget()
    qtbot.addWidget(widget)
    widget.item_activated.connect(viewmodel.play_at)

    viewmodel.add_to_playlist(MediaItem(file_path=FIXTURE_PATH, display_name="sample.mp3"))
    widget.set_items(viewmodel.playlist_items, viewmodel.current_index)

    with qtbot.waitSignal(viewmodel.state_changed, timeout=2000):
        widget.itemDoubleClicked.emit(widget.item(0))

    assert viewmodel.state == PlaybackState.PLAYING

    # Cf. tests/test_player_engine.py : ramener explicitement à STOPPED avant
    # que le PlayerEngine sous-jacent ne sorte de portée (destruction pendant
    # PlayingState bloque indéfiniment sur ce backend).
    viewmodel.stop()
    qtbot.wait(200)


def test_delete_key_removes_selected_item(qapp, qtbot):
    viewmodel = PlayerViewModel(PlayerEngine())
    widget = PlaylistWidget()
    qtbot.addWidget(widget)
    widget.remove_requested.connect(viewmodel.remove_from_playlist)

    viewmodel.add_to_playlist(MediaItem(file_path=FIXTURE_PATH, display_name="a.mp3"))
    viewmodel.add_to_playlist(MediaItem(file_path=FIXTURE_PATH, display_name="b.mp3"))
    widget.set_items(viewmodel.playlist_items, viewmodel.current_index)
    widget.setCurrentRow(0)

    qtbot.keyClick(widget, Qt.Key.Key_Delete)

    assert [item.display_name for item in viewmodel.playlist_items] == ["b.mp3"]


def test_set_items_shows_current_item_in_bold(qapp):
    widget = PlaylistWidget()
    items = [
        MediaItem(file_path=FIXTURE_PATH, display_name="a.mp3"),
        MediaItem(file_path=FIXTURE_PATH, display_name="b.mp3"),
    ]

    widget.set_items(items, current_index=1)

    assert not widget.item(0).font().bold()
    assert widget.item(1).font().bold()


def test_audio_item_shows_audio_icon_and_never_generates_thumbnail(qapp, qtbot, monkeypatch):
    generate_called = False

    def fake_generate(*args, **kwargs):
        nonlocal generate_called
        generate_called = True
        return None

    monkeypatch.setattr(playlist_widget_module, "generate_thumbnail", fake_generate)

    widget = PlaylistWidget()
    qtbot.addWidget(widget)

    widget.set_items(
        [MediaItem(file_path=FIXTURE_PATH, display_name="sample.mp3")], current_index=None
    )

    assert not widget.item(0).icon().isNull()
    # Laisse le temps à un éventuel worker asynchrone (qui ne devrait pas
    # exister) de démarrer avant de conclure.
    qtbot.wait(200)
    assert not generate_called


def test_video_item_generates_and_caches_thumbnail_file(qapp, qtbot, tmp_path):
    widget = PlaylistWidget(thumbnail_cache_dir=tmp_path)
    qtbot.addWidget(widget)

    widget.set_items(
        [MediaItem(file_path=VIDEO_FIXTURE_PATH, display_name="sample.mp4")], current_index=None
    )

    # La miniature est générée de façon asynchrone (QThreadPool) : on attend
    # qu'un fichier apparaisse dans le cache plutôt que de bloquer le thread
    # principal (exigence de non-blocage du PRD V2 section 5).
    qtbot.waitUntil(lambda: any(tmp_path.iterdir()), timeout=5000)

    cached_files = list(tmp_path.iterdir())
    assert len(cached_files) == 1
    assert cached_files[0].suffix == ".jpg"


def test_video_item_icon_updates_after_async_generation_completes(qapp, qtbot, tmp_path):
    widget = PlaylistWidget(thumbnail_cache_dir=tmp_path)
    qtbot.addWidget(widget)

    widget.set_items(
        [MediaItem(file_path=VIDEO_FIXTURE_PATH, display_name="sample.mp4")], current_index=None
    )

    initial_icon_key = widget.item(0).icon().cacheKey()
    assert not widget.item(0).icon().isNull()

    qtbot.waitUntil(
        lambda: widget.item(0).icon().cacheKey() != initial_icon_key, timeout=5000
    )


def test_generic_icon_applied_when_thumbnail_generation_fails(qapp, qtbot, tmp_path):
    widget = PlaylistWidget(thumbnail_cache_dir=tmp_path)
    qtbot.addWidget(widget)
    missing_video = MediaItem(file_path=Path("does_not_exist.mp4"), display_name="missing.mp4")

    widget.set_items([missing_video], current_index=None)

    initial_icon_key = widget.item(0).icon().cacheKey()
    qtbot.waitUntil(
        lambda: widget.item(0).icon().cacheKey() != initial_icon_key, timeout=3000
    )

    # Échec : rien n'a été écrit dans le cache disque.
    assert not any(tmp_path.iterdir())


def test_replacing_playlist_before_generation_completes_does_not_crash(qapp, qtbot, tmp_path):
    widget = PlaylistWidget(thumbnail_cache_dir=tmp_path)
    qtbot.addWidget(widget)

    widget.set_items(
        [MediaItem(file_path=VIDEO_FIXTURE_PATH, display_name="a.mp4")], current_index=None
    )
    # Remplace immédiatement par une playlist plus courte : le worker en vol
    # référence encore l'ancienne génération/ligne.
    widget.set_items([], current_index=None)

    qtbot.wait(500)

    assert widget.count() == 0
