from __future__ import annotations

from PyQt6 import QtCore, QtGui, QtWidgets

from ..config import (
    ACTIVE_SESSION_THRESHOLD_SECONDS,
    BREAK_DURATION_SECONDS,
    OVERLAY_ACCENT_COLOR,
    OVERLAY_BG_COLOR,
    OVERLAY_TEXT_COLOR,
)


class SettingsDialog(QtWidgets.QDialog):
    """Modal dialog for adjusting work-period and break-duration settings."""

    def __init__(
        self,
        work_period_minutes: int,
        break_duration_minutes: int,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Productivity Guardian — Settings")
        self.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
        self.setFixedSize(420, 300)
        self.setWindowFlags(
            self.windowFlags() & ~QtCore.Qt.WindowType.WindowContextHelpButtonHint
        )

        self._work_period_minutes = work_period_minutes
        self._break_duration_minutes = break_duration_minutes

        self._apply_style()
        self._build_ui()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def work_period_minutes(self) -> int:
        return self._work_spin.value()

    @property
    def break_duration_minutes(self) -> int:
        return self._break_spin.value()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _apply_style(self) -> None:
        self.setStyleSheet(
            f"""
            QDialog {{
                background-color: {OVERLAY_BG_COLOR};
                color: {OVERLAY_TEXT_COLOR};
                font-family: "Segoe UI", "Sans Serif", sans-serif;
            }}
            QLabel {{
                color: {OVERLAY_TEXT_COLOR};
                font-size: 13px;
            }}
            QLabel#sectionTitle {{
                color: {OVERLAY_ACCENT_COLOR};
                font-size: 18px;
                font-weight: bold;
            }}
            QLabel#subLabel {{
                color: #94a3b8;
                font-size: 11px;
            }}
            QSpinBox {{
                background-color: #1e293b;
                color: {OVERLAY_TEXT_COLOR};
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 14px;
                min-width: 90px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background-color: #334155;
                border: none;
                width: 22px;
            }}
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background-color: #475569;
            }}
            QPushButton {{
                background-color: {OVERLAY_ACCENT_COLOR};
                color: #0f172a;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #7dd3fc;
            }}
            QPushButton#cancelBtn {{
                background-color: #334155;
                color: {OVERLAY_TEXT_COLOR};
            }}
            QPushButton#cancelBtn:hover {{
                background-color: #475569;
            }}
            QFrame#divider {{
                color: #334155;
            }}
            """
        )

    def _build_ui(self) -> None:
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(0)

        # --- Title ---
        title = QtWidgets.QLabel("Timer Settings")
        title.setObjectName("sectionTitle")
        root.addWidget(title)
        root.addSpacing(4)

        sub = QtWidgets.QLabel("Adjust when breaks are triggered and how long they last.")
        sub.setObjectName("subLabel")
        sub.setWordWrap(True)
        root.addWidget(sub)

        root.addSpacing(20)

        # --- Work period row ---
        root.addWidget(self._row(
            "Work period",
            "How long you work before a break is triggered",
            self._make_spin(
                value=self._work_period_minutes,
                min_val=1,
                max_val=180,
                suffix=" min",
                attr="_work_spin",
            ),
        ))

        root.addSpacing(16)

        # --- Break duration row ---
        root.addWidget(self._row(
            "Break duration",
            "How long the break overlay stays on screen",
            self._make_spin(
                value=self._break_duration_minutes,
                min_val=1,
                max_val=60,
                suffix=" min",
                attr="_break_spin",
            ),
        ))

        root.addStretch(1)

        # --- Divider ---
        divider = QtWidgets.QFrame()
        divider.setObjectName("divider")
        divider.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        root.addWidget(divider)
        root.addSpacing(16)

        # --- Buttons ---
        btn_row = QtWidgets.QHBoxLayout()
        btn_row.setSpacing(12)
        btn_row.addStretch(1)

        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QtWidgets.QPushButton("Save")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.accept)
        btn_row.addWidget(save_btn)

        root.addLayout(btn_row)

    def _row(
        self,
        label: str,
        hint: str,
        spin: QtWidgets.QSpinBox,
    ) -> QtWidgets.QWidget:
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        text_col = QtWidgets.QVBoxLayout()
        text_col.setSpacing(2)

        lbl = QtWidgets.QLabel(label)
        lbl.setStyleSheet("font-size: 13px; font-weight: 600;")
        text_col.addWidget(lbl)

        hint_lbl = QtWidgets.QLabel(hint)
        hint_lbl.setObjectName("subLabel")
        hint_lbl.setWordWrap(True)
        text_col.addWidget(hint_lbl)

        layout.addLayout(text_col, stretch=1)
        layout.addWidget(spin)

        return container

    def _make_spin(
        self,
        value: int,
        min_val: int,
        max_val: int,
        suffix: str,
        attr: str,
    ) -> QtWidgets.QSpinBox:
        spin = QtWidgets.QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(value)
        spin.setSuffix(suffix)
        spin.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        setattr(self, attr, spin)
        return spin
