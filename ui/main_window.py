from pathlib import Path

from PyQt6.QtCore import QEvent, Qt, QTimer
from PyQt6.QtGui import QActionGroup, QKeySequence, QShortcut
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
from core.settings_manager import DEFAULT_SETTINGS_PATH, SettingsManager
from core.thumbnail_generator import DEFAULT_THUMBNAIL_CACHE_DIR
from ui.controls_widget import ControlsWidget
from ui.mini_mode_window import MiniModeWindow
from ui.overlay_panel import OverlayPanel
from ui.playlist_widget import PlaylistWidget
from ui.progress_widget import ProgressWidget
from ui.theme_manager import Theme, apply_theme, detect_system_theme
from ui.video_widget import VideoWidget
from ui.volume_widget import VolumeWidget
from viewmodels.player_viewmodel import PlayerViewModel

SEEK_STEP_MS = 5_000
VOLUME_STEP_PERCENT = 5
# Délai d'inactivité avant masquage automatique du panneau overlay en plein
# écran (décision actée en PRD V3 section 9).
OVERLAY_INACTIVITY_MS = 5_000

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
    def __init__(
        self,
        playlist_path: Path = DEFAULT_PLAYLIST_PATH,
        settings_path: Path = DEFAULT_SETTINGS_PATH,
        thumbnail_cache_dir: Path = DEFAULT_THUMBNAIL_CACHE_DIR,
    ) -> None:
        super().__init__()
        self.setWindowTitle("Lecteur Média")
        self.resize(900, 600)
        self.setAcceptDrops(True)

        self.viewmodel = PlayerViewModel(playlist_path=playlist_path)
        self._settings = SettingsManager(settings_path=settings_path)

        self.video_widget = VideoWidget()
        self.controls_widget = ControlsWidget()
        self.progress_widget = ProgressWidget()
        self.volume_widget = VolumeWidget()
        self.playlist_widget = PlaylistWidget(thumbnail_cache_dir=thumbnail_cache_dir)
        self.viewmodel.set_video_output(self.video_widget)
        self.video_widget.installEventFilter(self)

        self.mini_mode_window = MiniModeWindow(self.viewmodel, parent=self)
        self.mini_mode_window.closed.connect(self._exit_mini_mode)

        # US-130 : progress/controls/volume/playlist regroupés dans un seul
        # panneau, qui bascule comme un tout entre ancrage normal (bas de
        # fenêtre) et superposition sur la vidéo en plein écran — mêmes
        # instances de widgets, jamais dupliquées.
        self.overlay_panel = OverlayPanel()
        self.overlay_panel.layout_.addWidget(self.progress_widget)
        self.overlay_panel.layout_.addWidget(self.controls_widget)
        self.overlay_panel.layout_.addWidget(self.volume_widget)
        self.overlay_panel.layout_.addWidget(self.playlist_widget)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(self.video_widget, stretch=1)
        layout.addWidget(self.overlay_panel)
        self.setCentralWidget(central)
        self._central_layout = layout
        # Position d'origine du panneau dans le layout, pour l'y réinsérer
        # telle quelle à la sortie du plein écran (ancré en bas, sans
        # redémarrage ni réinitialisation d'état — même instances de widgets,
        # juste reparentées).
        self._overlay_panel_dock_index = layout.indexOf(self.overlay_panel)

        # US-131 : masquage automatique par inactivité en plein écran.
        self._inactivity_timer = QTimer(self)
        self._inactivity_timer.setSingleShot(True)
        self._inactivity_timer.setInterval(OVERLAY_INACTIVITY_MS)
        self._inactivity_timer.timeout.connect(self._on_inactivity_timeout)
        self._overlay_hover_suspended = False
        self.overlay_panel.mouse_entered.connect(self._on_overlay_hover_entered)
        self.overlay_panel.mouse_left.connect(self._on_overlay_hover_left)
        self.viewmodel.state_changed.connect(self._on_state_changed_for_overlay)
        # Filtre global (plutôt que sur un widget précis) : le panneau overlay
        # et la vidéo se partagent la fenêtre, un mouvement de souris doit être
        # détecté quel que soit le widget survolé. Qt retire automatiquement ce
        # filtre à la destruction de self.
        QApplication.instance().installEventFilter(self)

        self.controls_widget.play_requested.connect(self.viewmodel.play)
        self.controls_widget.pause_requested.connect(self.viewmodel.pause)
        self.controls_widget.stop_requested.connect(self.viewmodel.stop)
        self.controls_widget.previous_requested.connect(self.viewmodel.previous_track)
        self.controls_widget.next_requested.connect(self.viewmodel.next_track)
        self.controls_widget.playback_rate_changed.connect(self.viewmodel.set_playback_rate)
        self.controls_widget.repeat_mode_changed.connect(self.viewmodel.set_repeat_mode)
        self.controls_widget.shuffle_enabled_changed.connect(self.viewmodel.set_shuffle_enabled)

        self.viewmodel.position_changed.connect(self.progress_widget.set_position)
        self.viewmodel.duration_changed.connect(self.progress_widget.set_duration)
        self.progress_widget.seek_requested.connect(self.viewmodel.set_position)

        self.volume_widget.volume_changed.connect(self.viewmodel.set_volume)
        self.volume_widget.volume_changed.connect(self._on_volume_changed)

        self.playlist_widget.item_activated.connect(self.viewmodel.play_at)
        self.playlist_widget.remove_requested.connect(self.viewmodel.remove_from_playlist)
        self.viewmodel.playlist_changed.connect(self._on_playlist_changed)
        self.viewmodel.error_occurred.connect(self._on_playback_error)
        self.viewmodel.subtitle_text_changed.connect(self._on_subtitle_text_changed)
        self.viewmodel.subtitles_loaded.connect(self._on_subtitles_loaded)

        file_menu = self.menuBar().addMenu("Fichier")
        open_action = file_menu.addAction("Ouvrir un fichier")
        open_action.triggered.connect(self._open_file)
        subtitles_action = file_menu.addAction("Charger les sous-titres")
        subtitles_action.triggered.connect(self._load_subtitles)

        self._build_theme_menu()
        self._build_shortcuts()
        self._restore_saved_playlist(playlist_path)
        self._apply_saved_or_system_theme()
        self._restore_saved_volume()

    def _build_theme_menu(self) -> None:
        view_menu = self.menuBar().addMenu("Affichage")
        self._dark_theme_action = view_menu.addAction("Thème sombre")
        self._dark_theme_action.setCheckable(True)
        self._light_theme_action = view_menu.addAction("Thème clair")
        self._light_theme_action.setCheckable(True)

        theme_group = QActionGroup(self)
        theme_group.setExclusive(True)
        theme_group.addAction(self._dark_theme_action)
        theme_group.addAction(self._light_theme_action)

        self._dark_theme_action.triggered.connect(lambda: self._set_theme(Theme.DARK))
        self._light_theme_action.triggered.connect(lambda: self._set_theme(Theme.LIGHT))

        view_menu.addSeparator()
        mini_mode_action = view_menu.addAction("Mini-mode")
        mini_mode_action.triggered.connect(self._enter_mini_mode)

    def _apply_saved_or_system_theme(self) -> None:
        saved_theme = self._settings.get("theme")
        theme = Theme(saved_theme) if saved_theme is not None else detect_system_theme()
        self._set_theme(theme, persist=False)

    def _set_theme(self, theme: Theme, *, persist: bool = True) -> None:
        apply_theme(QApplication.instance(), theme)
        self._dark_theme_action.setChecked(theme == Theme.DARK)
        self._light_theme_action.setChecked(theme == Theme.LIGHT)
        if persist:
            self._settings.set("theme", theme.value)

    def _restore_saved_volume(self) -> None:
        # setValue() déclenche VolumeWidget.volume_changed, donc applique aussi
        # le volume restauré à PlayerEngine via self.viewmodel.set_volume.
        self.volume_widget.slider.setValue(self._settings.get("volume"))

    def _on_volume_changed(self, volume_percent: int) -> None:
        self._settings.set("volume", volume_percent)

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
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, self._exit_fullscreen)

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

    def eventFilter(self, obj, event) -> bool:
        if obj is self.video_widget and event.type() == QEvent.Type.MouseButtonDblClick:
            self._toggle_fullscreen()
            return True
        if event.type() == QEvent.Type.MouseMove and self.isFullScreen():
            self._on_fullscreen_mouse_moved()
        return super().eventFilter(obj, event)

    def _toggle_fullscreen(self) -> None:
        # Plein écran et mini-mode ne peuvent pas être actifs en même temps
        # (US-101, résout le TODO laissé par US-082) : MainWindow est masquée
        # pendant le mini-mode, donc son video_widget ne peut normalement pas
        # recevoir de double-clic — ce garde-fou reste une sécurité explicite
        # plutôt qu'un état ambigu implicite.
        if self.mini_mode_window.isVisible():
            return
        if self.isFullScreen():
            self._exit_fullscreen()
        else:
            self._enter_fullscreen()

    def _enter_fullscreen(self) -> None:
        self.showFullScreen()
        self._move_overlay_panel_to_video()
        # Apparition immédiate à l'entrée en plein écran (US-131), puis
        # démarrage du minuteur d'inactivité (sauf lecture non active).
        self.overlay_panel.show()
        self._reset_inactivity_timer()

    def _exit_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()
            self._inactivity_timer.stop()
            self._restore_overlay_panel_to_docked_position()

    def _move_overlay_panel_to_video(self) -> None:
        # Réutilise l'instance existante du panneau plutôt que d'en créer une
        # seconde pour le mode plein écran — seuls le parent et le style QSS
        # changent, la logique/les signaux des widgets qu'il contient restent
        # identiques.
        self._central_layout.removeWidget(self.overlay_panel)
        self.overlay_panel.setParent(self.video_widget)
        self.overlay_panel.set_overlay_mode(True)
        self.video_widget.set_overlay_panel(self.overlay_panel)

    def _restore_overlay_panel_to_docked_position(self) -> None:
        self.video_widget.set_overlay_panel(None)
        self.overlay_panel.set_overlay_mode(False)
        self.overlay_panel.setParent(None)
        self._central_layout.insertWidget(self._overlay_panel_dock_index, self.overlay_panel)
        self.overlay_panel.show()

    def _on_fullscreen_mouse_moved(self) -> None:
        if self._overlay_hover_suspended:
            return
        self.overlay_panel.show()
        self._reset_inactivity_timer()

    def _on_overlay_hover_entered(self) -> None:
        # Survol direct du panneau : suspend le minuteur tant que la souris ne
        # l'a pas quitté (US-131), indépendamment de l'état de lecture.
        self._overlay_hover_suspended = True
        self._inactivity_timer.stop()
        self.overlay_panel.show()

    def _on_overlay_hover_left(self) -> None:
        self._overlay_hover_suspended = False
        self._reset_inactivity_timer()

    def _on_state_changed_for_overlay(self, state: PlaybackState) -> None:
        if not self.isFullScreen():
            return
        if state != PlaybackState.PLAYING:
            # En pause (ou arrêt) : les contrôles n'ont pas de raison de se
            # masquer (US-131 mentionne explicitement la pause ; la même
            # logique s'applique à STOPPED/ERROR par cohérence — un minuteur
            # qui masquerait les contrôles sans lecture active n'aurait pas
            # de sens pour l'utilisateur).
            self._inactivity_timer.stop()
            self.overlay_panel.show()
        elif not self._overlay_hover_suspended:
            self._reset_inactivity_timer()

    def _reset_inactivity_timer(self) -> None:
        if self.viewmodel.state != PlaybackState.PLAYING:
            self._inactivity_timer.stop()
            return
        self._inactivity_timer.start()

    def _on_inactivity_timeout(self) -> None:
        # Garde défensive plutôt que de compter uniquement sur la discipline
        # de démarrage/arrêt du minuteur ailleurs (_reset_inactivity_timer,
        # _on_state_changed_for_overlay) : un signal timeout() déjà mis en
        # file au moment précis d'une pause resterait sinon possible.
        if self.viewmodel.state != PlaybackState.PLAYING:
            return
        self.overlay_panel.hide()

    def _enter_mini_mode(self) -> None:
        # Décision explicite (résout le TODO(US-101) laissé par US-082) : le
        # plein écran et le mini-mode sont incompatibles, on désactive donc le
        # premier en priorité plutôt que de laisser un état ambigu.
        self._exit_fullscreen()
        self.viewmodel.set_video_output(self.mini_mode_window.video_widget)
        self.hide()
        self.mini_mode_window.show()

    def _exit_mini_mode(self) -> None:
        self.mini_mode_window.hide()
        self.viewmodel.set_video_output(self.video_widget)
        self.show()

    def _open_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Ouvrir un fichier", "", MEDIA_FILE_FILTER
        )
        if not file_path:
            return

        self._add_files_to_playlist([Path(file_path)])

    def _load_subtitles(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Charger les sous-titres", "", "Sous-titres (*.srt)"
        )
        if not file_path:
            return
        self.viewmodel.load_subtitles(Path(file_path))

    def _on_playlist_changed(self) -> None:
        self.playlist_widget.set_items(self.viewmodel.playlist_items, self.viewmodel.current_index)

    def _on_playback_error(self, message: str) -> None:
        QMessageBox.warning(self, "Erreur de lecture", message)

    def _on_subtitle_text_changed(self, text: str) -> None:
        if text:
            self.video_widget.subtitle_overlay.set_text(text)
        else:
            self.video_widget.subtitle_overlay.clear()

    def _on_subtitles_loaded(self, success: bool) -> None:
        if not success:
            # Dégradation gracieuse (PRD V2 section 5) : message discret dans
            # la barre de statut plutôt qu'une boîte de dialogue bloquante, la
            # lecture vidéo continue normalement.
            self.statusBar().showMessage(
                "Le fichier de sous-titres n'a pas pu être chargé (format invalide ou vide).",
                5000,
            )

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
        # Fenêtre indépendante (always-on-top) : ne pas la laisser orpheline si
        # MainWindow se ferme pendant que le mini-mode est actif. hide() plutôt
        # que close() : mini_mode_window.closed déclenche _exit_mini_mode(), qui
        # ré-afficherait MainWindow (self.show()) en pleine fermeture.
        self.mini_mode_window.hide()

        # Cf. tests/test_player_engine.py : ramener à STOPPED avant destruction,
        # sinon le QMediaPlayer sous-jacent bloque indéfiniment (Qt 6.11 FFmpeg/macOS).
        self.viewmodel.stop()
        QApplication.processEvents()
        super().closeEvent(event)
