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
