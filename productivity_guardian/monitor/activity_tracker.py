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

    def is_idle(self) -> bool:
        self._ensure_listeners()
        with self._lock:
            idle_seconds = time.monotonic() - self._last_input_ts
        return idle_seconds >= self.idle_threshold_seconds

    def get_active_duration(self) -> int:
        with self._lock:
            return int(time.monotonic() - self._session_start_ts)

    def reset_timer(self) -> None:
        with self._lock:
            now = time.monotonic()
            self._session_start_ts = now
            self._last_input_ts = now
