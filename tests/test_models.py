from pathlib import Path

from core.models import MediaItem, PlaybackState


def test_media_item_fields():
    item = MediaItem(file_path=Path("song.mp3"), display_name="song.mp3")

    assert item.file_path == Path("song.mp3")
    assert item.display_name == "song.mp3"
    assert item.duration_ms is None


def test_playback_state_members():
    assert PlaybackState.STOPPED
    assert PlaybackState.PLAYING
    assert PlaybackState.PAUSED
    assert PlaybackState.ERROR
