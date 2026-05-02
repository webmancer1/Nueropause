from __future__ import annotations

import os
from pathlib import Path

# Configurable constants for Productivity Guardian
APP_NAME = "Productivity Guardian"
TRAY_TOOLTIP = "Productivity Guardian"

# Activity thresholds (seconds)
IDLE_THRESHOLD_SECONDS = 5 * 60
ACTIVE_SESSION_THRESHOLD_SECONDS = 50 * 60
BREAK_DURATION_SECONDS = 10 * 60

# Wellness prompts
WELLNESS_PROMPTS = [
    "Look 20 feet away for 20 seconds",
    "Stretch",
    "Drink water",
    "Deep breathing",
]

# Database — stored in ~/.local/share/productivity-guardian/ so the path is
# stable regardless of which directory the app is launched from.
_DATA_DIR = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "productivity-guardian"
_DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = str(_DATA_DIR / "sessions.db")

# Overlay appearance
OVERLAY_BG_COLOR = "#0f172a"
OVERLAY_TEXT_COLOR = "#f8fafc"
OVERLAY_ACCENT_COLOR = "#38bdf8"

# Prompt rotation interval (seconds)
PROMPT_ROTATE_SECONDS = 10
