from pathlib import Path

from PyQt6.QtCore import QObject, QRunnable, Qt, QThreadPool, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QStyle

from core.models import MediaItem
from core.thumbnail_generator import DEFAULT_THUMBNAIL_CACHE_DIR, generate_thumbnail, is_video_file


class _ThumbnailWorkerSignals(QObject):
    finished = pyqtSignal(int, int, object)  # generation, row, Path | None


class _ThumbnailWorker(QRunnable):
    def __init__(
        self, generation: int, row: int, media_item: MediaItem, cache_dir: Path
    ) -> None:
        super().__init__()
        self._generation = generation
        self._row = row
        self._media_item = media_item
        self._cache_dir = cache_dir
        self.signals = _ThumbnailWorkerSignals()

    @pyqtSlot()
    def run(self) -> None:
        thumbnail_path = generate_thumbnail(self._media_item, self._cache_dir)
        self.signals.finished.emit(self._generation, self._row, thumbnail_path)


class PlaylistWidget(QListWidget):
    item_activated = pyqtSignal(int)
    remove_requested = pyqtSignal(int)

    def __init__(self, thumbnail_cache_dir: Path = DEFAULT_THUMBNAIL_CACHE_DIR) -> None:
        super().__init__()
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._thumbnail_cache_dir = thumbnail_cache_dir
        self._thread_pool = QThreadPool()
        # Incrémenté à chaque set_items() : permet d'ignorer les résultats de
        # génération de miniatures encore en vol pour un ancien état de la
        # playlist (US-112 impose une génération asynchrone via QThreadPool,
        # donc les lignes peuvent avoir changé avant qu'un résultat n'arrive).
        self._generation = 0

    def set_items(self, items: list[MediaItem], current_index: int | None) -> None:
        self._generation += 1
        generation = self._generation
        self.clear()

        for index, media_item in enumerate(items):
            list_item = QListWidgetItem(media_item.display_name)
            if index == current_index:
                font = list_item.font()
                font.setBold(True)
                list_item.setFont(font)

            if is_video_file(media_item.file_path):
                list_item.setIcon(self._loading_icon())
                self.addItem(list_item)
                self._queue_thumbnail(generation, index, media_item)
            else:
                list_item.setIcon(self._audio_icon())
                self.addItem(list_item)

    def _queue_thumbnail(self, generation: int, row: int, media_item: MediaItem) -> None:
        worker = _ThumbnailWorker(generation, row, media_item, self._thumbnail_cache_dir)
        worker.signals.finished.connect(self._on_thumbnail_ready)
        self._thread_pool.start(worker)

    def _on_thumbnail_ready(self, generation: int, row: int, thumbnail_path) -> None:
        if generation != self._generation:
            # La playlist a changé depuis que cette génération a été lancée :
            # résultat obsolète, on l'ignore plutôt que de risquer d'appliquer
            # une miniature à la mauvaise ligne.
            return
        if row >= self.count():
            return

        item = self.item(row)
        if thumbnail_path is not None:
            item.setIcon(QIcon(str(thumbnail_path)))
        else:
            # Échec de generate_thumbnail() (fichier corrompu, timeout, etc.) :
            # dégradation gracieuse vers une icône générique, pas d'erreur
            # visible pour l'utilisateur.
            item.setIcon(self._generic_video_icon())

    def _loading_icon(self) -> QIcon:
        return self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload)

    def _generic_video_icon(self) -> QIcon:
        return self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)

    def _audio_icon(self) -> QIcon:
        return self.style().standardIcon(QStyle.StandardPixmap.SP_MediaVolume)

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        self.item_activated.emit(self.row(item))

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Delete and self.currentRow() >= 0:
            self.remove_requested.emit(self.currentRow())
            return
        super().keyPressEvent(event)
