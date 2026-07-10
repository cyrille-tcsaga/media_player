from core.models import MediaItem


class PlaylistManager:
    def __init__(self) -> None:
        self._items: list[MediaItem] = []
        self._current_index: int | None = None

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

    def select(self, index: int) -> MediaItem | None:
        if not (0 <= index < len(self._items)):
            return None
        self._current_index = index
        return self.current

    def next(self) -> MediaItem | None:
        # Bloque au dernier élément pour le MVP : pas de bouclage (le mode répétition est V2/F13).
        if self._current_index is None:
            return None
        if self._current_index + 1 < len(self._items):
            self._current_index += 1
        return self.current

    def previous(self) -> MediaItem | None:
        if self._current_index is None:
            return None
        if self._current_index > 0:
            self._current_index -= 1
        return self.current
