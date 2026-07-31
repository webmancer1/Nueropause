from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import List

from PyQt6 import QtCore, QtGui, QtWidgets

from ..config import (
    BREAK_DURATION_SECONDS,
    PROMPT_ROTATE_SECONDS,
)
from ..engine.wellness_engine import WellnessEngine
from ..monitor.wake_lock import WakeLock


_GRAD_STOPS: list[tuple[float, QtGui.QColor]] = [
    (0.0,  QtGui.QColor(15,  23,  42)),   # slate-900
    (0.35, QtGui.QColor(30,  27,  75)),   # indigo-950
    (0.65, QtGui.QColor(12,  74,  110)),  # sky-900
    (1.0,  QtGui.QColor(15,  23,  42)),   # slate-900
]

_ACCENT   = QtGui.QColor(56,  189, 248)   # sky-400
_ACCENT2  = QtGui.QColor(167, 139, 250)   # violet-400
_ACCENT3  = QtGui.QColor(52,  211, 153)   # emerald-400
_WHITE    = QtGui.QColor(248, 250, 252)   # slate-50



PROMPT_META: dict[str, tuple[str, QtGui.QColor]] = {
    "Look 20 feet away for 20 seconds": ("👀", QtGui.QColor(56,  189, 248)),
    "Stretch":                           ("🤸", QtGui.QColor(167, 139, 250)),
    "Drink water":                       ("💧", QtGui.QColor(52,  211, 153)),
    "Deep breathing":                    ("🌬️", QtGui.QColor(251, 191,  36)),
    "Roll your shoulders back":          ("🔄", QtGui.QColor(248, 113, 113)),
    "Close your eyes and relax":         ("😌", QtGui.QColor(196, 181, 253)),
    "Stand up and walk around":          ("🚶", QtGui.QColor(110, 231, 183)),
    "Do 10 jumping jacks":               ("🏃", QtGui.QColor(253, 186,  64)),
    
}
_DEFAULT_META = ("✨", _ACCENT)



@dataclass
class _Particle:
    x: float
    y: float
    radius: float
    speed_y: float
    speed_x: float
    color: QtGui.QColor
    alpha: int
    phase: float          


def _random_particle(width: int, height: int) -> _Particle:
    colors = [_ACCENT, _ACCENT2, _ACCENT3]
    c = QtGui.QColor(random.choice(colors))
    
    if random.random() < 0.15:
        # Fast, bright darting particles
        speed_y = random.uniform(-1.5, -0.8)
        radius = random.uniform(1.5, 3.5)
        alpha = random.randint(150, 220)
    else:
        # Slow, floating orbs
        speed_y = random.uniform(-0.5, -0.15)
        radius = random.uniform(3, 10)
        alpha = random.randint(30, 100)

    return _Particle(
        x=random.uniform(0, width),
        y=random.uniform(0, height),
        radius=radius,
        speed_y=speed_y,
        speed_x=random.uniform(-0.2, 0.2),
        color=c,
        alpha=alpha,
        phase=random.uniform(0, 2 * math.pi),
    )


