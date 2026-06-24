from __future__ import annotations

import threading
import time
from pynput import keyboard, mouse

from ..config import IDLE_THRESHOLD_SECONDS


class ActivityTracker:
    def __init__(self, idle_threshold_seconds: int = IDLE_THRESHOLD_SECONDS) -> None:
        self.idle_threshold_seconds = idle_threshold_seconds
        self._lock = threading.Lock()
        self._last_input_ts = time.monotonic()
        self._session_start_ts = time.monotonic()
    def _create_listeners(self) -> None:
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_input,
            on_release=self._on_input,
        )
        self._mouse_listener = mouse.Listener(
            on_move=self._on_input,
            on_click=self._on_input,
            on_scroll=self._on_input,
        )

    def start(self) -> None:
        if not hasattr(self, '_keyboard_listener'):
            self._create_listeners()
        self._ensure_listeners()

    def stop(self) -> None:
        self._keyboard_listener.stop()
        self._mouse_listener.stop()

    def _on_input(self, *args, **kwargs) -> None:
        with self._lock:
            self._last_input_ts = time.monotonic()

    def _ensure_listeners(self) -> None:
        if hasattr(self, '_keyboard_listener') and not self._keyboard_listener.is_alive():
            self._keyboard_listener = keyboard.Listener(on_press=self._on_input, on_release=self._on_input)
            self._keyboard_listener.start()
        if hasattr(self, '_mouse_listener') and not self._mouse_listener.is_alive():
            self._mouse_listener = mouse.Listener(on_move=self._on_input, on_click=self._on_input, on_scroll=self._on_input)
            self._mouse_listener.start()

    def _get_dbus_idle_seconds(self) -> float | None:
        try:
            from PyQt6.QtDBus import QDBusConnection, QDBusMessage
            bus = QDBusConnection.sessionBus()
            msg = QDBusMessage.createMethodCall(
                'org.gnome.Mutter.IdleMonitor',
                '/org/gnome/Mutter/IdleMonitor/Core',
                'org.gnome.Mutter.IdleMonitor',
                'GetIdletime'
            )
            reply = bus.call(msg)
            args = reply.arguments()
            if args:
                return float(args[0]) / 1000.0
        except Exception:
            pass
        return None

    def is_idle(self) -> bool:
        self._ensure_listeners()
        
        dbus_idle = self._get_dbus_idle_seconds()
        
        with self._lock:
            pynput_idle = time.monotonic() - self._last_input_ts
            
        if dbus_idle is not None:
            idle_seconds = min(pynput_idle, dbus_idle)
        else:
            idle_seconds = pynput_idle
            
        return idle_seconds >= self.idle_threshold_seconds

    def get_active_duration(self) -> int:
        with self._lock:
            return int(time.monotonic() - self._session_start_ts)

    def reset_timer(self) -> None:
        with self._lock:
            now = time.monotonic()
            self._session_start_ts = now
            self._last_input_ts = now
