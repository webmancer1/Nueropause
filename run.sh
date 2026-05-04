#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Productivity Guardian — launcher
# Designed for both X11 and Wayland (GNOME/Fedora).
# Run this script to start the app; it detaches from the terminal so closing
# the terminal does NOT kill the app.
# ---------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/.venv"
LOG_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/productivity-guardian"
LOG_FILE="$LOG_DIR/app.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Source the virtual-environment
if [[ ! -f "$VENV/bin/python" ]]; then
    echo "ERROR: venv not found at $VENV" >&2
    exit 1
fi

# Prevent duplicate instances
if pgrep -f "productivity_guardian.main" > /dev/null 2>&1; then
    echo "Productivity Guardian is already running." >&2
    exit 0
fi

# ---------------------------------------------------------------------------
# Wayland / X11 display detection
# On Wayland, PyQt6 needs QT_QPA_PLATFORM=wayland (or xcb as fallback).
# We also ensure DBUS_SESSION_BUS_ADDRESS is available.
# ---------------------------------------------------------------------------
if [[ -z "$WAYLAND_DISPLAY" && -z "$DISPLAY" ]]; then
    # Try to discover the Wayland display for the current user from systemd
    eval "$(systemctl --user show-environment 2>/dev/null | grep -E '^(WAYLAND_DISPLAY|DISPLAY|DBUS_SESSION_BUS_ADDRESS|XDG_RUNTIME_DIR)=')" 2>/dev/null || true
fi

# Prefer Wayland backend; fall back to xcb (X11) if Wayland socket not found
if [[ -n "$WAYLAND_DISPLAY" ]]; then
    export QT_QPA_PLATFORM="wayland;xcb"
else
    export QT_QPA_PLATFORM="xcb"
fi

# Suppress Qt accessibility bridge warnings (harmless on Wayland)
export QT_ACCESSIBILITY=1
export NO_AT_BRIDGE=1

echo "[$(date -Iseconds)] Starting Productivity Guardian (platform: $QT_QPA_PLATFORM)..." >> "$LOG_FILE"

# PYTHONPATH must include the project root so Python can find the
# 'productivity_guardian' package regardless of the working directory
# (critical when launched from autostart/systemd where CWD != project root)
export PYTHONPATH="$SCRIPT_DIR:${PYTHONPATH:-}"

# Launch detached from terminal; nohup + setsid ensure it outlives the shell
nohup setsid "$VENV/bin/python" -m productivity_guardian.main \
    >> "$LOG_FILE" 2>&1 &

echo "Started (PID $!). Logs: $LOG_FILE"
