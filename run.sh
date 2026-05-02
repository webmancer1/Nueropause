#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Productivity Guardian — launcher
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

echo "[$(date -Iseconds)] Starting Productivity Guardian..." >> "$LOG_FILE"

# Launch detached from terminal; nohup + setsid ensure it outlives the shell
nohup setsid "$VENV/bin/python" -m productivity_guardian.main \
    >> "$LOG_FILE" 2>&1 &

echo "Started (PID $!). Logs: $LOG_FILE"
