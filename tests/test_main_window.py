from pathlib import Path

from PyQt6.QtCore import QMimeData, QPointF, Qt, QUrl
from PyQt6.QtGui import QDropEvent
from PyQt6.QtWidgets import QMessageBox

from core.models import MediaItem, PlaybackState
from core.playlist_persistence import load_playlist, save_playlist
from core.settings_manager import SettingsManager
from ui.main_window import MainWindow
from ui.theme_manager import Theme, load_stylesheet

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample.mp3"


def _drop_event(paths: list[Path]) -> QDropEvent:
    mime_data = QMimeData()
    mime_data.setUrls([QUrl.fromLocalFile(str(path)) for path in paths])
    event = QDropEvent(
        QPointF(0, 0),
        Qt.DropAction.CopyAction,
        mime_data,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    # QDropEvent ne garde pas de référence Python vers mime_data : sans ceci,
    # l'objet est GC avant que dropEvent() ne lise event.mimeData() (crash).
    event._mime_data = mime_data
    return event


def test_drop_adds_files_and_starts_playback_when_idle(qapp, qtbot, tmp_path):
    window = MainWindow(
        playlist_path=tmp_path / "playlist.json",
        settings_path=tmp_path / "settings.json",
        thumbnail_cache_dir=tmp_path / "thumbnails",
    )
    qtbot.addWidget(window)

    with qtbot.waitSignal(window.viewmodel.state_changed, timeout=2000):
        window.dropEvent(_drop_event([FIXTURE_PATH]))

    assert [item.display_name for item in window.viewmodel.playlist_items] == ["sample.mp3"]
    assert window.viewmodel.state == PlaybackState.PLAYING

    window.viewmodel.stop()
    qtbot.wait(200)


def test_drop_adds_files_without_interrupting_current_playback(qapp, qtbot, tmp_path):
    window = MainWindow(
        playlist_path=tmp_path / "playlist.json",
        settings_path=tmp_path / "settings.json",
        thumbnail_cache_dir=tmp_path / "thumbnails",
    )
    qtbot.addWidget(window)

    with qtbot.waitSignal(window.viewmodel.state_changed, timeout=2000):
        window.dropEvent(_drop_event([FIXTURE_PATH]))

    with qtbot.waitSignal(window.viewmodel.playlist_changed, timeout=1000):
        window.dropEvent(_drop_event([FIXTURE_PATH]))

    # Un second fichier déposé pendant la lecture rejoint la playlist mais ne
    # coupe pas la piste en cours (cf. _add_files_to_playlist).
    assert len(window.viewmodel.playlist_items) == 2
    assert window.viewmodel.current_index == 0
    assert window.viewmodel.state == PlaybackState.PLAYING

    window.viewmodel.stop()
    qtbot.wait(200)


def test_drop_ignores_files_with_unrecognized_extension(qapp, qtbot, tmp_path):
    window = MainWindow(
        playlist_path=tmp_path / "playlist.json",
        settings_path=tmp_path / "settings.json",
        thumbnail_cache_dir=tmp_path / "thumbnails",
    )
    qtbot.addWidget(window)

    window.dropEvent(_drop_event([Path("document.txt")]))

    assert window.viewmodel.playlist_items == []
    assert window.viewmodel.state == PlaybackState.STOPPED


def test_playback_error_shows_message_box(qapp, qtbot, monkeypatch, tmp_path):
    window = MainWindow(
        playlist_path=tmp_path / "playlist.json",
        settings_path=tmp_path / "settings.json",
        thumbnail_cache_dir=tmp_path / "thumbnails",
    )
    qtbot.addWidget(window)

    captured = {}
    monkeypatch.setattr(
        QMessageBox, "warning", lambda parent, title, message: captured.update(message=message)
    )

    window.viewmodel.error_occurred.emit("Ce format de fichier n'est pas pris en charge.")

    assert captured["message"] == "Ce format de fichier n'est pas pris en charge."


def test_startup_restores_playlist_from_disk(qapp, qtbot, tmp_path):
    playlist_path = tmp_path / "playlist.json"
    save_playlist([MediaItem(file_path=FIXTURE_PATH, display_name="sample.mp3")], playlist_path)

    window = MainWindow(
        playlist_path=playlist_path,
        settings_path=tmp_path / "settings.json",
        thumbnail_cache_dir=tmp_path / "thumbnails",
    )
    qtbot.addWidget(window)

    assert [item.display_name for item in window.viewmodel.playlist_items] == ["sample.mp3"]
    # La restauration au lancement ne doit pas déclencher la lecture toute seule.
    assert window.viewmodel.state == PlaybackState.STOPPED


def test_startup_shows_status_bar_message_when_files_are_missing(qapp, qtbot, tmp_path):
    playlist_path = tmp_path / "playlist.json"
    save_playlist(
        [
            MediaItem(file_path=FIXTURE_PATH, display_name="sample.mp3"),
            MediaItem(file_path=Path("gone_since_last_session.mp3"), display_name="gone.mp3"),
        ],
        playlist_path,
    )

    window = MainWindow(
        playlist_path=playlist_path,
        settings_path=tmp_path / "settings.json",
        thumbnail_cache_dir=tmp_path / "thumbnails",
    )
    qtbot.addWidget(window)

    assert [item.display_name for item in window.viewmodel.playlist_items] == ["sample.mp3"]
    assert "1 fichier" in window.statusBar().currentMessage()


def test_adding_a_file_persists_playlist_to_disk(qapp, qtbot, tmp_path):
    playlist_path = tmp_path / "playlist.json"
    window = MainWindow(
        playlist_path=playlist_path,
        settings_path=tmp_path / "settings.json",
        thumbnail_cache_dir=tmp_path / "thumbnails",
    )
    qtbot.addWidget(window)

    with qtbot.waitSignal(window.viewmodel.state_changed, timeout=2000):
        window.dropEvent(_drop_event([FIXTURE_PATH]))

    saved = load_playlist(playlist_path)
    assert [item.display_name for item in saved] == ["sample.mp3"]

    window.viewmodel.stop()
    qtbot.wait(200)


def test_double_click_on_video_widget_toggles_fullscreen(qapp, qtbot, tmp_path):
    window = MainWindow(
        playlist_path=tmp_path / "playlist.json",
        settings_path=tmp_path / "settings.json",
        thumbnail_cache_dir=tmp_path / "thumbnails",
    )
    qtbot.addWidget(window)
    window.show()

    qtbot.mouseDClick(window.video_widget, Qt.MouseButton.LeftButton)
    assert window.isFullScreen()

    qtbot.mouseDClick(window.video_widget, Qt.MouseButton.LeftButton)
    assert not window.isFullScreen()


def test_exit_fullscreen_returns_to_normal_when_active(qapp, qtbot, tmp_path):
    window = MainWindow(
        playlist_path=tmp_path / "playlist.json",
        settings_path=tmp_path / "settings.json",
        thumbnail_cache_dir=tmp_path / "thumbnails",
    )
    qtbot.addWidget(window)
    window.show()
    window.showFullScreen()
    assert window.isFullScreen()

    window._exit_fullscreen()

    assert not window.isFullScreen()


def test_exit_fullscreen_is_noop_when_not_fullscreen(qapp, qtbot, tmp_path):
    window = MainWindow(
        playlist_path=tmp_path / "playlist.json",
        settings_path=tmp_path / "settings.json",
        thumbnail_cache_dir=tmp_path / "thumbnails",
    )
    qtbot.addWidget(window)
    window.show()

    window._exit_fullscreen()

    assert not window.isFullScreen()


def test_selecting_light_theme_applies_it_and_persists_choice(qapp, qtbot, tmp_path):
    settings_path = tmp_path / "settings.json"
    window = MainWindow(
        playlist_path=tmp_path / "playlist.json",
        settings_path=settings_path,
        thumbnail_cache_dir=tmp_path / "thumbnails",
    )
    qtbot.addWidget(window)

    window._light_theme_action.trigger()

    assert qapp.styleSheet() == load_stylesheet(Theme.LIGHT)
    assert SettingsManager(settings_path).get("theme") == "light"


def test_startup_restores_previously_saved_theme(qapp, qtbot, tmp_path):
    settings_path = tmp_path / "settings.json"
    SettingsManager(settings_path).set("theme", "light")

    window = MainWindow(
        playlist_path=tmp_path / "playlist.json",
        settings_path=settings_path,
        thumbnail_cache_dir=tmp_path / "thumbnails",
    )
    qtbot.addWidget(window)

    assert qapp.styleSheet() == load_stylesheet(Theme.LIGHT)
    assert window._light_theme_action.isChecked()
    assert not window._dark_theme_action.isChecked()


def test_startup_without_saved_theme_uses_system_detection(qapp, qtbot, monkeypatch, tmp_path):
    monkeypatch.setattr(qapp.styleHints(), "colorScheme", lambda: Qt.ColorScheme.Light)
    settings_path = tmp_path / "settings.json"

    window = MainWindow(
        playlist_path=tmp_path / "playlist.json",
        settings_path=settings_path,
        thumbnail_cache_dir=tmp_path / "thumbnails",
    )
    qtbot.addWidget(window)

    assert qapp.styleSheet() == load_stylesheet(Theme.LIGHT)
    # Une détection au premier lancement ne doit pas être sauvegardée comme un
    # choix explicite de l'utilisateur.
    assert SettingsManager(settings_path).get("theme") is None


def test_entering_mini_mode_hides_main_window_and_shows_mini_window(qapp, qtbot, tmp_path):
    window = MainWindow(
        playlist_path=tmp_path / "playlist.json",
        settings_path=tmp_path / "settings.json",
        thumbnail_cache_dir=tmp_path / "thumbnails",
    )
    qtbot.addWidget(window)
    window.show()

    window._enter_mini_mode()

    assert not window.isVisible()
    assert window.mini_mode_window.isVisible()


def test_closing_mini_mode_restores_main_window(qapp, qtbot, tmp_path):
    window = MainWindow(
        playlist_path=tmp_path / "playlist.json",
        settings_path=tmp_path / "settings.json",
        thumbnail_cache_dir=tmp_path / "thumbnails",
    )
    qtbot.addWidget(window)
    window.show()
    window._enter_mini_mode()

    window.mini_mode_window.closed.emit()

    assert window.isVisible()
    assert not window.mini_mode_window.isVisible()


def test_entering_mini_mode_exits_fullscreen_first(qapp, qtbot, tmp_path):
    window = MainWindow(
        playlist_path=tmp_path / "playlist.json",
        settings_path=tmp_path / "settings.json",
        thumbnail_cache_dir=tmp_path / "thumbnails",
    )
    qtbot.addWidget(window)
    window.show()
    window.showFullScreen()
    assert window.isFullScreen()

    window._enter_mini_mode()

    assert not window.isFullScreen()


def test_toggle_fullscreen_is_noop_while_mini_mode_active(qapp, qtbot, tmp_path):
    window = MainWindow(
        playlist_path=tmp_path / "playlist.json",
        settings_path=tmp_path / "settings.json",
        thumbnail_cache_dir=tmp_path / "thumbnails",
    )
    qtbot.addWidget(window)
    window.show()
    window._enter_mini_mode()

    window._toggle_fullscreen()

    assert not window.isFullScreen()


def test_loading_malformed_subtitles_shows_status_bar_message(qapp, qtbot, tmp_path):
    srt_path = tmp_path / "broken.srt"
    srt_path.write_text("not a valid srt file at all", encoding="utf-8")
    window = MainWindow(
        playlist_path=tmp_path / "playlist.json",
        settings_path=tmp_path / "settings.json",
        thumbnail_cache_dir=tmp_path / "thumbnails",
    )
    qtbot.addWidget(window)

    window.viewmodel.load_subtitles(srt_path)

    assert "sous-titres" in window.statusBar().currentMessage().lower()


def test_loading_valid_subtitles_does_not_show_status_bar_message(qapp, qtbot, tmp_path):
    srt_path = tmp_path / "valid.srt"
    srt_path.write_text("1\n00:00:00,000 --> 00:00:01,000\nHello\n", encoding="utf-8")
    window = MainWindow(
        playlist_path=tmp_path / "playlist.json",
        settings_path=tmp_path / "settings.json",
        thumbnail_cache_dir=tmp_path / "thumbnails",
    )
    qtbot.addWidget(window)

    window.viewmodel.load_subtitles(srt_path)

    assert window.statusBar().currentMessage() == ""


def test_changing_volume_persists_it_to_settings(qapp, qtbot, tmp_path):
    settings_path = tmp_path / "settings.json"
    window = MainWindow(
        playlist_path=tmp_path / "playlist.json",
        settings_path=settings_path,
        thumbnail_cache_dir=tmp_path / "thumbnails",
    )
    qtbot.addWidget(window)

    window.volume_widget.slider.setValue(42)

    assert SettingsManager(settings_path).get("volume") == 42


def test_startup_restores_previously_saved_volume(qapp, qtbot, tmp_path):
    settings_path = tmp_path / "settings.json"
    SettingsManager(settings_path).set("volume", 37)

    window = MainWindow(
        playlist_path=tmp_path / "playlist.json",
        settings_path=settings_path,
        thumbnail_cache_dir=tmp_path / "thumbnails",
    )
    qtbot.addWidget(window)

    assert window.volume_widget.slider.value() == 37
    assert window.viewmodel.volume == 37


def test_entering_fullscreen_moves_overlay_panel_to_video(qapp, qtbot, tmp_path):
    window = MainWindow(
        playlist_path=tmp_path / "playlist.json",
        settings_path=tmp_path / "settings.json",
        thumbnail_cache_dir=tmp_path / "thumbnails",
    )
    qtbot.addWidget(window)
    window.show()

    window._toggle_fullscreen()

    assert window.overlay_panel.parentWidget() is window.video_widget
    assert window.overlay_panel.property("overlayMode") is True
    assert window._central_layout.indexOf(window.overlay_panel) == -1
    # Les widgets groupés dans le panneau voyagent avec lui, pas dupliqués.
    assert window.controls_widget.parentWidget() is window.overlay_panel
    assert window.progress_widget.parentWidget() is window.overlay_panel
    assert window.volume_widget.parentWidget() is window.overlay_panel
    assert window.playlist_widget.parentWidget() is window.overlay_panel


def test_exiting_fullscreen_restores_overlay_panel_to_docked_position(qapp, qtbot, tmp_path):
    window = MainWindow(
        playlist_path=tmp_path / "playlist.json",
        settings_path=tmp_path / "settings.json",
        thumbnail_cache_dir=tmp_path / "thumbnails",
    )
    qtbot.addWidget(window)
    window.show()

    window._toggle_fullscreen()
    window._toggle_fullscreen()

    assert (
        window._central_layout.indexOf(window.overlay_panel) == window._overlay_panel_dock_index
    )
    assert window.overlay_panel.property("overlayMode") is False
    # Mêmes instances, toujours fonctionnelles : les signaux existants restent
    # câblés sans avoir besoin de reconnexion.
    with qtbot.waitSignal(window.controls_widget.play_requested, timeout=1000):
        window.controls_widget.play_button.click()


def test_escape_while_fullscreen_also_restores_overlay_panel(qapp, qtbot, tmp_path):
    window = MainWindow(
        playlist_path=tmp_path / "playlist.json",
        settings_path=tmp_path / "settings.json",
        thumbnail_cache_dir=tmp_path / "thumbnails",
    )
    qtbot.addWidget(window)
    window.show()
    window._toggle_fullscreen()

    window._exit_fullscreen()

    assert (
        window._central_layout.indexOf(window.overlay_panel) == window._overlay_panel_dock_index
    )
    assert window.overlay_panel.property("overlayMode") is False


def test_entering_fullscreen_shows_overlay_panel_immediately(qapp, qtbot, tmp_path):
    window = MainWindow(
        playlist_path=tmp_path / "playlist.json",
        settings_path=tmp_path / "settings.json",
        thumbnail_cache_dir=tmp_path / "thumbnails",
    )
    qtbot.addWidget(window)
    window.show()

    window._toggle_fullscreen()

    assert window.overlay_panel.isVisible()


def test_inactivity_timeout_hides_overlay_panel_while_playing(qapp, qtbot, tmp_path):
    window = MainWindow(
        playlist_path=tmp_path / "playlist.json",
        settings_path=tmp_path / "settings.json",
        thumbnail_cache_dir=tmp_path / "thumbnails",
    )
    qtbot.addWidget(window)
    window.show()
    window.viewmodel.load(MediaItem(file_path=FIXTURE_PATH, display_name="sample.mp3"))
    with qtbot.waitSignal(window.viewmodel.state_changed, timeout=2000):
        window.viewmodel.play()
    window._toggle_fullscreen()

    window._on_inactivity_timeout()

    assert not window.overlay_panel.isVisible()

    window.viewmodel.stop()
    qtbot.wait(200)


def test_mouse_move_while_fullscreen_reshows_hidden_overlay_panel(qapp, qtbot, tmp_path):
    window = MainWindow(
        playlist_path=tmp_path / "playlist.json",
        settings_path=tmp_path / "settings.json",
        thumbnail_cache_dir=tmp_path / "thumbnails",
    )
    qtbot.addWidget(window)
    window.show()
    window.viewmodel.load(MediaItem(file_path=FIXTURE_PATH, display_name="sample.mp3"))
    with qtbot.waitSignal(window.viewmodel.state_changed, timeout=2000):
        window.viewmodel.play()
    window._toggle_fullscreen()
    window._on_inactivity_timeout()
    assert not window.overlay_panel.isVisible()

    window._on_fullscreen_mouse_moved()

    assert window.overlay_panel.isVisible()

    window.viewmodel.stop()
    qtbot.wait(200)


def test_overlay_panel_stays_visible_while_paused(qapp, qtbot, tmp_path):
    window = MainWindow(
        playlist_path=tmp_path / "playlist.json",
        settings_path=tmp_path / "settings.json",
        thumbnail_cache_dir=tmp_path / "thumbnails",
    )
    qtbot.addWidget(window)
    window.show()
    window.viewmodel.load(MediaItem(file_path=FIXTURE_PATH, display_name="sample.mp3"))
    with qtbot.waitSignal(window.viewmodel.state_changed, timeout=2000):
        window.viewmodel.play()
    window._toggle_fullscreen()

    with qtbot.waitSignal(window.viewmodel.state_changed, timeout=2000):
        window.viewmodel.pause()

    # Le minuteur ne doit plus pouvoir masquer le panneau tant que la lecture
    # n'a pas repris.
    window._on_inactivity_timeout()
    assert window.overlay_panel.isVisible()
    assert not window._inactivity_timer.isActive()


def test_hovering_overlay_panel_suspends_inactivity_timer(qapp, qtbot, tmp_path):
    window = MainWindow(
        playlist_path=tmp_path / "playlist.json",
        settings_path=tmp_path / "settings.json",
        thumbnail_cache_dir=tmp_path / "thumbnails",
    )
    qtbot.addWidget(window)
    window.show()
    window.viewmodel.load(MediaItem(file_path=FIXTURE_PATH, display_name="sample.mp3"))
    with qtbot.waitSignal(window.viewmodel.state_changed, timeout=2000):
        window.viewmodel.play()
    window._toggle_fullscreen()

    window._on_overlay_hover_entered()
    assert not window._inactivity_timer.isActive()

    # Le survol suspend le minuteur : un timeout ne devrait normalement pas
    # être déclenché pendant ce temps, mais on vérifie directement l'état
    # plutôt que d'attendre les 5 secondes réelles.
    window._on_overlay_hover_left()
    assert window._inactivity_timer.isActive()

    window.viewmodel.stop()
    qtbot.wait(200)
