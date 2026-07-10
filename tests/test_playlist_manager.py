from pathlib import Path

from core.models import MediaItem
from core.playlist_manager import PlaylistManager
from core.playlist_persistence import load_playlist


def _item(name: str) -> MediaItem:
    return MediaItem(file_path=Path(f"/media/{name}"), display_name=name)


def test_add_first_item_becomes_current():
    manager = PlaylistManager()
    manager.add(_item("a.mp3"))
    assert manager.current.display_name == "a.mp3"
    assert manager.current_index == 0


def test_add_subsequent_items_keeps_current_unchanged():
    manager = PlaylistManager()
    manager.add(_item("a.mp3"))
    manager.add(_item("b.mp3"))
    assert manager.current.display_name == "a.mp3"
    assert len(manager.items) == 2


def test_next_advances_and_blocks_at_last_item():
    manager = PlaylistManager()
    manager.add(_item("a.mp3"))
    manager.add(_item("b.mp3"))
    assert manager.next().display_name == "b.mp3"
    assert manager.next().display_name == "b.mp3"


def test_previous_retreats_and_blocks_at_first_item():
    manager = PlaylistManager()
    manager.add(_item("a.mp3"))
    manager.add(_item("b.mp3"))
    manager.select(1)
    assert manager.previous().display_name == "a.mp3"
    assert manager.previous().display_name == "a.mp3"


def test_next_and_previous_on_empty_playlist_return_none():
    manager = PlaylistManager()
    assert manager.next() is None
    assert manager.previous() is None
    assert manager.current is None


def test_select_jumps_to_given_index():
    manager = PlaylistManager()
    manager.add(_item("a.mp3"))
    manager.add(_item("b.mp3"))
    manager.add(_item("c.mp3"))
    assert manager.select(2).display_name == "c.mp3"
    assert manager.current_index == 2


def test_select_out_of_range_is_noop_and_returns_none():
    manager = PlaylistManager()
    manager.add(_item("a.mp3"))
    assert manager.select(5) is None
    assert manager.current.display_name == "a.mp3"


def test_remove_before_current_shifts_current_index_down():
    manager = PlaylistManager()
    manager.add(_item("a.mp3"))
    manager.add(_item("b.mp3"))
    manager.add(_item("c.mp3"))
    manager.select(2)
    manager.remove(0)
    assert manager.current.display_name == "c.mp3"
    assert manager.current_index == 1


def test_remove_current_item_falls_back_to_previous_index():
    manager = PlaylistManager()
    manager.add(_item("a.mp3"))
    manager.add(_item("b.mp3"))
    manager.select(1)
    manager.remove(1)
    assert manager.current.display_name == "a.mp3"


def test_remove_last_remaining_item_clears_current():
    manager = PlaylistManager()
    manager.add(_item("a.mp3"))
    manager.remove(0)
    assert manager.current is None
    assert manager.items == []


def test_remove_invalid_index_is_noop():
    manager = PlaylistManager()
    manager.add(_item("a.mp3"))
    manager.remove(5)
    assert len(manager.items) == 1


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample.mp3"


def test_add_saves_playlist_when_path_is_configured(tmp_path):
    playlist_path = tmp_path / "playlist.json"
    manager = PlaylistManager(playlist_path=playlist_path)

    manager.add(MediaItem(file_path=FIXTURE_PATH, display_name="a.mp3"))

    saved = load_playlist(playlist_path)
    assert [item.display_name for item in saved] == ["a.mp3"]


def test_remove_saves_playlist_when_path_is_configured(tmp_path):
    playlist_path = tmp_path / "playlist.json"
    manager = PlaylistManager(playlist_path=playlist_path)
    manager.add(MediaItem(file_path=FIXTURE_PATH, display_name="a.mp3"))
    manager.add(MediaItem(file_path=FIXTURE_PATH, display_name="b.mp3"))

    manager.remove(0)

    saved = load_playlist(playlist_path)
    assert [item.display_name for item in saved] == ["b.mp3"]
