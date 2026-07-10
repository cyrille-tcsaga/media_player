import json
from dataclasses import asdict
from pathlib import Path

from core.models import MediaItem


def save_playlist(items: list[MediaItem], path: Path) -> None:
    payload = [{**asdict(item), "file_path": str(item.file_path)} for item in items]
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def load_playlist(path: Path) -> list[MediaItem]:
    if not path.exists():
        return []

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    if not isinstance(raw, list):
        return []

    items = []
    for entry in raw:
        try:
            file_path = Path(entry["file_path"])
            display_name = entry["display_name"]
            duration_ms = entry.get("duration_ms")
        except (KeyError, TypeError):
            continue

        if not file_path.exists():
            continue

        items.append(
            MediaItem(file_path=file_path, display_name=display_name, duration_ms=duration_ms)
        )

    return items
