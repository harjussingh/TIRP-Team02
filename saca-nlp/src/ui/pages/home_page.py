from PySide6.QtCore import (
    Qt, Signal, QPropertyAnimation, QEasingCurve,
    QTimer, Property,
)
from src.ui.widgets.help_popup import HelpButton
from PySide6.QtGui import (
    QPainter, QPen, QColor, QFont, QLinearGradient, QBrush,
    QPainterPath, QPixmap,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QStackedWidget, QSizePolicy, QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
)
import os
from src.utils.audio import play as _play, play_sequence as _play_sequence, stop_all as _stop_all


# ──────────────────────────────────────────────────────────────────
#  Lottie animation widget (renders via rlottie-python)
# ──────────────────────────────────────────────────────────────────
class LottieWidget(QWidget):
    """
    Renders a real Lottie JSON animation using QWebEngineView + lottie-web JS.
    The bundled lottie.min.js lives at  assets/js/lottie.min.js  so no internet
    access is required.
    """
    def __init__(self, json_path: str = "", size: int = 120, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)

        try:
            from PySide6.QtWebEngineWidgets import QWebEngineView
            from PySide6.QtWebEngineCore import QWebEngineSettings
            import json as _json

            # Resolve paths
            _here = os.path.dirname(os.path.abspath(__file__))
            _lottie_js = os.path.normpath(
                os.path.join(_here, "..", "..", "..", "assets", "js", "lottie.min.js")
            )
            # Read and inline both files so the page is fully self-contained
            with open(_lottie_js, "r", encoding="utf-8") as f:
                _js_src = f.read()
            with open(json_path, "r", encoding="utf-8") as f:
                _anim_data = f.read()

            _html = f"""<!DOCTYPE html>
<html><head><meta charset='utf-8'>
<style>*{{margin:0;padding:0;overflow:hidden;background:transparent}}
 body{{width:{size}px;height:{size}px}}
 #c{{width:{size}px;height:{size}px}}</style></head>
<body><div id='c'></div>
<script>{_js_src}</script>
<script>
lottie.loadAnimation({{
  container: document.getElementById('c'),
  renderer: 'svg',
  loop: true,
  autoplay: true,
  animationData: {_anim_data}
}});
</script></body></html>"""

            self._view = QWebEngineView(self)
            self._view.setFixedSize(size, size)
            # Transparent background
            self._view.page().setBackgroundColor(Qt.transparent)
            settings = self._view.page().settings()
            settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
            self._view.setHtml(_html)
        except Exception as e:
            print(f"[SACA] LottieWidget failed: {e}")
            self._view = None




class AnimatedWelcomeLabel(QLabel):
    """
    Typewriter reveal, then looping lub-dub heartbeat scale.
    Uses a cached QPixmap so we can scale without a double-painter crash.
    """
    def __init__(self, text: str, parent=None):
        super().__init__("", parent)
        self._full_text = text
        self._char_idx  = 0
        self._scale     = 1.0
        self._hb_phase  = 0
        self._hb_t      = 0.0
        self._cache_pm  = None   # QPixmap snapshot taken after typing finishes
        self._caching   = False  # guard against re-entrant grab

        self._type_timer = QTimer(self)
        self._type_timer.setInterval(140)
        self._type_timer.timeout.connect(self._type_tick)

        self._hb_timer = QTimer(self)
        self._hb_timer.setInterval(33)
        self._hb_timer.timeout.connect(self._hb_tick)

    def play(self):
        QTimer.singleShot(200, self._type_timer.start)

    def _type_tick(self):
        self._char_idx += 1
        self.setText(self._full_text[: self._char_idx])
        if self._char_idx >= len(self._full_text):
            self._type_timer.stop()
            # Let the final setText paint once, then grab a snapshot
            QTimer.singleShot(80, self._build_cache)

    def _build_cache(self):
        """Grab the label as-is into a pixmap, then start heartbeat."""
        self._caching = True
        self._cache_pm = self.grab()   # safe here — not inside paintEvent
        self._caching = False
        QTimer.singleShot(400, self._hb_timer.start)

    # lub-dub: (target_scale, frames_at_30fps)
    _HB = [
        (1.20, 5),   # lub — quick expand
        (1.00, 7),   # back
        (1.12, 4),   # dub — softer bump
        (1.00, 6),   # back
        (1.00, 52),  # rest ~1.7 s
    ]

    def _hb_tick(self):
        target, frames = self._HB[self._hb_phase]
        prev = self._HB[self._hb_phase - 1][0] if self._hb_phase > 0 else 1.0
        self._hb_t += 1.0 / frames
        if self._hb_t >= 1.0:
            self._hb_t = 0.0
            self._scale = target
            self._hb_phase = (self._hb_phase + 1) % len(self._HB)
        else:
            self._scale = prev + (target - prev) * self._hb_t
        self.update()

    def paintEvent(self, event):
        # While building the cache or no cache yet — normal paint
        if self._caching or self._cache_pm is None:
            super().paintEvent(event)
            return
        # Draw the cached snapshot scaled around its vertical centre.
        # grab() returns a pixmap at device pixel ratio (2× on Retina),
        # so divide by dpr to get the logical (CSS) pixel size.
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        dpr  = self._cache_pm.devicePixelRatio()
        s    = self._scale
        lw   = self._cache_pm.width()  / dpr   # logical width
        lh   = self._cache_pm.height() / dpr   # logical height
        new_w = lw * s
        new_h = lh * s
        y_off = (lh - new_h) / 2
        p.drawPixmap(0, int(y_off), int(new_w), int(new_h), self._cache_pm)



