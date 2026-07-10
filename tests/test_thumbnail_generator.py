import subprocess
from pathlib import Path

import core.thumbnail_generator as thumbnail_generator_module
from core.models import MediaItem
from core.thumbnail_generator import generate_thumbnail

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample.mp4"


def test_generate_thumbnail_succeeds_on_real_video_file(tmp_path):
    item = MediaItem(file_path=FIXTURE_PATH, display_name="sample.mp4")

    result = generate_thumbnail(item, tmp_path)

    assert result is not None
    assert result.exists()
    assert result.stat().st_size > 0


def test_generate_thumbnail_returns_none_for_nonexistent_file(tmp_path):
    item = MediaItem(file_path=Path("does_not_exist.mp4"), display_name="missing.mp4")

    assert generate_thumbnail(item, tmp_path) is None


def test_generate_thumbnail_returns_none_on_timeout(tmp_path, monkeypatch):
    def raise_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="ffmpeg", timeout=10)

    monkeypatch.setattr(thumbnail_generator_module.subprocess, "run", raise_timeout)

    item = MediaItem(file_path=FIXTURE_PATH, display_name="sample.mp4")

    assert generate_thumbnail(item, tmp_path) is None


def test_generate_thumbnail_uses_cache_on_second_call(tmp_path, monkeypatch):
    item = MediaItem(file_path=FIXTURE_PATH, display_name="sample.mp4")

    first_result = generate_thumbnail(item, tmp_path)
    assert first_result is not None

    call_count = 0
    original_run = thumbnail_generator_module.subprocess.run

    def counting_run(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return original_run(*args, **kwargs)

    monkeypatch.setattr(thumbnail_generator_module.subprocess, "run", counting_run)

    second_result = generate_thumbnail(item, tmp_path)

    assert second_result == first_result
    # Le cache disque évite tout nouvel appel à ffmpeg au second passage.
    assert call_count == 0
