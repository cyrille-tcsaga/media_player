from PyQt6.QtCore import QObject, pyqtSignal

from core.models import MediaItem, PlaybackState
from core.player_engine import PlayerEngine


class PlayerViewModel(QObject):
    state_changed = pyqtSignal(PlaybackState)

    def __init__(self, engine: PlayerEngine | None = None) -> None:
        super().__init__()
        self._engine = engine if engine is not None else PlayerEngine()
        self._engine.state_changed.connect(self.state_changed)

    @property
    def state(self) -> PlaybackState:
        return self._engine.state

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
