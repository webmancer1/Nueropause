from __future__ import annotations

import os
from typing import Optional


class WakeLock:
    """
    Prevents the system from suspending/sleeping while active.
    Uses both the systemd logind D-Bus Inhibit interface and the
    freedesktop ScreenSaver interface for broader desktop environment support.
    """

    def __init__(self, reason: str = "Active application task") -> None:
        self.reason = reason
        self._fd: Optional[int] = None
        self._cookie: Optional[int] = None

    def acquire(self) -> bool:
        """
        Attempt to acquire the wake lock.
        Returns True if at least one inhibit method was successful or already held.
        """
        if self._fd is not None or self._cookie is not None:
            return True

        success = False
        try:
            from PyQt6.QtDBus import QDBusConnection, QDBusMessage, QDBusUnixFileDescriptor

            # 1. Try ScreenSaver (Session Bus) - Prevents idle/screen blanking in DEs (GNOME, KDE)
            session_bus = QDBusConnection.sessionBus()
            if session_bus.isConnected():
                msg = QDBusMessage.createMethodCall(
                    "org.freedesktop.ScreenSaver",
                    "/org/freedesktop/ScreenSaver",
                    "org.freedesktop.ScreenSaver",
                    "Inhibit",
                )
                msg << "Neuropause" << self.reason
                reply = session_bus.call(msg)
                if reply.type() != QDBusMessage.MessageType.ErrorMessage:
                    self._cookie = int(reply.arguments()[0])
                    success = True

            # 2. Try logind (System Bus) - Prevents sleep at the system level
            system_bus = QDBusConnection.systemBus()
            if system_bus.isConnected():
                msg = QDBusMessage.createMethodCall(
                    "org.freedesktop.login1",
                    "/org/freedesktop/login1",
                    "org.freedesktop.login1.Manager",
                    "Inhibit",
                )
                msg << "idle:sleep" << "Neuropause" << self.reason << "block"
                reply = system_bus.call(msg)
                
                if reply.type() != QDBusMessage.MessageType.ErrorMessage:
                    arg = reply.arguments()[0]
                    if isinstance(arg, QDBusUnixFileDescriptor):
                        fd_num = arg.fileDescriptor()
                        if fd_num >= 0:
                            self._fd = os.dup(fd_num)
                            success = True

        except Exception as e:
            print(f"Failed to acquire wake lock: {e}")

        return success

    def release(self) -> None:
        """Release the wake lock if it is held."""
        # Release logind inhibit
        if self._fd is not None:
            try:
                os.close(self._fd)
            except OSError:
                pass
            finally:
                self._fd = None
                
        # Release ScreenSaver inhibit
        if self._cookie is not None:
            try:
                from PyQt6.QtDBus import QDBusConnection, QDBusMessage
                session_bus = QDBusConnection.sessionBus()
                if session_bus.isConnected():
                    msg = QDBusMessage.createMethodCall(
                        "org.freedesktop.ScreenSaver",
                        "/org/freedesktop/ScreenSaver",
                        "org.freedesktop.ScreenSaver",
                        "UnInhibit",
                    )
                    msg << int(self._cookie)
                    session_bus.call(msg)
            except Exception as e:
                print(f"Failed to release ScreenSaver lock: {e}")
            finally:
                self._cookie = None
