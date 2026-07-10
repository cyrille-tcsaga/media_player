from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QListWidget, QListWidgetItem

from core.models import MediaItem


class PlaylistWidget(QListWidget):
    item_activated = pyqtSignal(int)
    remove_requested = pyqtSignal(int)

    def __init__(self) -> None:
        super().__init__()
        self.itemDoubleClicked.connect(self._on_item_double_clicked)

    def set_items(self, items: list[MediaItem], current_index: int | None) -> None:
        self.clear()
        for index, media_item in enumerate(items):
            list_item = QListWidgetItem(media_item.display_name)
            if index == current_index:
                font = list_item.font()
                font.setBold(True)
                list_item.setFont(font)
            self.addItem(list_item)

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        self.item_activated.emit(self.row(item))

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Delete and self.currentRow() >= 0:
            self.remove_requested.emit(self.currentRow())
            return
        super().keyPressEvent(event)
