import json
from pathlib import Path
from typing import Any

DEFAULT_SETTINGS_PATH = Path.home() / ".media_player" / "settings.json"

# Anticipe le "dernier volume" mentionné en PRD V2 section 7 : la clé existe
# dès maintenant, même si sa lecture/écriture n'est pas câblée dans cette story.
DEFAULT_SETTINGS: dict[str, Any] = {
    "volume": 100,
}


class SettingsManager:
    def __init__(self, settings_path: Path = DEFAULT_SETTINGS_PATH) -> None:
        self._path = settings_path
        self._values = self._load()

    def get(self, key: str, default: Any = None) -> Any:
        if key in self._values:
            return self._values[key]
        return default

    def set(self, key: str, value: Any) -> None:
        self._values[key] = value
        self._save()

    def _load(self) -> dict[str, Any]:
        values = dict(DEFAULT_SETTINGS)
        if not self._path.exists():
            return values

        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return values

        if isinstance(raw, dict):
            values.update(raw)
        return values

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(self._values, indent=2, ensure_ascii=False), encoding="utf-8"
        )
