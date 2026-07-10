from PyQt6.QtCore import QObject, QUrl, pyqtSignal
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer

from core.models import MediaItem, PlaybackState

_QT_STATE_TO_PLAYBACK_STATE = {
    QMediaPlayer.PlaybackState.StoppedState: PlaybackState.STOPPED,
    QMediaPlayer.PlaybackState.PlayingState: PlaybackState.PLAYING,
    QMediaPlayer.PlaybackState.PausedState: PlaybackState.PAUSED,
}

_QT_ERROR_TO_MESSAGE = {
    QMediaPlayer.Error.ResourceError: (
        "Impossible d'accéder au fichier média : il est introuvable ou endommagé."
    ),
    QMediaPlayer.Error.FormatError: "Ce format de fichier n'est pas pris en charge.",
    QMediaPlayer.Error.NetworkError: "Une erreur réseau a interrompu la lecture.",
    QMediaPlayer.Error.AccessDeniedError: "Accès refusé à ce fichier média.",
}
_DEFAULT_ERROR_MESSAGE = "Une erreur inattendue est survenue pendant la lecture."

MIN_PLAYBACK_RATE = 0.5
MAX_PLAYBACK_RATE = 2.0


class PlayerEngine(QObject):
    state_changed = pyqtSignal(PlaybackState)
    position_changed = pyqtSignal(int)
    duration_changed = pyqtSignal(int)
    media_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

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
        self._player.mediaStatusChanged.connect(self._on_media_status_changed)

    @property
    def state(self) -> PlaybackState:
        return self._state

    def load(self, media_item: MediaItem) -> None:
        # Appeler setSource() pendant PlayingState bloque indéfiniment sur ce
        # backend (Qt 6.11 FFmpeg) — même famille de bug que le closeEvent
        # documenté dans main_window.py. On stoppe explicitement avant de
        # changer de source (utile pour next/previous pendant la lecture).
        self._player.stop()
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

    @property
    def volume(self) -> float:
        return self._audio_output.volume()

    def set_volume(self, volume: float) -> None:
        self._audio_output.setVolume(volume)

    @property
    def playback_rate(self) -> float:
        return self._player.playbackRate()

    def set_playback_rate(self, rate: float) -> None:
        # Choix explicite : on clampe plutôt que de rejeter une valeur hors
        # plage (0.5x-2.0x, cf. F18 du PRD V2), pour qu'un contrôle UI à bornes
        # ne puisse jamais lever d'exception ni laisser le lecteur dans un état
        # incohérent.
        clamped_rate = max(MIN_PLAYBACK_RATE, min(MAX_PLAYBACK_RATE, rate))
        self._player.setPlaybackRate(clamped_rate)

    def _on_playback_state_changed(self, qt_state: QMediaPlayer.PlaybackState) -> None:
        self._state = _QT_STATE_TO_PLAYBACK_STATE.get(qt_state, self._state)
        self.state_changed.emit(self._state)

    def _on_error(self, error: QMediaPlayer.Error, error_string: str) -> None:
        self._state = PlaybackState.ERROR
        self.state_changed.emit(self._state)
        message = _QT_ERROR_TO_MESSAGE.get(error, _DEFAULT_ERROR_MESSAGE)
        self.error_occurred.emit(message)

        # Revient explicitement à STOPPED (cf. US-050) : self._player.stop() ne
        # réémet pas toujours playbackStateChanged ici, car le lecteur n'a
        # souvent jamais atteint PlayingState (ex. fichier introuvable), donc
        # Qt ne considère pas stop() comme un changement d'état réel.
        self._player.stop()
        self._state = PlaybackState.STOPPED
        self.state_changed.emit(self._state)

    def _on_position_changed(self, position_ms: int) -> None:
        self.position_changed.emit(int(position_ms))

    def _on_duration_changed(self, duration_ms: int) -> None:
        self.duration_changed.emit(int(duration_ms))

    def _on_media_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.media_finished.emit()
