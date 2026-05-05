<div align="center">

#  Neuropause
### *Productivity Guardian*

**A lightweight, always-on break reminder for Linux desktops.**  
Monitors your active work time and nudges you to rest before fatigue sets in.

</div>

---

##  What it does

Neuropause sits quietly in your **system tray** and tracks how long you've been working. After your configured work period (default: 50 min), it takes over the screen with an animated full-screen overlay that counts down your break and rotates wellness prompts.

**Three minutes before the break**, a system notification pops up so you can wrap up your thoughts. When the break is done, everything resets automatically and the cycle starts again.

---

##  Features

| Feature | Details |
|---|---|
| ⏱ **Live tray countdown** | The tray menu shows a live `MM:SS` countdown to your next break, updating every second |
| 🔔 **3-minute pre-break alert** | A system notification fires once when 3 minutes remain — so you're never caught off guard |
| 🎬 **Animated break overlay** | Full-screen overlay with animated gradient background, floating particles, pulsing progress ring, and smooth fade in/out |
| 🤸 **Wellness prompts with emoji** | 10 rotating prompts (eye exercises, stretching, hydration, breathing, jumping jacks, and more), each with a unique emoji and accent colour that cross-fade on rotation |
| 🎯 **Work-period tracking** | Counts elapsed work time; if you step away for an entire work period the timer silently resets so you start fresh on return |
| ⚙️ **Adjustable timers** | Set your own work period (1–180 min) and break duration (1–60 min) via the tray menu; changes apply immediately |
| 🖥️ **System tray icon** | Pause monitoring, trigger a break immediately, or open settings — all from the tray |
| 🌙 **Sleep/suspend aware** | Detects system wake events; resets the work timer and dismisses any in-progress overlay |
| 💾 **Session logging** | Every break is recorded to a local SQLite database |
| 📋 **Crash-safe logging** | Logs to `~/.local/share/productivity-guardian/app.log` |
| 🚀 **Auto-start on login** | Installed as an XDG autostart entry; launches automatically every time you log in |

---

##  Quick Start

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

> **Note (Fedora/RHEL):** `pynput` needs `python3-devel` to build its `evdev` backend:
> ```bash
> sudo dnf install python3-devel
> ```
> Without it, pynput falls back to the **xlib** backend (already included via `python-xlib`) which works fine.

### 4. Run it

```bash
bash run.sh
```

The app starts in the background and appears as a **system tray icon**. Close the terminal — it keeps running.

---

##  Tray Menu Reference

Right-click the tray icon to access:

| Item | Description |
|---|---|
| ⏱ **Next break in MM:SS** | Live countdown display (non-clickable) |
| **Pause monitoring** | Toggles the work timer off; no breaks will trigger while paused |
| **Start break now** | Immediately shows the animated break overlay |
| **Settings…** | Opens the timer configuration dialog |
| **Quit** | Cleanly stops all timers and exits |

### Tray states

| Display | Meaning |
|---|---|
| `⏱ Next break in 47:23` | Normal — counting down to next break |
| `☕ Break in progress…` | Break overlay is currently active |
| `⏸ Monitoring paused` | Monitoring has been manually paused |

---

##  Configuring Timers

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

IDLE_THRESHOLD_SECONDS           = 5 * 60    # Considered idle after 5 min of no input
ACTIVE_SESSION_THRESHOLD_SECONDS = 50 * 60   # Trigger break after 50 min
BREAK_DURATION_SECONDS           = 10 * 60   # Break lasts 10 min
PROMPT_ROTATE_SECONDS            = 10        # Wellness prompt rotates every 10 s
```

---

##  Break Overlay

The break screen is fully animated:

- **Gradient background** — a deep-space colour palette (slate → indigo → sky) that slowly shifts and rotates over time
- **Floating particles** — 55 soft glowing bubbles drift upward in sky-blue, violet, and emerald
- **Progress ring** — an arc around the countdown timer that shrinks clockwise as time runs out, with a glowing tip and a colour that pulses between sky-blue and violet
- **Wellness prompt** — each prompt has a matching emoji and unique accent colour; prompts cross-fade when they rotate
- **Fade in / fade out** — the overlay smoothly fades in on start and fades out when the break ends

---

##  Wellness Prompts

The break overlay cycles through these reminders:

| Prompt | Emoji |
|---|---|
| Look 20 feet away for 20 seconds | 👀 |
| Stretch | 🤸 |
| Drink water | 💧 |
| Deep breathing | 🌬️ |
| Roll your shoulders back | 🔄 |
| Close your eyes and relax | 😌 |
| Stand up and walk around | 🚶 |
| Do 10 jumping jacks | 🏃 |
| Wiggle your fingers and toes | 🖐️ |
| Smile — you're doing great! | 😊 |

Add your own prompts in `config.py`:

```python
WELLNESS_PROMPTS = [
    "Look 20 feet away for 20 seconds",
    "Stretch",
    # ... add your own here
]
```

---

##  Useful Commands

```bash
# Start the app (detached from terminal)
bash run.sh

# Check if it's currently running
pgrep -f productivity_guardian.main

# Stop it
pkill -f productivity_guardian.main

# Restart
pkill -f productivity_guardian.main; bash run.sh

# Tail the live log
tail -f ~/.local/share/productivity-guardian/app.log

# Run directly (attached to terminal, useful for debugging)
.venv/bin/python -m productivity_guardian.main
```

---

##  Dependencies

| Package | Version | Purpose |
|---|---|---|
| `PyQt6` | ≥ 6.11 | GUI framework (tray icon, overlay, dialogs, animations) |
| `pynput` | ≥ 1.8 | Keyboard & mouse event listener |
| `psutil` | ≥ 7.0 | System utilities (used by sleep monitor) |
| `python-xlib` | ≥ 0.33 | X11 backend for pynput on Linux |
| `six` | ≥ 1.17 | Required by python-xlib |

---

##  Data Storage

All data is stored **locally** — nothing is sent anywhere.

| File | Location |
|---|---|
| Session database | `~/.local/share/productivity-guardian/sessions.db` |
| Application log | `~/.local/share/productivity-guardian/app.log` |

---

##  How the Break Trigger Works

1. The work timer counts elapsed wall-clock time from the last reset
2. At **T-3 minutes** a system notification fires once (one-shot per cycle)
3. At **T=0** the animated break overlay appears automatically
4. If you were **idle for the entire work period** (e.g. away from desk), the timer resets silently — no break ambush when you return
5. After the break, `break_finished` is emitted, the timer resets, and the cycle restarts