# ──────────────────────────────────────────────────────────────────
#  Left panel — solid coloured hero side
# ──────────────────────────────────────────────────────────────────
class _FadeInLabel(QLabel):
    """QLabel that fades in from transparent over `duration` ms after show()."""
    def __init__(self, text: str = "", duration: int = 600, delay: int = 0, parent=None):
        super().__init__(text, parent)
        self._duration = duration
        self._delay    = delay
        self._fx       = QGraphicsOpacityEffect(self)
        self._fx.setOpacity(0.0)
        self.setGraphicsEffect(self._fx)
        self._anim = QPropertyAnimation(self._fx, b"opacity", self)
        self._anim.setDuration(duration)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

    def play(self, delay: int = None):
        ms = delay if delay is not None else self._delay
        QTimer.singleShot(ms, self._anim.start)


class HeroPanel(QWidget):
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0.0, QColor("#8B3A2E"))
        grad.setColorAt(1.0, QColor("#5A1F16"))
        p.fillRect(self.rect(), grad)

        # Decorative circle top-right
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 18))
        p.drawEllipse(self.width() - 120, -80, 260, 260)

        # Decorative circle bottom-left
        p.setBrush(QColor(255, 255, 255, 12))
        p.drawEllipse(-80, self.height() - 150, 280, 280)

        # Yellow ochre accent stripe at bottom
        p.setBrush(QColor("#D4A017"))
        p.drawRect(0, self.height() - 6, self.width(), 6)


