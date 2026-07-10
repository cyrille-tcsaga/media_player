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

    def __init__(self) -> None:
        super().__init__()
        self._state = PlaybackState.STOPPED

        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)

        self._player.playbackStateChanged.connect(self._on_playback_state_changed)
        self._player.errorOccurred.connect(self._on_error)

    @property
    def state(self) -> PlaybackState:
        return self._state

    def load(self, media_item: MediaItem) -> None:
        self._player.setSource(QUrl.fromLocalFile(str(media_item.file_path)))

    def play(self) -> None:
        self._player.play()

    def pause(self) -> None:
        self._player.pause()

    def stop(self) -> None:
        self._player.stop()

    def _on_playback_state_changed(self, qt_state: QMediaPlayer.PlaybackState) -> None:
        self._state = _QT_STATE_TO_PLAYBACK_STATE.get(qt_state, self._state)
        self.state_changed.emit(self._state)

    def _on_error(self, error: QMediaPlayer.Error, error_string: str) -> None:
        self._state = PlaybackState.ERROR
        self.state_changed.emit(self._state)
