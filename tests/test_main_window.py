from pathlib import Path

from PyQt6.QtCore import QMimeData, QPointF, Qt, QUrl
from PyQt6.QtGui import QDropEvent
from PyQt6.QtWidgets import QMessageBox

from core.models import PlaybackState
from ui.main_window import MainWindow

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


def test_drop_adds_files_and_starts_playback_when_idle(qapp, qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    with qtbot.waitSignal(window.viewmodel.state_changed, timeout=2000):
        window.dropEvent(_drop_event([FIXTURE_PATH]))

    assert [item.display_name for item in window.viewmodel.playlist_items] == ["sample.mp3"]
    assert window.viewmodel.state == PlaybackState.PLAYING

    window.viewmodel.stop()
    qtbot.wait(200)


def test_drop_adds_files_without_interrupting_current_playback(qapp, qtbot):
    window = MainWindow()
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


def test_drop_ignores_files_with_unrecognized_extension(qapp, qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.dropEvent(_drop_event([Path("document.txt")]))

    assert window.viewmodel.playlist_items == []
    assert window.viewmodel.state == PlaybackState.STOPPED


def test_playback_error_shows_message_box(qapp, qtbot, monkeypatch):
    window = MainWindow()
    qtbot.addWidget(window)

    captured = {}
    monkeypatch.setattr(
        QMessageBox, "warning", lambda parent, title, message: captured.update(message=message)
    )

    window.viewmodel.error_occurred.emit("Ce format de fichier n'est pas pris en charge.")

    assert captured["message"] == "Ce format de fichier n'est pas pris en charge."
