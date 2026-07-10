from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSlider, QStyle, QWidget

from utils.formatters import format_duration


class _SeekSlider(QSlider):
    # Le clic sur la piste saute à la position cliquée, peu importe le style Qt actif
    # (le comportement natif "jump to click" varie selon la plateforme/le style).
    def mousePressEvent(self, event) -> None:
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            value = QStyle.sliderValueFromPosition(
                self.minimum(), self.maximum(), int(event.position().x()), self.width()
            )
            self.setValue(value)


class ProgressWidget(QWidget):
    seek_requested = pyqtSignal(int)

    def __init__(self) -> None:
        super().__init__()
        self.is_seeking = False

        self.slider = _SeekSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 0)
        self.elapsed_label = QLabel(format_duration(0))
        self.duration_label = QLabel(format_duration(0))

        self.slider.sliderPressed.connect(self._on_slider_pressed)
        self.slider.sliderReleased.connect(self._on_slider_released)

        layout = QHBoxLayout(self)
        layout.addWidget(self.elapsed_label)
        layout.addWidget(self.slider)
        layout.addWidget(self.duration_label)

    def _on_slider_pressed(self) -> None:
        self.is_seeking = True

    def _on_slider_released(self) -> None:
        self.is_seeking = False
        self.seek_requested.emit(self.slider.value())

    def set_position(self, position_ms: int) -> None:
        if self.is_seeking:
            return
        self.slider.setValue(position_ms)
        self.elapsed_label.setText(format_duration(position_ms))

    def set_duration(self, duration_ms: int) -> None:
        self.slider.setRange(0, duration_ms)
        self.duration_label.setText(format_duration(duration_ms))
