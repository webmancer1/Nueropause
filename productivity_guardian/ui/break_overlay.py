from __future__ import annotations

from PyQt6 import QtCore, QtGui, QtWidgets

from ..config import (
    BREAK_DURATION_SECONDS,
    OVERLAY_ACCENT_COLOR,
    OVERLAY_BG_COLOR,
    OVERLAY_TEXT_COLOR,
    PROMPT_ROTATE_SECONDS,
)
from ..engine.wellness_engine import WellnessEngine


class BreakOverlay(QtWidgets.QWidget):
    break_finished = QtCore.pyqtSignal()

    def __init__(self, duration_seconds: int = BREAK_DURATION_SECONDS) -> None:
        super().__init__()
        self.duration_seconds = duration_seconds
        self.remaining_seconds = duration_seconds
        self.wellness_engine = WellnessEngine()

        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint
            | QtCore.Qt.WindowType.WindowStaysOnTopHint
            | QtCore.Qt.WindowType.Tool
        )
        self.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self._build_ui()

        self._countdown_timer = QtCore.QTimer(self)
        self._countdown_timer.setInterval(1000)
        self._countdown_timer.timeout.connect(self._tick)

        self._prompt_timer = QtCore.QTimer(self)
        self._prompt_timer.setInterval(PROMPT_ROTATE_SECONDS * 1000)
        self._prompt_timer.timeout.connect(self._rotate_prompt)

    def _build_ui(self) -> None:
        self.setStyleSheet(
            f"""
            QWidget {{ background-color: {OVERLAY_BG_COLOR}; }}
            QLabel {{ color: {OVERLAY_TEXT_COLOR}; }}
            QLabel#promptLabel {{ color: {OVERLAY_ACCENT_COLOR}; }}
            """
        )

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(80, 80, 80, 80)
        layout.setSpacing(24)

        title = QtWidgets.QLabel("Time for a break")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title.setFont(QtGui.QFont("Sans Serif", 32, QtGui.QFont.Weight.Bold))

        self.countdown_label = QtWidgets.QLabel(self._format_time(self.remaining_seconds))
        self.countdown_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.countdown_label.setFont(QtGui.QFont("Sans Serif", 48, QtGui.QFont.Weight.Bold))

        self.prompt_label = QtWidgets.QLabel("")
        self.prompt_label.setObjectName("promptLabel")
        self.prompt_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.prompt_label.setFont(QtGui.QFont("Sans Serif", 24))
        self.prompt_label.setWordWrap(True)

        layout.addStretch(1)
        layout.addWidget(title)
        layout.addWidget(self.countdown_label)
        layout.addWidget(self.prompt_label)
        layout.addStretch(1)
        self.setLayout(layout)

    def start(self) -> None:
        self.remaining_seconds = self.duration_seconds
        self.countdown_label.setText(self._format_time(self.remaining_seconds))
        self._rotate_prompt()
        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        self._countdown_timer.start()
        self._prompt_timer.start()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        # Prevent accidental closure during break
        event.ignore()

    def _tick(self) -> None:
        self.remaining_seconds -= 1
        if self.remaining_seconds <= 0:
            self._finish()
            return
        self.countdown_label.setText(self._format_time(self.remaining_seconds))

    def _rotate_prompt(self) -> None:
        state = self.wellness_engine.next_prompt()
        self.prompt_label.setText(state.prompt)

    def _finish(self) -> None:
        self._countdown_timer.stop()
        self._prompt_timer.stop()
        self.hide()
        self.break_finished.emit()

    @staticmethod
    def _format_time(seconds: int) -> str:
        minutes = seconds // 60
        remaining = seconds % 60
        return f"{minutes:02d}:{remaining:02d}"
