from PyQt6.QtCore import QObject, QUrl, pyqtSignal
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer

from core.models import MediaItem, PlaybackState

_QT_STATE_TO_PLAYBACK_STATE = {
    QMediaPlayer.PlaybackState.StoppedState: PlaybackState.STOPPED,
    QMediaPlayer.PlaybackState.PlayingState: PlaybackState.PLAYING,
    QMediaPlayer.PlaybackState.PausedState: PlaybackState.PAUSED,
}


class PlayerEngine(QObject):
    state_changed = pyqtSignal(PlaybackState)
    position_changed = pyqtSignal(int)
    duration_changed = pyqtSignal(int)

    def __init__(self) -> None:
        super().__init__()
        self._state = PlaybackState.STOPPED

        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)

        self._player.playbackStateChanged.connect(self._on_playback_state_changed)
        self._player.errorOccurred.connect(self._on_error)
        self._player.positionChanged.connect(self._on_position_changed)
        self._player.durationChanged.connect(self._on_duration_changed)

    @property
    def state(self) -> PlaybackState:
        return self._state

    def load(self, media_item: MediaItem) -> None:
        self._player.setSource(QUrl.fromLocalFile(str(media_item.file_path)))

    # Pas de type hint sur video_output : éviter d'importer un module widget dans core/.
    def set_video_output(self, video_output) -> None:
        self._player.setVideoOutput(video_output)

    def play(self) -> None:
        self._player.play()

    def pause(self) -> None:
        self._player.pause()

    def stop(self) -> None:
        self._player.stop()

    def set_position(self, position_ms: int) -> None:
        self._player.setPosition(position_ms)

    def _on_playback_state_changed(self, qt_state: QMediaPlayer.PlaybackState) -> None:
        self._state = _QT_STATE_TO_PLAYBACK_STATE.get(qt_state, self._state)
        self.state_changed.emit(self._state)

    def _on_error(self, error: QMediaPlayer.Error, error_string: str) -> None:
        self._state = PlaybackState.ERROR
        self.state_changed.emit(self._state)

    def _on_position_changed(self, position_ms: int) -> None:
        self.position_changed.emit(int(position_ms))

    def _on_duration_changed(self, duration_ms: int) -> None:
        self.duration_changed.emit(int(duration_ms))