# ──────────────────────────────────────────────────────────────────
#  Animated language card  — white body, accent-red on hover
# ──────────────────────────────────────────────────────────────────
class LanguageCard(QWidget):
    clicked = Signal()

    def __init__(self, flag: str, title: str, subtitle: str,
                 action_text: str, accent_color: str,
                 badge_bg: str, badge_fg: str,
                 audio_file: str = "", filled: bool = False,
                 base_color: str = "#FFFFFF", hover_min: float = 0.0):
        super().__init__()
        self._audio_file = audio_file
        self._accent     = QColor(accent_color)
        self._badge_bg   = QColor(badge_bg)
        self._badge_fg   = QColor(badge_fg)
        self._base       = QColor(base_color)  # card bg when t=0
        self._filled     = filled
        self._hover_min  = hover_min   # floor for filled cards so they never go fully white
        self.__hover_t   = 0.0

        self.setFixedSize(268, 230)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover)

        # ── animation ──
        self._anim = QPropertyAnimation(self, b"hoverProgress")
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

        # ── layout ──
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(0)

        top_row = QHBoxLayout()
        self._badge = QLabel(flag)
        self._badge.setAlignment(Qt.AlignCenter)
        self._badge.setFixedSize(50, 50)
        top_row.addWidget(self._badge)
        top_row.addStretch()
        self._arrow = QLabel("→")
        top_row.addWidget(self._arrow)

        self.title_label  = QLabel(title)
        self.sub_label    = QLabel(subtitle)
        self.action_label = QLabel(action_text)

        layout.addLayout(top_row)
        layout.addSpacing(12)
        layout.addWidget(self.title_label)
        layout.addSpacing(4)
        layout.addWidget(self.sub_label)
        layout.addStretch()
        layout.addWidget(self.action_label)

        if self._filled:
            self.__hover_t = 1.0
        self._apply_label_styles(self.__hover_t)

    # ── proper PySide6 Qt Property ──
    def _get_hover(self):
        return self.__hover_t

    def _set_hover(self, v: float):
        self.__hover_t = v
        self._apply_label_styles(v)
        self.update()

    hoverProgress = Property(float, _get_hover, _set_hover)

    def _apply_label_styles(self, t: float):
        # on_accent: 1.0 = fully accent-filled bg, 0.0 = white bg
        # t itself carries this meaning for both card types;
        # filled cards just animate in the opposite direction (enter→0, leave→1)
        on_accent = t

        # badge pill: accent bg + white text when filled, pale bg + accent text when empty
        b_r = int(self._accent.red()   * on_accent + self._badge_bg.red()   * (1 - on_accent))
        b_g = int(self._accent.green() * on_accent + self._badge_bg.green() * (1 - on_accent))
        b_b = int(self._accent.blue()  * on_accent + self._badge_bg.blue()  * (1 - on_accent))
        # badge text: white on accent, accent-coloured on pale bg
        f_r = int(255          * on_accent + self._badge_fg.red()   * (1 - on_accent))
        f_g = int(255          * on_accent + self._badge_fg.green() * (1 - on_accent))
        f_b = int(255          * on_accent + self._badge_fg.blue()  * (1 - on_accent))
        self._badge.setStyleSheet(
            f"background:rgb({b_r},{b_g},{b_b}); color:rgb({f_r},{f_g},{f_b});"
            f"border-radius:13px; font-size:15px; font-weight:900;"
        )

        # title: dark on light bg (t≈0), white on accent bg (t≈1)
        tc_r = int(45  * (1 - on_accent) + 255 * on_accent)
        tc_g = int(24  * (1 - on_accent) + 255 * on_accent)
        tc_b = int(16  * (1 - on_accent) + 255 * on_accent)
        # subtitle: medium grey on light, soft white on accent
        sc_r = int(110 * (1 - on_accent) + 230 * on_accent)
        sc_g = int(110 * (1 - on_accent) + 230 * on_accent)
        sc_b = int(110 * (1 - on_accent) + 230 * on_accent)
        # action/arrow: accent-coloured on light bg, white on accent bg
        ac = int(self._accent.red()   * (1 - on_accent) + 255 * on_accent)
        ag = int(self._accent.green() * (1 - on_accent) + 255 * on_accent)
        ab = int(self._accent.blue()  * (1 - on_accent) + 255 * on_accent)

        self.title_label.setStyleSheet(
            f"color:rgb({tc_r},{tc_g},{tc_b}); font-size:23px; font-weight:900; background:transparent;"
        )
        self.sub_label.setStyleSheet(
            f"color:rgb({sc_r},{sc_g},{sc_b}); font-size:13px; font-weight:700; background:transparent;"
        )
        arrow_style = f"color:rgb({ac},{ag},{ab}); font-size:13px; font-weight:900; background:transparent;"
        self.action_label.setStyleSheet(arrow_style)
        self._arrow.setStyleSheet(
            f"color:rgb({ac},{ag},{ab}); font-size:20px; font-weight:900; background:transparent;"
        )

    def set_content(self, title, subtitle, action_text):
        self.title_label.setText(title)
        self.sub_label.setText(subtitle)
        self.action_label.setText(action_text)

    # ── self-painted background ──
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        t = self.__hover_t
        r = 18.0
        w = self.width() - 6
        h = self.height() - 6

        on_accent = t

        # drop shadow (heavier when accent-filled)
        for i in range(4, 0, -1):
            alpha = int((8 + 8 * on_accent) * i / 4)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, alpha))
            p.drawRoundedRect(i, i + int(3 * on_accent), w, h, r, r)

        # card fill: base_color ↔ accent
        fill = QColor(
            int(self._base.red()   + (self._accent.red()   - self._base.red())   * on_accent),
            int(self._base.green() + (self._accent.green() - self._base.green()) * on_accent),
            int(self._base.blue()  + (self._accent.blue()  - self._base.blue())  * on_accent),
        )
        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, r, r)
        p.fillPath(path, fill)

        # border
        border_alpha = int(255 * (1.0 - on_accent * 0.6))
        b_r = int(225 + (self._accent.red()   - 225) * on_accent)
        b_g = int(212 + (self._accent.green() - 212) * on_accent)
        b_b = int(198 + (self._accent.blue()  - 198) * on_accent)
        p.setPen(QPen(QColor(b_r, b_g, b_b, border_alpha), 2.0))
        p.setBrush(Qt.NoBrush)
        p.drawPath(path)

    def enterEvent(self, e):
        self._anim.stop()
        self._anim.setStartValue(self.__hover_t)
        # filled=True: hover lightens but never reaches fully white (hover_min floor)
        self._anim.setEndValue(self._hover_min if self._filled else 1.0)
        self._anim.start()
        if self._audio_file:
            _play(self._audio_file)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._anim.stop()
        self._anim.setStartValue(self.__hover_t)
        self._anim.setEndValue(1.0 if self._filled else 0.0)
        self._anim.start()
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(e)


