from __future__ import annotations

import time

from PyQt6 import QtCore


class SleepMonitor(QtCore.QObject):
    """
    Emits ``system_resumed`` when the machine wakes from suspend/sleep.

    Detection strategy (tried in order):
    1. **D-Bus logind** – subscribes to the systemd
       ``org.freedesktop.login1.Manager.PrepareForSleep(false)`` signal.
       Zero-latency, no polling, works on any systemd-based Linux.
    2. **Clock-divergence watchdog** – if D-Bus is unavailable, compares
       ``time.time()`` (wall clock, advances through sleep) against
       ``time.monotonic()`` (CLOCK_MONOTONIC, pauses during sleep).
       A gap > 5 s between the two means a suspend/resume occurred.
    """

    system_resumed = QtCore.pyqtSignal()

    # Minimum wall-vs-monotonic divergence (seconds) to treat as a resume.
    _SLEEP_GAP_THRESHOLD = 5.0
    # How often the watchdog polls (milliseconds).
    _WATCHDOG_INTERVAL_MS = 2_000

    def __init__(self, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)
        self._dbus_ok = self._try_connect_dbus()
        if not self._dbus_ok:
            self._start_watchdog()

    # ------------------------------------------------------------------
    # Strategy 1 – D-Bus logind
    # ------------------------------------------------------------------

    def _try_connect_dbus(self) -> bool:
        """Return True if the D-Bus connection was established successfully."""
        try:
            from PyQt6.QtDBus import QDBusConnection  # type: ignore[import]

            bus = QDBusConnection.systemBus()
            if not bus.isConnected():
                return False

            ok = bus.connect(
                "org.freedesktop.login1",           # service
                "/org/freedesktop/login1",          # path
                "org.freedesktop.login1.Manager",   # interface
                "PrepareForSleep",                  # signal name
                "b",                                # signature: boolean
                self._on_prepare_for_sleep,         # slot
            )
            return ok
        except Exception:
            return False

    def _on_prepare_for_sleep(self, sleeping: bool) -> None:
        """Called by D-Bus: sleeping=True before suspend, False after wake."""
        if not sleeping:
            self.system_resumed.emit()

    # ------------------------------------------------------------------
    # Strategy 2 – clock-divergence watchdog
    # ------------------------------------------------------------------

    def _start_watchdog(self) -> None:
        self._wall_last = time.time()
        self._mono_last = time.monotonic()

        self._watchdog = QtCore.QTimer(self)
        self._watchdog.setInterval(self._WATCHDOG_INTERVAL_MS)
        self._watchdog.timeout.connect(self._watchdog_tick)
        self._watchdog.start()

    def _watchdog_tick(self) -> None:
        wall_now = time.time()
        mono_now = time.monotonic()

        wall_delta = wall_now - self._wall_last
        mono_delta = mono_now - self._mono_last

        # Wall clock includes sleep; monotonic does not.
        # A large discrepancy means the machine slept.
        if wall_delta - mono_delta > self._SLEEP_GAP_THRESHOLD:
            self.system_resumed.emit()

        self._wall_last = wall_now
        self._mono_last = mono_now
