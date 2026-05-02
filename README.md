<div align="center">

# 🧠 Neuropause
### *Productivity Guardian*

**A lightweight, always-on break reminder for Linux desktops.**  
Monitors your active work time and nudges you to rest before fatigue sets in.

![Python](https://img.shields.io/badge/Python-3.14-blue?style=flat-square&logo=python)
![PyQt6](https://img.shields.io/badge/PyQt6-6.11-green?style=flat-square&logo=qt)
![Platform](https://img.shields.io/badge/Platform-Linux%20%28X11%29-orange?style=flat-square&logo=linux)
![License](https://img.shields.io/badge/License-MIT-purple?style=flat-square)

</div>

---

## ✨ What it does

Neuropause sits quietly in your **system tray** and tracks how long you've been working. After your configured work period (default: 50 min), it takes over the screen with a calming full-screen overlay that counts down your break and rotates wellness prompts — reminding you to rest your eyes, stretch, or drink water.

When the break is done, it gets out of your way and the cycle resets.

---

## 🖥️ Features

| Feature | Details |
|---|---|
| 🕐 **Work-period tracking** | Counts active keyboard/mouse time; pauses automatically when you're idle |
| 🌑 **Full-screen break overlay** | Dark, distraction-free overlay with a live countdown timer |
| 💡 **Wellness prompts** | Rotating reminders: eye exercises, stretching, hydration, breathing |
| ⚙️ **Adjustable timers** | Set your own work period (1–180 min) and break duration (1–60 min) via the tray menu |
| 🔔 **System tray icon** | Pause monitoring, trigger a break immediately, or open settings — all from the tray |
| 🚀 **Auto-start on login** | Installed as an XDG autostart entry; launches automatically every time you log in |
| 🗄️ **Session logging** | Every break is recorded to a local SQLite database for future reference |
| 📋 **Crash-safe logging** | Logs to `~/.local/share/productivity-guardian/app.log` |

---

## 📁 Project Structure

```
Neuropause/
├── run.sh                          # Detached launcher (use this to start the app)
├── productivity_guardian/
│   ├── main.py                     # App entry-point & system tray logic
│   ├── config.py                   # All tunable constants
│   ├── database.py                 # SQLite session logger
│   ├── engine/
│   │   ├── rule_engine.py          # Decides when to trigger a break
│   │   └── wellness_engine.py      # Rotates wellness prompts
│   ├── monitor/
│   │   └── activity_tracker.py     # Keyboard/mouse idle detection (pynput)
│   └── ui/
│       ├── break_overlay.py        # Full-screen break countdown widget
│       └── settings_dialog.py      # Tray → Settings… dialog
└── .venv/                          # Python virtual environment
```

---

## ⚡ Quick Start

### 1. Clone & enter the project

```bash
git clone https://github.com/your-username/neuropause.git
cd neuropause
```

### 2. Create the virtual environment

```bash
python3 -m venv .venv
```

### 3. Install dependencies

```bash
.venv/bin/pip install -r productivity_guardian/requirements.txt
```

> **Note (Fedora/RHEL):** `pynput` needs `python3-devel` to build its `evdev` backend. Install it with:
> ```bash
> sudo dnf install python3-devel
> ```
> Without it, pynput falls back to the **xlib** backend (already included via `python-xlib`) which works fine.

### 4. Run it

```bash
./run.sh
```

The app starts in the background and appears as a **system tray icon**. Close the terminal — it keeps running.

---

## 🔄 Auto-start on Login (already installed)

An XDG autostart entry is created at:

```
~/.config/autostart/productivity-guardian.desktop
```

GNOME reads this at login and launches the app automatically, **10 seconds after your desktop loads**. No manual steps needed after the first run.

```bash
# Confirm it's registered
ls ~/.config/autostart/productivity-guardian.desktop

# Disable auto-start (without deleting)
# Go to: GNOME Settings → Apps → Startup Applications
```

---

## ⚙️ Configuring Timers

**Via the tray icon (recommended):**

Right-click the tray icon → **Settings…**

| Setting | Default | Range |
|---|---|---|
| Work period | 50 min | 1 – 180 min |
| Break duration | 10 min | 1 – 60 min |

Changes apply **immediately** — no restart needed.

**Via `config.py` (permanent defaults):**

```python
# productivity_guardian/config.py

IDLE_THRESHOLD_SECONDS        = 5 * 60   # Idle after 5 min of no input
ACTIVE_SESSION_THRESHOLD_SECONDS = 50 * 60  # Trigger break after 50 min active
BREAK_DURATION_SECONDS        = 10 * 60  # Break lasts 10 min
PROMPT_ROTATE_SECONDS         = 10       # Wellness prompt changes every 10 s
```

---

## 🧰 Tray Menu Reference

| Action | Description |
|---|---|
| **Pause monitoring** | Toggles the activity tracker off; no breaks will trigger while paused |
| **Start break now** | Immediately shows the break overlay |
| **Settings…** | Opens the timer configuration dialog |
| **Quit** | Cleanly stops all threads and exits |

---

## 🛠️ Useful Commands

```bash
# Start the app (detached from terminal)
./run.sh

# Check if it's currently running
pgrep -f productivity_guardian.main

# Stop it manually
pkill -f productivity_guardian.main

# Tail the live log
tail -f ~/.local/share/productivity-guardian/app.log

# Run directly (attached to terminal, useful for debugging)
.venv/bin/python -m productivity_guardian.main
```

---

## 📦 Dependencies

| Package | Version | Purpose |
|---|---|---|
| `PyQt6` | ≥ 6.11 | GUI framework (tray icon, overlay, dialogs) |
| `pynput` | ≥ 1.8 | Keyboard & mouse event listener |
| `psutil` | ≥ 7.0 | System utilities |
| `python-xlib` | ≥ 0.33 | X11 backend for pynput on Linux |
| `six` | ≥ 1.17 | Required by python-xlib |

---

## 🗄️ Data Storage

All data is stored locally — nothing is sent anywhere.

| File | Location |
|---|---|
| Session database | `~/.local/share/productivity-guardian/sessions.db` |
| Application log | `~/.local/share/productivity-guardian/app.log` |

---

## 🩺 Wellness Prompts

The break overlay cycles through these reminders during your break:

- 👁️ **Look 20 feet away for 20 seconds** *(20-20-20 rule for eye strain)*
- 🧘 **Stretch**
- 💧 **Drink water**
- 🌬️ **Deep breathing**

You can add or edit prompts in `config.py`:

```python
WELLNESS_PROMPTS = [
    "Look 20 feet away for 20 seconds",
    "Stretch",
    "Drink water",
    "Deep breathing",
    # Add your own here...
]
```

---

## 📄 License

MIT — do whatever you like with it.

---

<div align="center">

Made with 🧠 to protect your focus and your health.

</div>
