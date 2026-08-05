from __future__ import annotations

import os
from typing import Optional


class WakeLock:
    """
    Prevents the system from suspending/sleeping while active.
    Uses the systemd logind D-Bus Inhibit interface.
    """

    def __init__(self, reason: str = "Active application task") -> None:
        self.reason = reason
        self._fd: Optional[int] = None

    def acquire(self) -> bool:
        """
        Attempt to acquire the wake lock.
        Returns True if successful or already held, False if failed.
        """
        if self._fd is not None:
            return True

        try:
            from PyQt6.QtDBus import QDBusConnection, QDBusMessage, QDBusUnixFileDescriptor

            bus = QDBusConnection.systemBus()
            if not bus.isConnected():
                return False

            msg = QDBusMessage.createMethodCall(
                "org.freedesktop.login1",
                "/org/freedesktop/login1",
                "org.freedesktop.login1.Manager",
                "Inhibit",
            )
            msg << "sleep" << "Neuropause" << self.reason << "block"

            reply = bus.call(msg)
            if reply.type() == QDBusMessage.MessageType.ErrorMessage:
                return False

            arg = reply.arguments()[0]
            if isinstance(arg, QDBusUnixFileDescriptor):
                # We dup the file descriptor to ensure we own its lifetime,
                # as PyQt might close the original when 'arg' is garbage collected.
                fd_num = arg.fileDescriptor()
                if fd_num >= 0:
                    self._fd = os.dup(fd_num)
                    return True

        except Exception as e:
            print(f"Failed to acquire wake lock: {e}")

        return False

    def release(self) -> None:
        """Release the wake lock if it is held."""
        if self._fd is not None:
            try:
                os.close(self._fd)
            except OSError:
                pass
            finally:
                self._fd = None
