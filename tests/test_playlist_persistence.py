from pathlib import Path

from core.models import MediaItem
from core.playlist_persistence import load_playlist, save_playlist

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample.mp3"


def test_save_then_load_round_trip(tmp_path):
    playlist_path = tmp_path / "playlist.json"
    items = [
        MediaItem(file_path=FIXTURE_PATH, display_name="a.mp3", duration_ms=2000),
        MediaItem(file_path=FIXTURE_PATH, display_name="b.mp3"),
    ]

    save_playlist(items, playlist_path)
    loaded = load_playlist(playlist_path)

    assert loaded == items


def test_load_missing_file_returns_empty_list(tmp_path):
    playlist_path = tmp_path / "does_not_exist.json"

    assert load_playlist(playlist_path) == []


def test_load_corrupted_json_returns_empty_list(tmp_path):
    playlist_path = tmp_path / "playlist.json"
    playlist_path.write_text("{not valid json", encoding="utf-8")

    assert load_playlist(playlist_path) == []


def test_load_filters_entries_with_missing_media_file(tmp_path):
    playlist_path = tmp_path / "playlist.json"
    save_playlist(
        [
            MediaItem(file_path=FIXTURE_PATH, display_name="a.mp3"),
            MediaItem(
                file_path=Path("does_not_exist_anymore.mp3"), display_name="gone.mp3"
            ),
        ],
        playlist_path,
    )

    loaded = load_playlist(playlist_path)

    assert [item.display_name for item in loaded] == ["a.mp3"]
