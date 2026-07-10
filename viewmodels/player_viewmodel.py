from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

from core.models import MediaItem, PlaybackState, RepeatMode
from core.player_engine import PlayerEngine
from core.playlist_manager import PlaylistManager


class PlayerViewModel(QObject):
    state_changed = pyqtSignal(PlaybackState)
    position_changed = pyqtSignal(int)
    duration_changed = pyqtSignal(int)
    playlist_changed = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(
        self, engine: PlayerEngine | None = None, playlist_path: Path | None = None
    ) -> None:
        super().__init__()
        self._engine = engine if engine is not None else PlayerEngine()
        self._playlist = PlaylistManager(playlist_path=playlist_path)
        self._position = 0
        self._duration = 0

        self._engine.state_changed.connect(self.state_changed)
        self._engine.position_changed.connect(self._on_position_changed)
        self._engine.duration_changed.connect(self._on_duration_changed)
        self._engine.media_finished.connect(self._on_media_finished)
        self._engine.error_occurred.connect(self.error_occurred)

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

    @property
    def playlist_items(self) -> list[MediaItem]:
        return self._playlist.items

    @property
    def current_index(self) -> int | None:
        return self._playlist.current_index

    def add_to_playlist(self, media_item: MediaItem) -> None:
        self._playlist.add(media_item)
        self.playlist_changed.emit()

    def remove_from_playlist(self, index: int) -> None:
        self._playlist.remove(index)
        self.playlist_changed.emit()

    def play_at(self, index: int) -> None:
        media_item = self._playlist.select(index)
        if media_item is None:
            return
        self.load(media_item)
        self.play()
        self.playlist_changed.emit()

    def next_track(self) -> None:
        self._navigate(self._playlist.next)

    def previous_track(self) -> None:
        self._navigate(self._playlist.previous)

    def _navigate(self, move, *, force_play: bool = False) -> None:
        previous_index = self._playlist.current_index
        media_item = move()
        if media_item is None:
            return
        # PlaylistManager bloque aux bords en RepeatMode.NONE (pas de bouclage) :
        # si l'index n'a pas bougé, on est déjà en début/fin de playlist, donc on
        # ne fait rien plutôt que de relancer le même morceau depuis le début. En
        # RepeatMode.TRACK, next()/previous() renvoient volontairement le même
        # index à chaque appel (US-091) : ce n'est pas un blocage de bord, il faut
        # bien recharger.
        if (
            self._playlist.repeat_mode != RepeatMode.TRACK
            and self._playlist.current_index == previous_index
        ):
            return

        # Choix explicite (non spécifié par le PRD) : si la lecture était en pause
        # (ou stoppée), changer de piste la charge sans relancer la lecture — sinon
        # on reprend automatiquement, pour ne pas surprendre l'utilisateur en train
        # d'écouter. force_play=True court-circuite ce choix pour l'enchaînement
        # automatique en fin de piste (_on_media_finished), où l'on veut toujours
        # continuer la lecture.
        was_playing = force_play or self.state == PlaybackState.PLAYING
        self.load(media_item)
        if was_playing:
            self.play()
        self.playlist_changed.emit()

    def _on_media_finished(self) -> None:
        self._navigate(self._playlist.next, force_play=True)

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

    def set_playback_rate(self, rate: float) -> None:
        self._engine.set_playback_rate(rate)

    def set_repeat_mode(self, mode: RepeatMode) -> None:
        self._playlist.set_repeat_mode(mode)

    def _on_position_changed(self, position_ms: int) -> None:
        self._position = position_ms
        self.position_changed.emit(position_ms)

    def _on_duration_changed(self, duration_ms: int) -> None:
        self._duration = duration_ms
        self.duration_changed.emit(duration_ms)
