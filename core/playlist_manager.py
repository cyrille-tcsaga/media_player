from pathlib import Path

from core.models import MediaItem, RepeatMode
from core.playlist_persistence import save_playlist


class PlaylistManager:
    def __init__(
        self, playlist_path: Path | None = None, repeat_mode: RepeatMode = RepeatMode.NONE
    ) -> None:
        self._items: list[MediaItem] = []
        self._current_index: int | None = None
        self._playlist_path = playlist_path
        self._repeat_mode = repeat_mode

    @property
    def repeat_mode(self) -> RepeatMode:
        return self._repeat_mode

    def set_repeat_mode(self, mode: RepeatMode) -> None:
        self._repeat_mode = mode

    @property
    def items(self) -> list[MediaItem]:
        return list(self._items)

    @property
    def current_index(self) -> int | None:
        return self._current_index

    @property
    def current(self) -> MediaItem | None:
        if self._current_index is None:
            return None
        return self._items[self._current_index]

    def add(self, media_item: MediaItem) -> None:
        self._items.append(media_item)
        if self._current_index is None:
            self._current_index = 0
        self._save()

    def remove(self, index: int) -> None:
        if not (0 <= index < len(self._items)):
            return

        del self._items[index]

        if not self._items:
            self._current_index = None
        elif self._current_index is not None:
            if index < self._current_index:
                self._current_index -= 1
            elif index == self._current_index:
                self._current_index = min(self._current_index, len(self._items) - 1)

        self._save()

    def select(self, index: int) -> MediaItem | None:
        if not (0 <= index < len(self._items)):
            return None
        self._current_index = index
        return self.current

    def next(self) -> MediaItem | None:
        if self._current_index is None:
            return None

        if self._repeat_mode == RepeatMode.TRACK:
            # Recharge le même élément au lieu d'avancer (F13 du PRD V2).
            return self.current

        if self._current_index + 1 < len(self._items):
            self._current_index += 1
        elif self._repeat_mode == RepeatMode.PLAYLIST:
            self._current_index = 0
        # RepeatMode.NONE : bloque au dernier élément, comportement V1 inchangé
        # (pas de bouclage).
        return self.current

    def previous(self) -> MediaItem | None:
        if self._current_index is None:
            return None

        if self._repeat_mode == RepeatMode.TRACK:
            # Choix explicite (non spécifié par le PRD, par symétrie avec next()) :
            # reste sur la piste courante plutôt que de reculer.
            return self.current

        if self._current_index > 0:
            self._current_index -= 1
        elif self._repeat_mode == RepeatMode.PLAYLIST:
            self._current_index = len(self._items) - 1
        # RepeatMode.NONE : bloque au premier élément, comportement V1 inchangé
        # (pas de bouclage).
        return self.current

    def _save(self) -> None:
        if self._playlist_path is not None:
            save_playlist(self._items, self._playlist_path)
