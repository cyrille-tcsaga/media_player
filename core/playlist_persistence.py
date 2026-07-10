import json
from dataclasses import asdict
from pathlib import Path

from core.models import MediaItem

DEFAULT_PLAYLIST_PATH = Path.home() / ".media_player" / "playlist.json"


def save_playlist(items: list[MediaItem], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [{**asdict(item), "file_path": str(item.file_path)} for item in items]
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def load_playlist(path: Path) -> list[MediaItem]:
    items, _missing_count = load_playlist_with_missing_count(path)
    return items


def load_playlist_with_missing_count(path: Path) -> tuple[list[MediaItem], int]:
    entries = _read_entries(path)

    items = []
    missing_count = 0
    for entry in entries:
        try:
            file_path = Path(entry["file_path"])
            display_name = entry["display_name"]
            duration_ms = entry.get("duration_ms")
        except (KeyError, TypeError):
            continue

        if not file_path.exists():
            missing_count += 1
            continue

        items.append(
            MediaItem(file_path=file_path, display_name=display_name, duration_ms=duration_ms)
        )

    return items, missing_count


def _read_entries(path: Path) -> list:
    if not path.exists():
        return []

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    if not isinstance(raw, list):
        return []

    return raw
