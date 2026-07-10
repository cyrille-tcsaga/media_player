from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QSlider, QWidget


class VolumeWidget(QWidget):
    volume_changed = pyqtSignal(int)  # 0-100

    def __init__(self) -> None:
        super().__init__()
        self._previous_volume = 100
        self._unmuting_from_slider = False

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(100)

        self.mute_button = QPushButton("Mute")
        self.mute_button.setCheckable(True)

        self.slider.valueChanged.connect(self._on_slider_changed)
        self.mute_button.toggled.connect(self._on_mute_toggled)

        layout = QHBoxLayout(self)
        layout.addWidget(self.slider)
        layout.addWidget(self.mute_button)

    def _on_slider_changed(self, value: int) -> None:
        if value > 0 and self.mute_button.isChecked():
            self._unmuting_from_slider = True
            self.mute_button.setChecked(False)
            self._unmuting_from_slider = False
        self.volume_changed.emit(value)

    def _on_mute_toggled(self, checked: bool) -> None:
        if checked:
            if self.slider.value() > 0:
                self._previous_volume = self.slider.value()
            self.slider.blockSignals(True)
            self.slider.setValue(0)
            self.slider.blockSignals(False)
            self.volume_changed.emit(0)
        elif not self._unmuting_from_slider:
            self.slider.blockSignals(True)
            self.slider.setValue(self._previous_volume)
            self.slider.blockSignals(False)
            self.volume_changed.emit(self._previous_volume)
