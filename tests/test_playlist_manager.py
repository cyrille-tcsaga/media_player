from pathlib import Path

from core.models import MediaItem, RepeatMode
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


def test_default_repeat_mode_is_none():
    manager = PlaylistManager()
    assert manager.repeat_mode == RepeatMode.NONE


def test_repeat_track_next_reloads_same_item_instead_of_advancing():
    manager = PlaylistManager(repeat_mode=RepeatMode.TRACK)
    manager.add(_item("a.mp3"))
    manager.add(_item("b.mp3"))

    assert manager.next().display_name == "a.mp3"
    assert manager.next().display_name == "a.mp3"
    assert manager.current_index == 0


def test_repeat_track_previous_stays_on_same_item():
    manager = PlaylistManager(repeat_mode=RepeatMode.TRACK)
    manager.add(_item("a.mp3"))
    manager.add(_item("b.mp3"))
    manager.select(1)

    assert manager.previous().display_name == "b.mp3"
    assert manager.current_index == 1


def test_repeat_playlist_next_wraps_to_first_item_at_end():
    manager = PlaylistManager(repeat_mode=RepeatMode.PLAYLIST)
    manager.add(_item("a.mp3"))
    manager.add(_item("b.mp3"))
    manager.select(1)

    assert manager.next().display_name == "a.mp3"
    assert manager.current_index == 0


def test_repeat_playlist_previous_wraps_to_last_item_at_start():
    manager = PlaylistManager(repeat_mode=RepeatMode.PLAYLIST)
    manager.add(_item("a.mp3"))
    manager.add(_item("b.mp3"))

    assert manager.previous().display_name == "b.mp3"
    assert manager.current_index == 1


def test_set_repeat_mode_changes_mode_at_runtime():
    manager = PlaylistManager()
    manager.add(_item("a.mp3"))
    manager.add(_item("b.mp3"))
    manager.select(1)

    manager.set_repeat_mode(RepeatMode.PLAYLIST)

    assert manager.next().display_name == "a.mp3"


def test_shuffle_disabled_by_default():
    manager = PlaylistManager()
    assert manager.shuffle_enabled is False


def test_shuffle_next_visits_each_item_exactly_once_per_cycle():
    names = ["a.mp3", "b.mp3", "c.mp3", "d.mp3", "e.mp3"]
    manager = PlaylistManager()
    for name in names:
        manager.add(_item(name))

    manager.set_shuffle_enabled(True)

    visited = [manager.next().display_name for _ in range(len(names))]

    assert sorted(visited) == sorted(names)
    assert len(set(visited)) == len(names)


def test_shuffle_order_is_computed_once_not_on_every_next_call(monkeypatch):
    import core.playlist_manager as playlist_manager_module

    manager = PlaylistManager()
    for name in ("a.mp3", "b.mp3", "c.mp3"):
        manager.add(_item(name))
    manager.set_shuffle_enabled(True)

    call_count = 0
    original_shuffle = playlist_manager_module.random.shuffle

    def counting_shuffle(seq):
        nonlocal call_count
        call_count += 1
        original_shuffle(seq)

    monkeypatch.setattr(playlist_manager_module.random, "shuffle", counting_shuffle)

    for _ in range(3):
        manager.next()

    assert call_count == 0


def test_disabling_shuffle_restores_linear_navigation():
    manager = PlaylistManager()
    manager.add(_item("a.mp3"))
    manager.add(_item("b.mp3"))
    manager.add(_item("c.mp3"))

    manager.set_shuffle_enabled(True)
    manager.set_shuffle_enabled(False)

    assert manager.next().display_name == "b.mp3"
    assert manager.next().display_name == "c.mp3"
    assert manager.next().display_name == "c.mp3"


def test_shuffle_with_repeat_playlist_reshuffles_on_new_cycle():
    names = ["a.mp3", "b.mp3", "c.mp3"]
    manager = PlaylistManager(repeat_mode=RepeatMode.PLAYLIST)
    for name in names:
        manager.add(_item(name))
    manager.set_shuffle_enabled(True)

    first_cycle = [manager.next().display_name for _ in range(len(names))]
    assert sorted(first_cycle) == sorted(names)

    # Un appel de plus doit boucler (RepeatMode.PLAYLIST) sur un nouveau tirage
    # plutôt que de bloquer (comportement NONE) ou planter.
    fourth = manager.next()
    assert fourth is not None
    assert fourth.display_name in names


def test_shuffle_with_repeat_track_ignores_shuffle_and_reloads_same_item():
    manager = PlaylistManager(repeat_mode=RepeatMode.TRACK)
    manager.add(_item("a.mp3"))
    manager.add(_item("b.mp3"))
    manager.set_shuffle_enabled(True)

    assert manager.next().display_name == "a.mp3"
    assert manager.next().display_name == "a.mp3"
    assert manager.current_index == 0
