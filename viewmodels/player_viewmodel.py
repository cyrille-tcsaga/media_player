from PyQt6.QtCore import QObject, pyqtSignal

from core.models import MediaItem, PlaybackState
from core.player_engine import PlayerEngine


class PlayerViewModel(QObject):
    state_changed = pyqtSignal(PlaybackState)
    position_changed = pyqtSignal(int)
    duration_changed = pyqtSignal(int)

    def __init__(self, engine: PlayerEngine | None = None) -> None:
        super().__init__()
        self._engine = engine if engine is not None else PlayerEngine()
        self._position = 0
        self._duration = 0

        self._engine.state_changed.connect(self.state_changed)
        self._engine.position_changed.connect(self._on_position_changed)
        self._engine.duration_changed.connect(self._on_duration_changed)

    @property
    def state(self) -> PlaybackState:
        return self._engine.state

    @property
    def position(self) -> int:
        return self._position

    @property
    def duration(self) -> int:
        return self._duration

    @property
    def volume(self) -> int:
        return round(self._engine.volume * 100)

    def load(self, media_item: MediaItem) -> None:
        self._engine.load(media_item)

    def set_video_output(self, video_output) -> None:
        self._engine.set_video_output(video_output)

    def play(self) -> None:
        self._engine.play()

    def pause(self) -> None:
        self._engine.pause()

    def stop(self) -> None:
        self._engine.stop()

    def set_position(self, position_ms: int) -> None:
        self._engine.set_position(position_ms)

    def set_volume(self, volume_percent: int) -> None:
        self._engine.set_volume(volume_percent / 100)

    def _on_position_changed(self, position_ms: int) -> None:
        self._position = position_ms
        self.position_changed.emit(position_ms)

    def _on_duration_changed(self, duration_ms: int) -> None:
        self._duration = duration_ms
        self.duration_changed.emit(duration_ms)