# ──────────────────────────────────────────────────────────────────
#  Input mode card — same animated style as LanguageCard
#  Wide horizontal card: icon left, text centre, arrow right
# ──────────────────────────────────────────────────────────────────
class InputModeCard(QWidget):
    clicked = Signal()

    # icon_type: "mic" | "picture" | "type"
    # accent_color: fill colour on hover
    # base_color: resting bg
    def __init__(self, icon_type: str, title: str, subtitle: str,
                 accent_color: str = "#8B3A2E",
                 base_color: str = "#FDF3EE"):
        super().__init__()
        self._icon_type  = icon_type
        self._accent     = QColor(accent_color)
        self._base       = QColor(base_color)
        self.__hover_t   = 0.0

        self.setFixedHeight(104)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover)

        self._anim = QPropertyAnimation(self, b"hoverProgress")
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(22, 0, 22, 0)
        layout.setSpacing(18)

        # icon badge (56×56)
        self._icon_widget = _ModeIcon(icon_type, self._accent, self._base)
        self._icon_widget.setFixedSize(56, 56)

        text_col = QVBoxLayout()
        text_col.setSpacing(3)
        text_col.setAlignment(Qt.AlignVCenter)
        self._title_lbl    = QLabel(title)
        self._subtitle_lbl = QLabel(subtitle)
        text_col.addWidget(self._title_lbl)
        text_col.addWidget(self._subtitle_lbl)

        self._arrow_lbl = QLabel("→")

        layout.addWidget(self._icon_widget, 0, Qt.AlignVCenter)
        layout.addLayout(text_col, 1)
        layout.addWidget(self._arrow_lbl, 0, Qt.AlignVCenter)

        self._apply_styles(0.0)

    def _get_hover(self):  return self.__hover_t
    def _set_hover(self, v):
        self.__hover_t = v
        self._icon_widget.set_hover(v)
        self._apply_styles(v)
        self.update()
    hoverProgress = Property(float, _get_hover, _set_hover)

    def _apply_styles(self, t: float):
        # title: dark → white
        tc = int(45  * (1 - t) + 255 * t)
        tg = int(24  * (1 - t) + 255 * t)
        tb = int(16  * (1 - t) + 255 * t)
        # subtitle: grey → soft white
        sc = int(110 * (1 - t) + 220 * t)
        # arrow: accent → white
        ac = int(self._accent.red()   * (1 - t) + 255 * t)
        ag = int(self._accent.green() * (1 - t) + 255 * t)
        ab = int(self._accent.blue()  * (1 - t) + 255 * t)
        self._title_lbl.setStyleSheet(
            f"color:rgb({tc},{tg},{tb}); font-size:22px; font-weight:900; background:transparent;"
        )
        self._subtitle_lbl.setStyleSheet(
            f"color:rgb({sc},{sc},{sc}); font-size:14px; font-weight:700; background:transparent;"
        )
        self._arrow_lbl.setStyleSheet(
            f"color:rgb({ac},{ag},{ab}); font-size:26px; font-weight:900; background:transparent;"
        )

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        t  = self.__hover_t
        r  = 18.0
        w  = self.width()  - 4
        h  = self.height() - 4

        # shadow
        for i in range(4, 0, -1):
            a = int((6 + 10 * t) * i / 4)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, a))
            p.drawRoundedRect(i, i + int(2 * t), w, h, r, r)

        # fill: base → accent
        fill = QColor(
            int(self._base.red()   + (self._accent.red()   - self._base.red())   * t),
            int(self._base.green() + (self._accent.green() - self._base.green()) * t),
            int(self._base.blue()  + (self._accent.blue()  - self._base.blue())  * t),
        )
        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, r, r)
        p.fillPath(path, fill)

        # border fades away as card fills
        ba = int(255 * (1.0 - t * 0.8))
        br = int(225 + (self._accent.red()   - 225) * t)
        bg = int(212 + (self._accent.green() - 212) * t)
        bb = int(198 + (self._accent.blue()  - 198) * t)
        p.setPen(QPen(QColor(br, bg, bb, ba), 2.0))
        p.setBrush(Qt.NoBrush)
        p.drawPath(path)

    def enterEvent(self, e):
        self._anim.stop()
        self._anim.setStartValue(self.__hover_t)
        self._anim.setEndValue(1.0)
        self._anim.start()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._anim.stop()
        self._anim.setStartValue(self.__hover_t)
        self._anim.setEndValue(0.0)
        self._anim.start()
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(e)

    def set_content(self, icon_type, title, subtitle):
        self._icon_type = icon_type
        self._icon_widget.icon_type = icon_type
        self._icon_widget.update()
        self._title_lbl.setText(title)
        self._subtitle_lbl.setText(subtitle)


