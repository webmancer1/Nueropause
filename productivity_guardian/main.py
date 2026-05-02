from __future__ import annotations

import sys
from PyQt6 import QtCore, QtGui, QtWidgets

from .config import (
    APP_NAME,
    ACTIVE_SESSION_THRESHOLD_SECONDS,
    BREAK_DURATION_SECONDS,
    TRAY_TOOLTIP,
)
from .database import Database
from .engine.rule_engine import RuleEngine
from .monitor.activity_tracker import ActivityTracker
from .monitor.sleep_monitor import SleepMonitor
from .ui.break_overlay import BreakOverlay
from .ui.settings_dialog import SettingsDialog


class ProductivityGuardianApp(QtWidgets.QApplication):
    def __init__(self, argv: list[str]) -> None:
        super().__init__(argv)
        self.setApplicationName(APP_NAME)
        self.setQuitOnLastWindowClosed(False)

        self.db = Database()
        self.activity_tracker = ActivityTracker()
        self.rule_engine = RuleEngine()
        self.overlay = BreakOverlay(duration_seconds=BREAK_DURATION_SECONDS)

        self._break_count = 0
        self._monitoring_paused = False
        self._build_tray()

        self._monitor_timer = QtCore.QTimer(self)
        self._monitor_timer.setInterval(1000)
        self._monitor_timer.timeout.connect(self._monitor_loop)

        self.overlay.break_finished.connect(self._on_break_finished)

        # Sleep / suspend detection — resets the work timer on wake
        self.sleep_monitor = SleepMonitor(self)
        self.sleep_monitor.system_resumed.connect(self._on_system_resumed)

    def start(self) -> None:
        self.activity_tracker.start()
        self._monitor_timer.start()

    def _build_tray(self) -> None:
        self.tray_icon = QtWidgets.QSystemTrayIcon(self)
        icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip(TRAY_TOOLTIP)

        menu = QtWidgets.QMenu()
        self.pause_action = QtGui.QAction("Pause monitoring", self)
        self.pause_action.setCheckable(True)
        self.pause_action.toggled.connect(self._set_monitoring_paused)
        menu.addAction(self.pause_action)

        start_break_action = QtGui.QAction("Start break now", self)
        start_break_action.triggered.connect(self._start_break_now)
        menu.addAction(start_break_action)

        menu.addSeparator()
        settings_action = QtGui.QAction("Settings\u2026", self)
        settings_action.triggered.connect(self._open_settings)
        menu.addAction(settings_action)

        menu.addSeparator()
        quit_action = QtGui.QAction("Quit", self)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

    def _monitor_loop(self) -> None:
        if self._monitoring_paused:
            return
        is_idle = self.activity_tracker.is_idle()
        active_seconds = self.activity_tracker.get_active_duration()
        result = self.rule_engine.evaluate(active_seconds, is_idle)
        if result.should_break and not self.overlay.isVisible():
            self.overlay.start()

    def _on_break_finished(self) -> None:
        self._break_count += 1
        active_minutes = self.activity_tracker.get_active_duration() // 60
        self.db.log_session(active_minutes=active_minutes, break_count=self._break_count)
        self.activity_tracker.reset_timer()

    def _set_monitoring_paused(self, paused: bool) -> None:
        self._monitoring_paused = paused
        if paused:
            self.activity_tracker.stop()
            self._monitor_timer.stop()
        else:
            self.activity_tracker.reset_timer()
            self.activity_tracker.start()
            self._monitor_timer.start()

    def _start_break_now(self) -> None:
        if not self.overlay.isVisible():
            self.overlay.start()

    def _on_system_resumed(self) -> None:
        """Called when the machine wakes from suspend/sleep."""
        # Dismiss the overlay if it was visible when the lid closed
        if self.overlay.isVisible():
            self.overlay._finish()  # stops timers and hides cleanly

        # Reset work-session timer so the user gets a fresh period
        self.activity_tracker.reset_timer()

        self.tray_icon.showMessage(
            APP_NAME,
            "Welcome back! Your work timer has been reset.",
            QtWidgets.QSystemTrayIcon.MessageIcon.Information,
            4000,
        )

    def _open_settings(self) -> None:
        current_work = self.rule_engine.active_threshold_seconds // 60
        current_break = self.overlay.duration_seconds // 60
        dialog = SettingsDialog(
            work_period_minutes=current_work,
            break_duration_minutes=current_break,
        )
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            new_work_secs = dialog.work_period_minutes * 60
            new_break_secs = dialog.break_duration_minutes * 60
            self.rule_engine.active_threshold_seconds = new_work_secs
            self.overlay.duration_seconds = new_break_secs
            self.tray_icon.showMessage(
                APP_NAME,
                f"Work period: {dialog.work_period_minutes} min  •  "
                f"Break: {dialog.break_duration_minutes} min",
                QtWidgets.QSystemTrayIcon.MessageIcon.Information,
                3000,
            )

    def _quit(self) -> None:
        self.activity_tracker.stop()
        self._monitor_timer.stop()
        self.tray_icon.hide()
        self.quit()


def main() -> None:
    app = ProductivityGuardianApp(sys.argv)
    app.start()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
