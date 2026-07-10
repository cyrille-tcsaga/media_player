import random
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
        self._shuffle_enabled = False
        self._shuffle_order: list[int] = []
        self._shuffle_position = -1

    @property
    def repeat_mode(self) -> RepeatMode:
        return self._repeat_mode

    def set_repeat_mode(self, mode: RepeatMode) -> None:
        self._repeat_mode = mode

    @property
    def shuffle_enabled(self) -> bool:
        return self._shuffle_enabled

    def set_shuffle_enabled(self, enabled: bool) -> None:
        self._shuffle_enabled = enabled
        if enabled:
            self._reshuffle()
        else:
            self._shuffle_order = []
            self._shuffle_position = -1

    def _reshuffle(self) -> None:
        # random.shuffle() implémente Fisher-Yates. Un seul tirage à
        # l'activation (ou à chaque nouveau cycle complet en
        # RepeatMode.PLAYLIST), jamais recalculé à chaque next() — garantit
        # qu'aucune piste ne repasse avant que toutes les autres n'aient été
        # jouées (pas de shuffle naïf à répétitions rapprochées).
        indices = list(range(len(self._items)))
        random.shuffle(indices)
        self._shuffle_order = indices
        # Position -1 : le prochain next()/previous() démarre un cycle complet
        # et neuf. La piste en cours de lecture au moment de l'activation
        # continue de jouer normalement mais n'est pas comptée dans ce nouveau
        # tirage (choix explicite, non spécifié par le PRD — nécessaire pour
        # garantir qu'un cycle de N appels à next() visite bien les N pistes
        # exactement une fois, quel que soit l'index couramment en lecture).
        self._shuffle_position = -1

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
        if self._shuffle_enabled:
            self._reshuffle()
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

        if self._shuffle_enabled:
            self._reshuffle()

        self._save()

    def select(self, index: int) -> MediaItem | None:
        if not (0 <= index < len(self._items)):
            return None
        self._current_index = index
        if self._shuffle_enabled:
            self._shuffle_position = self._shuffle_order.index(self._current_index)
        return self.current

    def next(self) -> MediaItem | None:
        if self._current_index is None:
            return None

        if self._repeat_mode == RepeatMode.TRACK:
            # Recharge le même élément au lieu d'avancer (F13 du PRD V2).
            return self.current

        if self._shuffle_enabled:
            return self._shuffle_step(direction=1)

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

        if self._shuffle_enabled:
            return self._shuffle_step(direction=-1)

        if self._current_index > 0:
            self._current_index -= 1
        elif self._repeat_mode == RepeatMode.PLAYLIST:
            self._current_index = len(self._items) - 1
        # RepeatMode.NONE : bloque au premier élément, comportement V1 inchangé
        # (pas de bouclage).
        return self.current

    def _shuffle_step(self, *, direction: int) -> MediaItem | None:
        candidate_position = self._shuffle_position + direction
        if 0 <= candidate_position < len(self._shuffle_order):
            self._shuffle_position = candidate_position
        elif self._repeat_mode == RepeatMode.PLAYLIST:
            # Nouveau cycle complet : nouveau tirage aléatoire (F14 du PRD V2).
            self._reshuffle()
            self._shuffle_position = 0 if direction > 0 else len(self._shuffle_order) - 1
        else:
            # RepeatMode.NONE : bloque au bord du tirage courant (comportement
            # cohérent avec le mode linéaire, cf. US-040/US-091).
            self._shuffle_position = max(0, min(len(self._shuffle_order) - 1, candidate_position))
        self._current_index = self._shuffle_order[self._shuffle_position]
        return self.current

    def _save(self) -> None:
        if self._playlist_path is not None:
            save_playlist(self._items, self._playlist_path)