class BreakOverlay(QtWidgets.QWidget):
    break_finished = QtCore.pyqtSignal()

    _PARTICLE_COUNT = 55
    _RING_WIDTH      = 14
    _RING_RADIUS     = 130          

    def __init__(self, duration_seconds: int = BREAK_DURATION_SECONDS) -> None:
        super().__init__()
        self.duration_seconds  = duration_seconds
        self.remaining_seconds = duration_seconds
        self.wellness_engine   = WellnessEngine()
        self._wake_lock        = WakeLock("Break is currently active")

        
        self._current_emoji   = "✨"
        self._current_color   = _ACCENT
        self._current_prompt  = ""

        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint
            | QtCore.Qt.WindowType.WindowStaysOnTopHint
            | QtCore.Qt.WindowType.Tool
        )
        self.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)

       
        self._anim_t        = 0.0      
        self._breathe_t     = 0.0     
        self._particles: List[_Particle] = []

        self._anim_timer = QtCore.QTimer(self)
        self._anim_timer.setInterval(16)           
        self._anim_timer.timeout.connect(self._anim_tick)

        
        self._countdown_timer = QtCore.QTimer(self)
        self._countdown_timer.setInterval(1000)
        self._countdown_timer.timeout.connect(self._tick)

        self._prompt_timer = QtCore.QTimer(self)
        self._prompt_timer.setInterval(PROMPT_ROTATE_SECONDS * 1000)
        self._prompt_timer.timeout.connect(self._rotate_prompt_animated)

        
        self._fade_alpha = 0.0
        self._fade_anim = QtCore.QVariantAnimation(self)
        self._fade_anim.setDuration(600)
        self._fade_anim.setEasingCurve(QtCore.QEasingCurve.Type.InOutCubic)
        self._fade_anim.valueChanged.connect(self._on_fade_value_changed)
        self._fade_anim.finished.connect(self._on_fade_finished)
        self._fading_out = False

        self._build_ui()

    def _on_fade_value_changed(self, value: float) -> None:
        self._fade_alpha = value
        if hasattr(self, '_container_opacity'):
            self._container_opacity.setOpacity(value)
        self.update()

    def _on_prompt_alpha_changed(self, value: float) -> None:
        a = int(value * 255)
        c = self._current_color
        self._prompt_label.setStyleSheet(
            f"color: rgba({c.red()}, {c.green()}, {c.blue()}, {a}); background: transparent; letter-spacing: 0.3px;"
        )
        self._emoji_label.setStyleSheet(
            f"color: rgba(255, 255, 255, {a}); background: transparent;"
        )

    def _build_ui(self) -> None:
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._container = QtWidgets.QWidget()
        self._container_opacity = QtWidgets.QGraphicsOpacityEffect(self._container)
        self._container.setGraphicsEffect(self._container_opacity)
        self._container_opacity.setOpacity(0.0)
        root.addWidget(self._container)

        container_layout = QtWidgets.QVBoxLayout(self._container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        centre = QtWidgets.QWidget()
        centre.setStyleSheet("background: transparent;")
        col = QtWidgets.QVBoxLayout(centre)
        col.setContentsMargins(20, 40, 20, 40)
        col.setSpacing(0)

    
        self._title_label = QtWidgets.QLabel("Time for a break ☕")
        self._title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        font_title = QtGui.QFont("Sans Serif", 30, QtGui.QFont.Weight.Bold)
        self._title_label.setFont(font_title)
        self._title_label.setStyleSheet("color: #f8fafc; background: transparent; letter-spacing: 1px;")

    
        self._ring_canvas = _RingCanvas(
            radius=self._RING_RADIUS,
            ring_width=self._RING_WIDTH,
            parent=self,
        )
        self._ring_canvas.setFixedSize(340, 340)

        
        self._emoji_label = QtWidgets.QLabel("✨")
        self._emoji_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._emoji_label.setFont(QtGui.QFont("Sans Serif", 48))
        self._emoji_label.setStyleSheet("background: transparent;")

        
        self._prompt_label = QtWidgets.QLabel("")
        self._prompt_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._prompt_label.setFont(QtGui.QFont("Sans Serif", 22, QtGui.QFont.Weight.Medium))
        self._prompt_label.setWordWrap(True)
        self._prompt_label.setStyleSheet(f"color: {_ACCENT.name()}; background: transparent;")

        
        # Use QVariantAnimation for text alpha instead of QGraphicsOpacityEffect
        self._prompt_fade = QtCore.QVariantAnimation(self)
        self._prompt_fade.setDuration(400)
        self._prompt_fade.setEasingCurve(QtCore.QEasingCurve.Type.InOutSine)
        self._prompt_fade.valueChanged.connect(self._on_prompt_alpha_changed)
        self._prompt_fade.finished.connect(self._on_prompt_fade_step)
        self._pending_prompt: tuple[str, str, QtGui.QColor] | None = None
        self._fading_prompt_out = False


        sub = QtWidgets.QLabel("Step away · Recharge · Come back refreshed")
        sub.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        sub.setFont(QtGui.QFont("Sans Serif", 13))
        sub.setStyleSheet("color: rgba(148,163,184,200); background: transparent; letter-spacing: 0.5px;")

        self._skip_button = QtWidgets.QPushButton("Skip break (Esc)")
        self._skip_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._skip_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 10);
                color: rgba(255, 255, 255, 150);
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 18px;
                padding: 10px 24px;
                font-family: 'Sans Serif';
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 30);
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 80);
            }
        """)
        self._skip_button.clicked.connect(self._skip_break)

        col.addStretch(2)
        col.addWidget(self._title_label)
        col.addSpacing(20)
        col.addWidget(self._ring_canvas, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        col.addSpacing(20)
        col.addWidget(self._emoji_label)
        col.addSpacing(8)
        col.addWidget(self._prompt_label)
        col.addSpacing(16)
        col.addWidget(sub)
        col.addSpacing(30)
        col.addWidget(self._skip_button, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        col.addStretch(3)

        container_layout.addWidget(centre)
        self.setLayout(root)

 
    def start(self) -> None:
        self._wake_lock.acquire()
        
        self.remaining_seconds  = self.duration_seconds
        self._fading_out        = False

        
        self._fade_anim.stop()
        self._prompt_fade.stop()
        self._fading_prompt_out = False
        self._pending_prompt    = None
        self._on_prompt_alpha_changed(0.0)
        self._fade_alpha = 0.0
        if hasattr(self, '_container_opacity'):
            self._container_opacity.setOpacity(0.0)

        screen = QtWidgets.QApplication.primaryScreen()
        if screen:
            geo = screen.geometry()
            self.setGeometry(geo)

        
        self._particles = [
            _random_particle(self.width() or 1920, self.height() or 1080)
            for _ in range(self._PARTICLE_COUNT)
        ]

        self._update_ring()

        self.showFullScreen()
        self.raise_()
        self.activateWindow()

    
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.start()

        self._anim_timer.start()
        self._countdown_timer.start()
        self._prompt_timer.start()

        
        self._show_next_prompt()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        event.ignore()   

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() == QtCore.Qt.Key.Key_Escape:
            self._skip_break()
        else:
            super().keyPressEvent(event)

    def _skip_break(self) -> None:
        if not self._fading_out:
            self.remaining_seconds = 0
            self._finish()

    
    def paintEvent(self, _: QtGui.QPaintEvent) -> None:  
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()

        
        angle_rad = math.radians(135 + 20 * math.sin(self._anim_t * 0.3))
        cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
        cx, cy = w / 2, h / 2
        length = math.hypot(w, h) / 2
        x1 = cx - cos_a * length
        y1 = cy - sin_a * length
        x2 = cx + cos_a * length
        y2 = cy + sin_a * length

        grad = QtGui.QLinearGradient(x1, y1, x2, y2)
        
        drift = (math.sin(self._anim_t * 0.15) + 1) / 2  # 0..1
        for pos, base_col in _GRAD_STOPS:
            h_hue   = (base_col.hsvHue()   + int(drift * 30)) % 360
            h_sat   = base_col.hsvSaturation()
            h_val   = base_col.value()
            shifted = QtGui.QColor.fromHsv(h_hue, h_sat, h_val)
            shifted.setAlphaF(self._fade_alpha)
            grad.setColorAt(pos, shifted)

        p.fillRect(0, 0, w, h, grad)

        
        for part in self._particles:
            wobble_x = part.x + 10 * math.sin(self._anim_t * 0.8 + part.phase)
            c = QtGui.QColor(part.color)
            c.setAlpha(int(part.alpha * self._fade_alpha))
            
            r = part.radius * (0.8 + 0.3 * math.sin(self._anim_t * 2.0 + part.phase))
            
            # Glow effect for particles
            p_grad = QtGui.QRadialGradient(wobble_x, part.y, r)
            p_grad.setColorAt(0.0, c)
            c_trans = QtGui.QColor(c)
            c_trans.setAlpha(0)
            p_grad.setColorAt(1.0, c_trans)
            
            p.setBrush(QtGui.QBrush(p_grad))
            p.setPen(QtCore.Qt.PenStyle.NoPen)
            p.drawEllipse(QtCore.QPointF(wobble_x, part.y), r, r)

        p.end()

   
    def _anim_tick(self) -> None:
        self._anim_t    += 0.016          
        self._breathe_t += 0.016

        w, h = self.width() or 1920, self.height() or 1080

        
        for part in self._particles:
            part.y += part.speed_y
            part.x += part.speed_x
            if part.y < -part.radius * 2:
                part.y = h + part.radius
                part.x = random.uniform(0, w)

        
        pulse = (math.sin(self._breathe_t * 2.5) + 1) / 2  # 0..1
        r = int(_ACCENT.red()   + pulse * (_ACCENT2.red()   - _ACCENT.red()))
        g = int(_ACCENT.green() + pulse * (_ACCENT2.green() - _ACCENT.green()))
        b = int(_ACCENT.blue()  + pulse * (_ACCENT2.blue()  - _ACCENT.blue()))
        self._ring_canvas.set_ring_color(QtGui.QColor(r, g, b))

        self.update()           
        self._ring_canvas.update()


    def _tick(self) -> None:
        self.remaining_seconds -= 1
        if self.remaining_seconds <= 0:
            self._finish()
            return
        self._update_ring()

    def _update_ring(self) -> None:
        fraction = self.remaining_seconds / max(1, self.duration_seconds)
        self._ring_canvas.set_progress(fraction, self._format_time(self.remaining_seconds))

    
    def _show_next_prompt(self) -> None:
        """Load the next prompt and fade it in from scratch (no fade-out step)."""
        state = self.wellness_engine.next_prompt()
        emoji, color = PROMPT_META.get(state.prompt, _DEFAULT_META)
        self._current_prompt = state.prompt
        self._current_emoji  = emoji
        self._current_color  = color
        self._pending_prompt = None

        self._prompt_label.setText(state.prompt)
        self._emoji_label.setText(emoji)
        
        self._on_prompt_alpha_changed(0.0)

        self._fading_prompt_out = False
        self._prompt_fade.stop()
        self._prompt_fade.setStartValue(0.0)
        self._prompt_fade.setEndValue(1.0)
        self._prompt_fade.start()

    def _rotate_prompt_animated(self) -> None:
        """Called by _prompt_timer — cross-fades to the next prompt."""
        state  = self.wellness_engine.next_prompt()
        emoji, color = PROMPT_META.get(state.prompt, _DEFAULT_META)
        self._pending_prompt = (state.prompt, emoji, color)

    
        self._fading_prompt_out = True
        self._prompt_fade.stop()
        current_val = self._prompt_fade.currentValue() if self._prompt_fade.state() == QtCore.QAbstractAnimation.State.Running else 1.0
        self._prompt_fade.setStartValue(float(current_val))
        self._prompt_fade.setEndValue(0.0)
        self._prompt_fade.start()

    def _on_prompt_fade_step(self) -> None:
        if not self._fading_prompt_out or self._pending_prompt is None:
            return   

        text, emoji, color = self._pending_prompt
        self._pending_prompt = None
        self._current_prompt = text
        self._current_emoji  = emoji
        self._current_color  = color

        self._prompt_label.setText(text)
        self._emoji_label.setText(emoji)

        
        self._fading_prompt_out = False
        self._prompt_fade.stop()
        self._prompt_fade.setStartValue(0.0)
        self._prompt_fade.setEndValue(1.0)
        self._prompt_fade.start()

   
    def _finish(self) -> None:
        self._countdown_timer.stop()
        self._prompt_timer.stop()
        self._anim_timer.stop()

        self._fading_out = True
        self._fade_anim.stop()
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.start()

    def _on_fade_finished(self) -> None:
        if self._fading_out:
            self._fading_out = False          
            self.hide()
            self._fade_alpha = 0.0
            if hasattr(self, '_container_opacity'):
                self._container_opacity.setOpacity(0.0)  
            self._wake_lock.release()
            self.break_finished.emit()

    
    @staticmethod
    def _format_time(seconds: int) -> str:
        m = seconds // 60
        s = seconds % 60
        return f"{m:02d}:{s:02d}"



class _RingCanvas(QtWidgets.QWidget):
    def __init__(self, radius: int, ring_width: int, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._radius     = radius
        self._ring_width = ring_width
        self._progress   = 1.0          
        self._text       = "00:00"
        self._ring_color = _ACCENT
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setStyleSheet("background: transparent;")

    def set_progress(self, fraction: float, text: str) -> None:
        self._progress = fraction
        self._text     = text
        self.update()

    def set_ring_color(self, color: QtGui.QColor) -> None:
        self._ring_color = color

    def paintEvent(self, _: QtGui.QPaintEvent) -> None:  
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        cx = self.width()  / 2
        cy = self.height() / 2
        
        # Breathe the ring radius slightly
        breathe = 0.0
        if hasattr(self.parent(), '_breathe_t'):
            breathe = self.parent()._breathe_t
            
        r  = self._radius + 2.5 * math.sin(breathe * 2.0)

        # 1. Pulsating Aura Behind the ring
        aura_radius = r + self._ring_width + 5 + 8 * math.sin(breathe * 3.0)
        if aura_radius > 0:
            aura_grad = QtGui.QRadialGradient(cx, cy, aura_radius)
            aura_c = QtGui.QColor(self._ring_color)
            aura_c.setAlpha(int(20 + 15 * math.sin(breathe * 1.5)))
            aura_grad.setColorAt(0.7, aura_c)
            aura_c.setAlpha(0)
            aura_grad.setColorAt(1.0, aura_c)
            
            p.setBrush(QtGui.QBrush(aura_grad))
            p.setPen(QtCore.Qt.PenStyle.NoPen)
            p.drawEllipse(QtCore.QPointF(cx, cy), aura_radius, aura_radius)

        # 2. Central Glow Behind Text
        bg_grad = QtGui.QRadialGradient(cx, cy, r)
        bg_c = QtGui.QColor(self._ring_color)
        bg_c.setAlpha(30)
        bg_grad.setColorAt(0.0, bg_c)
        bg_c.setAlpha(0)
        bg_grad.setColorAt(1.0, bg_c)
        p.setBrush(QtGui.QBrush(bg_grad))
        p.setPen(QtCore.Qt.PenStyle.NoPen)
        p.drawEllipse(QtCore.QPointF(cx, cy), r, r)

        # 3. Inner Dashed Dial (Watch-face style)
        inner_r = r - self._ring_width - 12
        if inner_r > 0:
            dial_color = QtGui.QColor(255, 255, 255, 40)
            dial_pen = QtGui.QPen(dial_color, 2)
            dial_pen.setDashPattern([2, 6])
            p.setPen(dial_pen)
            p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            p.drawEllipse(QtCore.QPointF(cx, cy), inner_r, inner_r)
        
        # 4. Outer Dashed Dial
        outer_r = r + self._ring_width + 8
        if outer_r > 0:
            dial_color = QtGui.QColor(self._ring_color.red(), self._ring_color.green(), self._ring_color.blue(), 50)
            dial_pen = QtGui.QPen(dial_color, 1.5)
            dial_pen.setDashPattern([1, 4])
            p.setPen(dial_pen)
            p.drawEllipse(QtCore.QPointF(cx, cy), outer_r, outer_r)

        # 5. Track Groove
        track_color = QtGui.QColor(0, 0, 0, 60)
        pen_track = QtGui.QPen(track_color, self._ring_width, QtCore.Qt.PenStyle.SolidLine,
                               QtCore.Qt.PenCapStyle.RoundCap)
        p.setPen(pen_track)
        p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        rect = QtCore.QRectF(cx - r, cy - r, r * 2, r * 2)
        p.drawEllipse(rect)
        
        # Inner Track highlight (glassy effect)
        track_hl = QtGui.QColor(255, 255, 255, 10)
        pen_hl = QtGui.QPen(track_hl, self._ring_width - 4, QtCore.Qt.PenStyle.SolidLine, QtCore.Qt.PenCapStyle.RoundCap)
        p.setPen(pen_hl)
        p.drawEllipse(rect)

        # 6. Progress Arc with Conical Gradient (Comet tail effect)
        span = int(self._progress * 360 * 16)    
        if span > 0:
            tip_angle_deg = 90 - self._progress * 360
            conic = QtGui.QConicalGradient(cx, cy, tip_angle_deg)
            c_head = QtGui.QColor(self._ring_color)
            c_tail = QtGui.QColor(self._ring_color)
            c_tail.setAlpha(20) # Fade out to tail
            
            conic.setColorAt(0.0, c_head)
            if self._progress > 0.01:
                conic.setColorAt(self._progress, c_tail)
                conic.setColorAt(min(1.0, self._progress + 0.001), QtGui.QColor(0,0,0,0))
            
            pen_arc = QtGui.QPen(QtGui.QBrush(conic), self._ring_width,
                                 QtCore.Qt.PenStyle.SolidLine,
                                 QtCore.Qt.PenCapStyle.RoundCap)
            p.setPen(pen_arc)
            p.drawArc(rect, 90 * 16, -span)      

        # 7. Leading Orb at the tip
        if self._progress > 0.01:
            tip_rad = math.radians(tip_angle_deg)
            tip_x = cx + r * math.cos(tip_rad)
            tip_y = cy - r * math.sin(tip_rad)
            
            # Glow
            glow = QtGui.QRadialGradient(tip_x, tip_y, self._ring_width * 2.0)
            glow_col = QtGui.QColor(self._ring_color)
            glow_col.setAlpha(200)
            glow.setColorAt(0.0, glow_col)
            glow.setColorAt(1.0, QtGui.QColor(0, 0, 0, 0))
            p.setPen(QtCore.Qt.PenStyle.NoPen)
            p.setBrush(QtGui.QBrush(glow))
            hw = self._ring_width * 2.0
            p.drawEllipse(QtCore.QPointF(tip_x, tip_y), hw, hw)
            
            # Bright Core
            p.setBrush(QtGui.QBrush(QtGui.QColor(255, 255, 255)))
            p.drawEllipse(QtCore.QPointF(tip_x, tip_y), self._ring_width * 0.25, self._ring_width * 0.25)

        # 8. Text with Drop Shadow
        p.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 150)))
        font = QtGui.QFont("Sans Serif", 36, QtGui.QFont.Weight.Bold)
        p.setFont(font)
        text_rect = QtCore.QRectF(cx - r, cy - r, r * 2, r * 2)
        
        # Draw shadow
        shadow_rect = text_rect.translated(2, 2)
        p.drawText(shadow_rect, QtCore.Qt.AlignmentFlag.AlignCenter, self._text)
        
        # Draw text
        p.setPen(QtGui.QPen(_WHITE))
        p.drawText(text_rect, QtCore.Qt.AlignmentFlag.AlignCenter, self._text)

        p.end()
