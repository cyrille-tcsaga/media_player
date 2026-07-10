from pathlib import Path

from PyQt6.QtWidgets import QApplication, QFileDialog, QMainWindow, QVBoxLayout, QWidget

from core.models import MediaItem
from ui.controls_widget import ControlsWidget
from ui.progress_widget import ProgressWidget
from ui.video_widget import VideoWidget
from ui.volume_widget import VolumeWidget
from viewmodels.player_viewmodel import PlayerViewModel

MEDIA_FILE_FILTER = (
    "Fichiers média (*.mp4 *.mkv *.avi *.mov *.webm *.mp3 *.wav *.flac *.ogg *.m4a);;"
    "Tous les fichiers (*)"
)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Lecteur Média")
        self.resize(900, 600)

        self.viewmodel = PlayerViewModel()

        self.video_widget = VideoWidget()
        self.controls_widget = ControlsWidget()
        self.progress_widget = ProgressWidget()
        self.volume_widget = VolumeWidget()
        self.viewmodel.set_video_output(self.video_widget)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(self.video_widget)
        layout.addWidget(self.progress_widget)
        layout.addWidget(self.controls_widget)
        layout.addWidget(self.volume_widget)
        self.setCentralWidget(central)

        self.controls_widget.play_requested.connect(self.viewmodel.play)
        self.controls_widget.pause_requested.connect(self.viewmodel.pause)
        self.controls_widget.stop_requested.connect(self.viewmodel.stop)

        self.viewmodel.position_changed.connect(self.progress_widget.set_position)
        self.viewmodel.duration_changed.connect(self.progress_widget.set_duration)
        self.progress_widget.seek_requested.connect(self.viewmodel.set_position)

        self.volume_widget.volume_changed.connect(self.viewmodel.set_volume)

        file_menu = self.menuBar().addMenu("Fichier")
        open_action = file_menu.addAction("Ouvrir un fichier")
        open_action.triggered.connect(self._open_file)

    def _open_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Ouvrir un fichier", "", MEDIA_FILE_FILTER
        )
        if not file_path:
            return

        path = Path(file_path)
        self.viewmodel.load(MediaItem(file_path=path, display_name=path.name))
        self.viewmodel.play()

    def closeEvent(self, event) -> None:
        # Cf. tests/test_player_engine.py : ramener à STOPPED avant destruction,
        # sinon le QMediaPlayer sous-jacent bloque indéfiniment (Qt 6.11 FFmpeg/macOS).
        self.viewmodel.stop()
        QApplication.processEvents()
        super().closeEvent(event)