class _ModeIcon(QWidget):
    """Circular icon badge that tints on hover."""
    def __init__(self, icon_type: str, accent: QColor, base: QColor):
        super().__init__()
        self.icon_type = icon_type
        self._accent   = accent
        self._base     = base
        self._t        = 0.0
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def set_hover(self, t: float):
        self._t = t
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        t  = self._t
        w, h = self.width(), self.height()

        # badge circle: dark accent resting → white on hover
        bg_r = int(self._accent.red()   * (1 - t) + 255 * t)
        bg_g = int(self._accent.green() * (1 - t) + 255 * t)
        bg_b = int(self._accent.blue()  * (1 - t) + 255 * t)

        p.setPen(Qt.NoPen)
        p.setBrush(QColor(bg_r, bg_g, bg_b))
        p.drawEllipse(0, 0, w, h)

        # icon stroke: white resting → accent on hover
        ic_r = int(255 * (1 - t) + self._accent.red()   * t)
        ic_g = int(255 * (1 - t) + self._accent.green() * t)
        ic_b = int(255 * (1 - t) + self._accent.blue()  * t)
        icon_col = QColor(ic_r, ic_g, ic_b)

        pen = QPen(icon_col, 2.8)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)

        cx, cy = w // 2, h // 2
        if self.icon_type == "mic":
            p.drawRoundedRect(cx - 6, cy - 13, 12, 18, 5, 5)
            p.drawArc(cx - 10, cy - 6, 20, 18, 0, -180 * 16)
            p.drawLine(cx, cy + 12, cx, cy + 17)
            p.drawLine(cx - 5, cy + 17, cx + 5, cy + 17)
        elif self.icon_type == "picture":
            p.drawRoundedRect(cx - 14, cy - 11, 28, 22, 4, 4)
            p.drawEllipse(cx - 9, cy - 7, 7, 7)
            pts = [cx - 14, cy + 10, cx - 4, cy + 1, cx + 4, cy + 6, cx + 14, cy - 2]
            for i in range(0, len(pts) - 2, 2):
                p.drawLine(pts[i], pts[i+1], pts[i+2], pts[i+3])
        elif self.icon_type == "type":
            f = QFont()
            f.setPointSize(18)
            f.setBold(True)
            p.setFont(f)
            p.setPen(icon_col)
            p.drawText(self.rect(), Qt.AlignCenter, "T")


