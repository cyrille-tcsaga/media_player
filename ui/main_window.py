from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from core.models import MediaItem, PlaybackState
from core.playlist_persistence import DEFAULT_PLAYLIST_PATH, load_playlist_with_missing_count
from ui.controls_widget import ControlsWidget
from ui.playlist_widget import PlaylistWidget
from ui.progress_widget import ProgressWidget
from ui.video_widget import VideoWidget
from ui.volume_widget import VolumeWidget
from viewmodels.player_viewmodel import PlayerViewModel

SEEK_STEP_MS = 5_000
VOLUME_STEP_PERCENT = 5

MEDIA_EXTENSIONS = (
    ".mp4",
    ".mkv",
    ".avi",
    ".mov",
    ".webm",
    ".mp3",
    ".wav",
    ".flac",
    ".ogg",
    ".m4a",
)
MEDIA_FILE_FILTER = (
    f"Fichiers média ({' '.join(f'*{ext}' for ext in MEDIA_EXTENSIONS)});;"
    "Tous les fichiers (*)"
)


class MainWindow(QMainWindow):
    def __init__(self, playlist_path: Path = DEFAULT_PLAYLIST_PATH) -> None:
        super().__init__()
        self.setWindowTitle("Lecteur Média")
        self.resize(900, 600)
        self.setAcceptDrops(True)

        self.viewmodel = PlayerViewModel(playlist_path=playlist_path)

        self.video_widget = VideoWidget()
        self.controls_widget = ControlsWidget()
        self.progress_widget = ProgressWidget()
        self.volume_widget = VolumeWidget()
        self.playlist_widget = PlaylistWidget()
        self.viewmodel.set_video_output(self.video_widget)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(self.video_widget, stretch=1)
        layout.addWidget(self.progress_widget)
        layout.addWidget(self.controls_widget)
        layout.addWidget(self.volume_widget)
        layout.addWidget(self.playlist_widget)
        self.setCentralWidget(central)

        self.controls_widget.play_requested.connect(self.viewmodel.play)
        self.controls_widget.pause_requested.connect(self.viewmodel.pause)
        self.controls_widget.stop_requested.connect(self.viewmodel.stop)
        self.controls_widget.previous_requested.connect(self.viewmodel.previous_track)
        self.controls_widget.next_requested.connect(self.viewmodel.next_track)
        self.controls_widget.playback_rate_changed.connect(self.viewmodel.set_playback_rate)

        self.viewmodel.position_changed.connect(self.progress_widget.set_position)
        self.viewmodel.duration_changed.connect(self.progress_widget.set_duration)
        self.progress_widget.seek_requested.connect(self.viewmodel.set_position)

        self.volume_widget.volume_changed.connect(self.viewmodel.set_volume)

        self.playlist_widget.item_activated.connect(self.viewmodel.play_at)
        self.playlist_widget.remove_requested.connect(self.viewmodel.remove_from_playlist)
        self.viewmodel.playlist_changed.connect(self._on_playlist_changed)
        self.viewmodel.error_occurred.connect(self._on_playback_error)

        file_menu = self.menuBar().addMenu("Fichier")
        open_action = file_menu.addAction("Ouvrir un fichier")
        open_action.triggered.connect(self._open_file)

        self._build_shortcuts()
        self._restore_saved_playlist(playlist_path)

    def _restore_saved_playlist(self, playlist_path: Path) -> None:
        items, missing_count = load_playlist_with_missing_count(playlist_path)
        for item in items:
            self.viewmodel.add_to_playlist(item)
        if missing_count:
            self.statusBar().showMessage(
                f"{missing_count} fichier(s) de la précédente playlist introuvable(s) "
                "et ignoré(s).",
                5000,
            )

    def _build_shortcuts(self) -> None:
        QShortcut(QKeySequence(Qt.Key.Key_Space), self, self._toggle_play_pause)
        QShortcut(QKeySequence(Qt.Key.Key_Right), self, lambda: self._seek_relative(SEEK_STEP_MS))
        QShortcut(QKeySequence(Qt.Key.Key_Left), self, lambda: self._seek_relative(-SEEK_STEP_MS))
        QShortcut(
            QKeySequence(Qt.Key.Key_Up), self, lambda: self._change_volume(VOLUME_STEP_PERCENT)
        )
        QShortcut(
            QKeySequence(Qt.Key.Key_Down), self, lambda: self._change_volume(-VOLUME_STEP_PERCENT)
        )

    def _toggle_play_pause(self) -> None:
        if self.viewmodel.state == PlaybackState.PLAYING:
            self.viewmodel.pause()
        else:
            self.viewmodel.play()

    def _seek_relative(self, offset_ms: int) -> None:
        new_position = max(0, min(self.viewmodel.duration, self.viewmodel.position + offset_ms))
        self.viewmodel.set_position(new_position)
        self.progress_widget.set_position(new_position)

    def _change_volume(self, offset_percent: int) -> None:
        new_volume = max(0, min(100, self.volume_widget.slider.value() + offset_percent))
        self.volume_widget.slider.setValue(new_volume)

    def _open_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Ouvrir un fichier", "", MEDIA_FILE_FILTER
        )
        if not file_path:
            return

        self._add_files_to_playlist([Path(file_path)])

    def _on_playlist_changed(self) -> None:
        self.playlist_widget.set_items(self.viewmodel.playlist_items, self.viewmodel.current_index)

    def _on_playback_error(self, message: str) -> None:
        QMessageBox.warning(self, "Erreur de lecture", message)

    def _add_files_to_playlist(self, paths: list[Path]) -> None:
        was_playing = self.viewmodel.state == PlaybackState.PLAYING
        first_new_index = len(self.viewmodel.playlist_items)
        for path in paths:
            self.viewmodel.add_to_playlist(MediaItem(file_path=path, display_name=path.name))
        if not was_playing:
            self.viewmodel.play_at(first_new_index)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        paths = [
            Path(url.toLocalFile())
            for url in event.mimeData().urls()
            if url.isLocalFile() and Path(url.toLocalFile()).suffix.lower() in MEDIA_EXTENSIONS
        ]
        if not paths:
            return
        self._add_files_to_playlist(paths)

    def closeEvent(self, event) -> None:
        # Cf. tests/test_player_engine.py : ramener à STOPPED avant destruction,
        # sinon le QMediaPlayer sous-jacent bloque indéfiniment (Qt 6.11 FFmpeg/macOS).
        self.viewmodel.stop()
        QApplication.processEvents()
        super().closeEvent(event)
