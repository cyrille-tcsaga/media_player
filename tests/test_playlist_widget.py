from pathlib import Path

from PyQt6.QtCore import Qt

from core.models import MediaItem, PlaybackState
from core.player_engine import PlayerEngine
from ui.playlist_widget import PlaylistWidget
from viewmodels.player_viewmodel import PlayerViewModel

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample.mp3"


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
