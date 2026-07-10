from PyQt6.QtWidgets import QApplication


def test_qapplication_can_be_instantiated(qapp):
    assert isinstance(qapp, QApplication)
