from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path


@dataclass
class MediaItem:
    file_path: Path
    display_name: str
    duration_ms: int | None = None


class PlaybackState(Enum):
    STOPPED = auto()
    PLAYING = auto()
    PAUSED = auto()
    ERROR = auto()