# ──────────────────────────────────────────────────────────────────
#  HomePage
# ──────────────────────────────────────────────────────────────────
class HomePage(QWidget):
    speak_clicked    = Signal()
    type_clicked     = Signal()
    pictures_clicked = Signal()
    emergency_clicked = Signal()
    language_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.strings = {}
        self.current_language = "en"

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.stack = QStackedWidget()
        self.stack.setObjectName("homeStack")
        root.addWidget(self.stack)

        self.language_screen = self._build_language_screen()
        self.mode_screen     = self._build_mode_screen()

        self.stack.addWidget(self.language_screen)
        self.stack.addWidget(self.mode_screen)
        self.stack.setCurrentWidget(self.language_screen)

        # kick off welcome animation + audio
        QTimer.singleShot(80, self.welcome_label.play)
        QTimer.singleShot(300, lambda: _play("welcome.mp3"))

    # ── Language screen ────────────────────────────────────────────
    def _build_language_screen(self):
        page = QWidget()
        page.setObjectName("homeLanguagePage")

        # Full-width horizontal split
        split = QHBoxLayout(page)
        split.setContentsMargins(0, 0, 0, 0)
        split.setSpacing(0)

        # ── LEFT hero panel ──
        hero = HeroPanel()
        hero.setFixedWidth(300)
        hero.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(36, 44, 28, 36)
        hero_layout.setSpacing(0)
        hero_layout.setAlignment(Qt.AlignTop)

        # Animated "Welkom"
        self.welcome_label = AnimatedWelcomeLabel("Welkom")
        self.welcome_label.setObjectName("heroWelcome")
        self.welcome_label.setWordWrap(True)

        tagline = QLabel("Your health,\nyour voice.")
        tagline.setObjectName("heroTagline")
        tagline.setWordWrap(True)

        hero_layout.addStretch(1)
        hero_layout.addWidget(self.welcome_label)
        hero_layout.addSpacing(18)
        hero_layout.addWidget(tagline)
        hero_layout.addStretch(2)

        # Ochre divider dot row
        dot_row = QHBoxLayout()
        for c in ["#D4A017", "#C65D2E", "#F2E6D8"]:
            dot = QFrame()
            dot.setFixedSize(10, 10)
            dot.setStyleSheet(f"background:{c}; border-radius:5px;")
            dot_row.addWidget(dot)
            dot_row.addSpacing(6)
        dot_row.addStretch()
        hero_layout.addLayout(dot_row)
        hero_layout.addSpacing(24)

        # ── RIGHT content panel ──
        right = QWidget()
        right.setObjectName("homeRightPanel")
        right.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(40, 40, 40, 30)
        right_layout.setSpacing(0)
        right_layout.setAlignment(Qt.AlignTop)

        heading_row = QHBoxLayout()
        heading_row.setSpacing(0)
        heading_row.setContentsMargins(0, 0, 0, 0)
        heading = QLabel("Choose your\nlanguage")
        heading.setObjectName("rightHeading")
        lottie_size = 126   # 84 * 1.5
        lottie_path = os.path.normpath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "..", "..", "assets", "anim", "Translate language.json"
        ))
        self._lang_help_btn = HelpButton(
            en_title="Language Selection",
            en_text="Choose your preferred language.\n\n"
                    "• Select English to use the app in English.\n"
                    "• Select Kriol to use the app in Kriol language.\n\n"
                    "Pick the language you are most comfortable with.",
            kr_title="Jusum Langgwej",
            kr_text="Jusum langgwej yu laik.\n\n"
                    "• Jusum Ingris blong yusum app langa Ingris.\n"
                    "• Jusum Kriol blong yusum app langa Kriol.\n\n"
                    "Jusum langgwej we i isi blong yu.",
        )
        heading_row.addWidget(heading, 0, Qt.AlignVCenter)
        heading_row.addStretch()
        heading_row.addWidget(self._lang_help_btn, 0, Qt.AlignVCenter)

        sub = QLabel("Jus yu langgus")
        sub.setObjectName("rightSubheading")

        # Divider line
        line = QFrame()
        line.setFixedHeight(3)
        line.setObjectName("rightDivider")

        # Cards row
        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)

        self.english_card = LanguageCard(
            "EN", "English", "Speak in English", "Select  →",
            accent_color="#8B3A2E", badge_bg="#F5E8E6", badge_fg="#8B3A2E",
            audio_file="english.mp3", filled=True,
            base_color="#FFFFFF", hover_min=0.70,   # hover → lighter coral, never white
        )
        self.kriol_card = LanguageCard(
            "KR", "Kriol", "Tok langa Kriol", "Pikimup  →",
            accent_color="#C65D2E", badge_bg="#FAF0EB", badge_fg="#C65D2E",
            audio_file="kriol.mp3", filled=False,
            base_color="#FDF3EE",   # warm cream default — never pure white
        )

        self.english_card.clicked.connect(lambda: self._select_language("en"))
        self.kriol_card.clicked.connect(lambda: self._select_language("kriol"))

        cards_row.addWidget(self.english_card)
        cards_row.addWidget(self.kriol_card)
        cards_row.addStretch()

        # Emergency
        self.emergency_btn = QPushButton("⚠   Emergency Help  /  Emajncy Help")
        self.emergency_btn.setObjectName("homeEmergencyOutlineButton")
        self.emergency_btn.setCursor(Qt.PointingHandCursor)
        self.emergency_btn.setFixedSize(440, 52)
        self.emergency_btn.clicked.connect(self.emergency_clicked.emit)

        right_layout.addLayout(heading_row)
        right_layout.addSpacing(8)
        right_layout.addWidget(sub)
        right_layout.addSpacing(24)
        right_layout.addWidget(line)
        right_layout.addSpacing(32)
        right_layout.addLayout(cards_row)
        right_layout.addStretch()
        right_layout.addWidget(self.emergency_btn)

        split.addWidget(hero)
        split.addWidget(right, 1)

        return page

    # ── Mode screen ────────────────────────────────────────────────
    def _build_mode_screen(self):
        page = QWidget()
        page.setObjectName("homeLanguagePage")  # reuse same cream bg

        split = QHBoxLayout(page)
        split.setContentsMargins(0, 0, 0, 0)
        split.setSpacing(0)

        # ── LEFT hero panel (same as language screen) ──
        hero = HeroPanel()
        hero.setFixedWidth(300)
        hero.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(36, 44, 28, 36)
        hero_layout.setSpacing(0)

        hero_title = _FadeInLabel("How do\nyou want\nto tell us?", duration=700)
        hero_title.setObjectName("heroWelcome")
        hero_title.setWordWrap(True)
        self._mode_hero_title = hero_title

        hero_tag = _FadeInLabel("Your voice,\nyour choice.", duration=700, delay=200)
        hero_tag.setObjectName("heroTagline")
        hero_tag.setWordWrap(True)
        self._mode_hero_tag = hero_tag

        hero_layout.addStretch(1)
        hero_layout.addWidget(hero_title)
        hero_layout.addSpacing(18)
        hero_layout.addStretch(2)

        dot_row = QHBoxLayout()
        for c in ["#D4A017", "#C65D2E", "#F2E6D8"]:
            dot = QFrame()
            dot.setFixedSize(10, 10)
            dot.setStyleSheet(f"background:{c}; border-radius:5px;")
            dot_row.addWidget(dot)
            dot_row.addSpacing(6)
        dot_row.addStretch()
        hero_layout.addLayout(dot_row)
        hero_layout.addSpacing(24)

        # ── RIGHT content panel ──
        right = QWidget()
        right.setObjectName("homeRightPanel")
        right.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(40, 40, 40, 30)
        right_layout.setSpacing(0)
        right_layout.setAlignment(Qt.AlignTop)

        # back button
        self.back_btn = QPushButton("‹  Back")
        self.back_btn.setObjectName("backLinkButton")
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.setFixedHeight(40)
        self.back_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(139,58,46,0.10);
                color: #8B3A2E;
                border: 2px solid #8B3A2E;
                border-radius: 20px;
                font-size: 14px;
                font-weight: 800;
                padding: 6px 22px;
            }
            QPushButton:hover { background-color: rgba(139,58,46,0.20); }
        """)
        self.back_btn.clicked.connect(self._go_to_language_screen)
        self._mode_help_btn = HelpButton(
            en_title="How to Tell Us",
            en_text="Choose how you want to describe your symptoms.\n\n"
                    "• Speak – Press the mic and talk out loud. We will listen.\n"
                    "• Body Map – Tap the body diagram to show where it hurts.\n"
                    "• Type – Write your symptoms in the text box.\n\n"
                    "Pick whichever feels easiest for you.",
            kr_title="Haumej Yu Laik Telim Mibala",
            kr_text="Jusum wei yu laik diskaibim yu simptom.\n\n"
                    "• Tok – Pres maik en toktok laut. Mibala bai lisin.\n"
                    "• Bodi Mep – Tapim pikja blong shoim we i hati.\n"
                    "• Raidim – Raidim simptom langa tekst boks.\n\n"
                    "Jusum wei we i isi blong yu.",
        )

        # heading row
        heading = _FadeInLabel("Choose how\nto share", duration=600, delay=120)
        heading.setObjectName("rightHeading")
        self._mode_heading = heading

        sub = _FadeInLabel("Pick what feels easiest for you", duration=600, delay=260)
        sub.setObjectName("rightSubheading")
        self._mode_sub = sub

        # Divider
        line = QFrame()
        line.setFixedHeight(3)
        line.setObjectName("rightDivider")

        # Cards — each gets its own accent colour
        self.speak_card = InputModeCard(
            "mic", "Speak", "Talk and we will listen",
            accent_color="#8B3A2E", base_color="#FDF3EE",
        )
        self.picture_card = InputModeCard(
            "picture", "Body Map", "Tap where it hurts",
            accent_color="#5A7FA0", base_color="#EEF4FA",
        )
        self.type_card = InputModeCard(
            "type", "Type", "Write what you feel",
            accent_color="#7A6020", base_color="#FAF4E6",
        )

        self.speak_card.clicked.connect(_stop_all)
        self.speak_card.clicked.connect(self.speak_clicked.emit)
        self.picture_card.clicked.connect(_stop_all)
        self.picture_card.clicked.connect(self.pictures_clicked.emit)
        self.type_card.clicked.connect(_stop_all)
        self.type_card.clicked.connect(self.type_clicked.emit)

        # Emergency
        self.mode_emergency_btn = QPushButton("⚠   Emergency Help")
        self.mode_emergency_btn.setObjectName("homeEmergencyOutlineButton")
        self.mode_emergency_btn.setCursor(Qt.PointingHandCursor)
        self.mode_emergency_btn.setFixedSize(340, 52)
        self.mode_emergency_btn.clicked.connect(_stop_all)
        self.mode_emergency_btn.clicked.connect(self.emergency_clicked.emit)

        top_row_m = QHBoxLayout()
        top_row_m.setSpacing(0)
        top_row_m.addWidget(self.back_btn, 0, Qt.AlignVCenter)
        top_row_m.addStretch()
        top_row_m.addWidget(self._mode_help_btn, 0, Qt.AlignVCenter)
        right_layout.addLayout(top_row_m)
        right_layout.addSpacing(16)
        right_layout.addWidget(heading)
        right_layout.addSpacing(6)
        right_layout.addWidget(sub)
        right_layout.addSpacing(20)
        right_layout.addWidget(line)
        right_layout.addSpacing(24)
        right_layout.addWidget(self.speak_card)
        right_layout.addSpacing(12)
        right_layout.addWidget(self.picture_card)
        right_layout.addSpacing(12)
        right_layout.addWidget(self.type_card)
        right_layout.addStretch()
        right_layout.addWidget(self.mode_emergency_btn)

        split.addWidget(hero)
        split.addWidget(right, 1)

        return page

    # ── Actions ────────────────────────────────────────────────────
    def _select_language(self, code: str):
        self.current_language = code
        self.language_changed.emit(code)
        self.stack.setCurrentWidget(self.mode_screen)
        # Trigger fade-in animations on mode screen titles
        self._mode_hero_title.play()
        self._mode_hero_tag.play()
        self._mode_heading.play()
        self._mode_sub.play()
        # Play main screen voiceover for the selected language, then the input guide
        first  = "Kriol Main Screen.mp3"    if code == "kriol" else "English Main Screen.mp3"
        second = "Kriol-Main Screen2.mp3"   if code == "kriol" else "English-Main Screen2.mp3"
        QTimer.singleShot(300, lambda: _play_sequence([first, second], on_complete=self._animate_mode_cards))

    def _animate_mode_cards(self):
        """Give the 3 cards a staggered nudge animation after the audio ends."""
        cards = [self.speak_card, self.picture_card, self.type_card]
        for i, card in enumerate(cards):
            delay = i * 180
            def _nudge(c=card):
                orig = c.geometry()
                nudged = orig.translated(0, 10)
                # move down
                a1 = QPropertyAnimation(c, b"geometry", c)
                a1.setDuration(120)
                a1.setStartValue(orig)
                a1.setEndValue(nudged)
                a1.setEasingCurve(QEasingCurve.OutQuad)
                # bounce back up
                a2 = QPropertyAnimation(c, b"geometry", c)
                a2.setDuration(220)
                a2.setStartValue(nudged)
                a2.setEndValue(orig)
                a2.setEasingCurve(QEasingCurve.OutBack)
                a1.finished.connect(a2.start)
                a1.start()
                c._nudge_a1 = a1
                c._nudge_a2 = a2
            QTimer.singleShot(delay, _nudge)

    def _go_to_language_screen(self):
        _stop_all()
        self.stack.setCurrentWidget(self.language_screen)

    def show_mode_screen(self):
        self.stack.setCurrentWidget(self.mode_screen)

    def show_language_screen(self):
        self.stack.setCurrentWidget(self.language_screen)

    # ── String updates ─────────────────────────────────────────────
    def set_strings(self, s: dict):
        self.strings = s or {}
        is_kriol = self.current_language == "kriol"

        self.welcome_label.setText("Welkom")
        self.english_card.set_content("English", "Speak in English", "Select  →")
        self.kriol_card.set_content("Kriol", "Tok langa Kriol", "Pikimup  →")
        self.emergency_btn.setText("⚠   Emergency Help  /  Emajncy Help")

        self.back_btn.setText("‹  Bek" if is_kriol else "‹  Back")

        # Mode screen hero + headings
        self._mode_hero_title.setText(
            "Haumej wei\nyu laik\ntelim mibala?" if is_kriol else "How do\nyou want\nto tell us?"
        )
        self._mode_hero_tag.setText(
            "Yu wei,\nyu jusum." if is_kriol else "Your voice,\nyour choice."
        )
        self._mode_heading.setText(
            "Jusum wei\nyu laik" if is_kriol else "Choose how\nto share"
        )
        self._mode_sub.setText(
            "Pikimup wei im isi blong yu" if is_kriol else "Pick what feels easiest for you"
        )

        self.speak_card.set_content(
            "mic",
            "Tok" if is_kriol else "Speak",
            "Tok en wi garra lisin." if is_kriol else "Talk and we will listen",
        )
        self.picture_card.set_content(
            "picture",
            "Bodi Mep" if is_kriol else "Body Map",
            "Sho mibala wea im pein." if is_kriol else "Tap where it hurts",
        )
        self.type_card.set_content(
            "type",
            "Raidim" if is_kriol else "Type",
            "Raidim wei yu fil." if is_kriol else "Write what you feel",
        )
        self.mode_emergency_btn.setText(
            "⚠   Imijensi Elp" if is_kriol else "⚠   Emergency Help"
        )
        self._lang_help_btn.set_kriol(False)  # language screen always bilingual
        self._mode_help_btn.set_kriol(is_kriol)
        self._lang_help_btn.set_kriol(False)  # language screen is always bilingual
        self._mode_help_btn.set_kriol(is_kriol)
