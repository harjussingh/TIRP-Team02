from __future__ import annotations

from typing import Dict, List

from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QColor, QLinearGradient, QPainter
from PySide6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QSizePolicy, QStackedWidget, QVBoxLayout, QWidget,
)
from src.ui.widgets.help_popup import HelpButton
from src.utils.audio import play_sequence as _play_sequence, stop_all as _stop_all


# ── Palettes ──────────────────────────────────────────────────────────────────


class _FadeInLabel(QLabel):
    """QLabel that animates from transparent to opaque when play() is called."""
    def __init__(self, text="", duration=600, parent=None):
        super().__init__(text, parent)
        self._duration = duration
        self._fx = QGraphicsOpacityEffect(self)
        self._fx.setOpacity(0.0)
        self.setGraphicsEffect(self._fx)
        self._anim = QPropertyAnimation(self._fx, b"opacity", self)
        self._anim.setDuration(self._duration)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

    def play(self, delay: int = 0):
        self._fx.setOpacity(0.0)
        if delay > 0:
            QTimer.singleShot(delay, self._anim.start)
        else:
            self._anim.start()


_P = {
    "mild": {
        "bg":          "#1CA34A",
        "bg_dark":     "#157A37",
        "bg_light":    "#D8F4DF",
        "text":        "#157A37",
        "step_bg":     "#F0FAF3",
        "step_num":    "#1CA34A",
        "esc_bg":      "#FFFBEA",
        "esc_border":  "#E6B800",
        "esc_text":    "#7A5700",
    },
    "moderate": {
        "bg":          "#C65D2E",
        "bg_dark":     "#9E3D18",
        "bg_light":    "#FFF0E8",
        "text":        "#9E3D18",
        "step_bg":     "#FFF8F4",
        "step_num":    "#C65D2E",
        "esc_bg":      "#FFF0E8",
        "esc_border":  "#C65D2E",
        "esc_text":    "#9E3D18",
    },
    "critical": {
        "bg":          "#C00000",
        "bg_dark":     "#8B0000",
        "bg_light":    "#FFE0E0",
        "text":        "#8B0000",
        "step_bg":     "#FFF5F5",
        "step_num":    "#C00000",
        "esc_bg":      "#FFE0E0",
        "esc_border":  "#C00000",
        "esc_text":    "#8B0000",
    },
}

_ICONS  = {"mild": "\u2705", "moderate": "\u26a0\ufe0f", "critical": "\U0001f6a8"}
_LABELS = {
    "mild":     ("Rest at Home",  "Rest langa Haus"),
    "moderate": ("See a Clinic",  "Go langa Klinik"),
    "critical": ("Call 000 Now",  "Kol 000 Nau"),
}
_CTA = {
    "mild":     ("What should I do?  \u2192", "Wanim fo du?  \u2192"),
    "moderate": ("\u260e\ufe0f  What should I do?  \u2192", "\u260e\ufe0f  Wanim fo du?  \u2192"),
    "critical": ("\u260e\ufe0f  What should I do?  \u2192", "\u260e\ufe0f  Wanim fo du?  \u2192"),
}
_ESC = {
    "mild":     (
        "\u2139\ufe0f  If chest pain, breathing trouble or collapse \u2014 go to emergency immediately.",
        "\u2139\ufe0f  If jes pein, brithin trabul o poldaun \u2014 go langa imijensi nau.",
    ),
    "moderate": (
        "\u26a0\ufe0f  If breathing becomes very hard or you collapse \u2014 call 000 now.",
        "\u26a0\ufe0f  If brith kam brabli had o yu poldaun \u2014 kol 000 nau.",
    ),
    "critical": (
        "\u26a0\ufe0f  This is a medical emergency. Do not wait. Call 000 now.",
        "\u26a0\ufe0f  Diswan imijensi. No weit. Kol 000 nau.",
    ),
}


# ── Shared helpers ────────────────────────────────────────────────────────────

def _nav_btn(text: str, primary: bool = False, danger: bool = False) -> QPushButton:
    btn = QPushButton(text)
    btn.setFixedHeight(52)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    if danger:
        btn.setStyleSheet("""
            QPushButton { background:#B10000; color:white; border:none;
                border-radius:12px; font-size:15px; font-weight:700; }
            QPushButton:hover { background:#8B0000; }
        """)
    elif primary:
        btn.setStyleSheet("""
            QPushButton { background:#8B3A2E; color:white; border:none;
                border-radius:12px; font-size:15px; font-weight:700; }
            QPushButton:hover { background:#5A1F16; }
        """)
    else:
        btn.setStyleSheet("""
            QPushButton { background:white; color:#3D2B1F;
                border:1.5px solid #8B3A2E; border-radius:12px;
                font-size:15px; font-weight:600; }
            QPushButton:hover { background:#FFF5F0; }
        """)
    return btn


def _nav_bar(*buttons) -> QWidget:
    bar = QWidget()
    bar.setFixedHeight(72)
    bar.setStyleSheet("background:#F5EDE6; border-top:1px solid rgba(139,58,46,0.12);")
    lay = QHBoxLayout(bar)
    lay.setContentsMargins(24, 10, 24, 10)
    lay.setSpacing(12)
    for btn in buttons:
        lay.addWidget(btn)
    return bar


def _step_dot(active: bool) -> QLabel:
    dot = QLabel()
    dot.setFixedSize(10, 10)
    color = "#8B3A2E" if active else "#D4B8B0"
    dot.setStyleSheet(f"background:{color}; border-radius:5px; border:none;")
    return dot


# ── Step 1 — Verdict ─────────────────────────────────────────────────────────

class _Step1(QWidget):
    next_clicked = Signal()
    emergency_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._triage = "mild"
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Main area
        self._main = QWidget()
        self._main.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_lay = QVBoxLayout(self._main)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setAlignment(Qt.AlignCenter)

        # Coloured verdict card fills most of the panel
        self._card = QFrame()
        self._card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        card_lay = QVBoxLayout(self._card)
        card_lay.setContentsMargins(40, 40, 40, 40)
        card_lay.setSpacing(16)
        card_lay.setAlignment(Qt.AlignCenter)

        self._icon_lbl = QLabel()
        self._icon_lbl.setAlignment(Qt.AlignCenter)
        self._icon_lbl.setStyleSheet("font-size:96px; background:transparent; border:none;")
        card_lay.addWidget(self._icon_lbl)

        self._verdict_lbl = QLabel()
        self._verdict_lbl.setAlignment(Qt.AlignCenter)
        self._verdict_lbl.setWordWrap(True)
        self._verdict_lbl.setStyleSheet(
            "color:white; font-size:42px; font-weight:800; background:transparent; border:none;"
        )
        card_lay.addWidget(self._verdict_lbl)

        self._condition_lbl = QLabel()
        self._condition_lbl.setAlignment(Qt.AlignCenter)
        self._condition_lbl.setWordWrap(True)
        self._condition_lbl.setStyleSheet(
            "color:rgba(255,255,255,0.80); font-size:18px; font-weight:500;"
            "background:transparent; border:none;"
        )
        card_lay.addWidget(self._condition_lbl)

        card_lay.addSpacing(28)

        # CTA button lives inside the card
        self._cta_btn = QPushButton()
        self._cta_btn.setCursor(Qt.PointingHandCursor)
        self._cta_btn.setFixedHeight(54)
        self._cta_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._cta_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,0.18);
                color: white;
                border: 2px solid rgba(255,255,255,0.55);
                border-radius: 14px;
                font-size: 17px;
                font-weight: 800;
                padding: 0 24px;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.30);
            }
            QPushButton:pressed {
                background-color: rgba(255,255,255,0.12);
            }
        """)
        self._cta_btn.clicked.connect(self.next_clicked)
        card_lay.addWidget(self._cta_btn)

        # Step dots
        dots_row = QHBoxLayout()
        dots_row.setAlignment(Qt.AlignCenter)
        dots_row.setSpacing(8)
        self._dots = [_step_dot(i == 0) for i in range(2)]
        for d in self._dots:
            dots_row.addWidget(d)
        card_lay.addSpacing(8)
        card_lay.addLayout(dots_row)

        main_lay.addWidget(self._card)
        root.addWidget(self._main, 1)

        # Nav bar — Emergency only
        self._emg_btn = _nav_btn("\u26a0\ufe0f  Emergency", danger=True)
        self._emg_btn.clicked.connect(self.emergency_clicked)
        root.addWidget(_nav_bar(self._emg_btn))

    def update(self, triage: str, condition: str, cta_text: str, kr: bool = False):
        self._triage = triage
        p = _P[triage]
        self._card.setStyleSheet(
            f"QFrame {{ background: qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            f"stop:0 {p['bg']}, stop:1 {p['bg_dark']}); border:none; }}"
        )
        self._icon_lbl.setText(_ICONS[triage])
        en, kr_txt = _LABELS[triage]
        self._verdict_lbl.setText(kr_txt if kr else en)
        self._condition_lbl.setText(condition)
        self._cta_btn.setText(cta_text)

    def set_kriol(self, kr: bool):
        en, kr_txt = _LABELS[self._triage]
        self._verdict_lbl.setText(kr_txt if kr else en)

    def paintEvent(self, e):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#FDFAF6"))


# ── Step 2 — What to do + What we found (combined) ───────────────────────────

class _Step2(QWidget):
    back_clicked = Signal()
    home_clicked = Signal()
    emergency_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Top bar: pill back button (same style as follow-up questions)
        top_bar = QWidget()
        top_bar.setFixedHeight(60)
        top_bar.setStyleSheet("background:#FDFAF6; border-bottom:1px solid rgba(139,58,46,0.10);")
        top_lay = QHBoxLayout(top_bar)
        top_lay.setContentsMargins(20, 10, 20, 10)
        top_lay.setSpacing(0)
        back_btn = QPushButton("\u2190  Back")
        back_btn.setObjectName("backLinkButton")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setFixedHeight(40)
        back_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        back_btn.setStyleSheet("""
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
        back_btn.clicked.connect(self.back_clicked)
        self._back_btn = back_btn
        self._help_btn = HelpButton(
            en_title="Your Results",
            en_text="These are your health assessment results based on your symptoms.\n\n"
                    "• Step 1 shows the overall verdict — how urgent your situation may be.\n"
                    "• Step 2 (this screen) shows what to do and what symptoms were detected.\n\n"
                    "Follow the recommended steps and seek help from a health worker if you are unsure or if symptoms worsen.\n\n"
                    "This is a support tool only — it does not replace professional medical advice.",
            kr_title="Yu Rizalt",
            kr_text="Diswan i yu helt asesmen rizalt blong yu simptom.\n\n"
                    "• Step 1 i shoim ol rizalt — hau bebet yu situesen ken bi.\n"
                    "• Step 2 (diswan skrin) i shoim wanim fo du en wanem simptom bin faindim.\n\n"
                    "Folem rekomendeishin step en lukaut blong elp long helt woka if yu no shua o simptom i kamap woswan.\n\n"
                    "Diswan sapot tul nomo — i no ripleis prafesenel medikol advaes.",
        )
        top_lay.addWidget(back_btn)
        top_lay.addStretch()
        top_lay.addWidget(self._help_btn)
        dots_row2 = QHBoxLayout()
        dots_row2.setSpacing(8)
        self._dots = [_step_dot(i == 1) for i in range(2)]
        for d in self._dots:
            dots_row2.addWidget(d)
        top_lay.addLayout(dots_row2)
        root.addWidget(top_bar)

        # Scroll area for combined content
        from PySide6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background:#FDFAF6; border:none;")

        content_widget = QWidget()
        content_widget.setStyleSheet("background:#FDFAF6;")
        self._content_lay = QVBoxLayout(content_widget)
        self._content_lay.setContentsMargins(32, 24, 32, 24)
        self._content_lay.setSpacing(0)
        self._content_lay.setAlignment(Qt.AlignTop)

        # Section A: What to do
        self._todo_heading = QLabel("What to do")
        self._todo_heading.setStyleSheet(
            "color:#3D2B1F; font-size:17px; font-weight:800; background:transparent; border:none;"
        )
        self._content_lay.addWidget(self._todo_heading)
        self._content_lay.addSpacing(14)

        self._steps_lay = QVBoxLayout()
        self._steps_lay.setSpacing(12)
        self._content_lay.addLayout(self._steps_lay)

        # Divider between sections
        self._content_lay.addSpacing(28)
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            " stop:0 transparent, stop:0.2 rgba(139,58,46,0.18),"
            " stop:0.8 rgba(139,58,46,0.18), stop:1 transparent); border:none;"
        )
        self._content_lay.addWidget(div)
        self._content_lay.addSpacing(24)

        # Section B: What we found
        self._found_heading = QLabel("What we found")
        self._found_heading.setStyleSheet(
            "color:#3D2B1F; font-size:17px; font-weight:800; background:transparent; border:none;"
        )
        self._content_lay.addWidget(self._found_heading)
        self._content_lay.addSpacing(14)

        # Symptoms card
        self._sym_card = QFrame()
        self._sym_card.setStyleSheet(
            "QFrame { background:white; border-radius:14px;"
            "border:1px solid rgba(139,58,46,0.12); }"
        )
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 16))
        self._sym_card.setGraphicsEffect(shadow)
        sym_lay = QVBoxLayout(self._sym_card)
        sym_lay.setContentsMargins(24, 18, 24, 18)
        sym_lay.setSpacing(10)
        self._sym_hdr = QLabel("Symptoms detected:")
        self._sym_hdr.setStyleSheet(
            "color:#8B3A2E; font-size:13px; font-weight:700; letter-spacing:0.6px;"
            "background:transparent; border:none;"
        )
        sym_lay.addWidget(self._sym_hdr)
        self._sym_lbl = QLabel()
        self._sym_lbl.setWordWrap(True)
        self._sym_lbl.setStyleSheet(
            "color:#1C1C1C; font-size:18px; font-weight:600; background:transparent; border:none;"
        )
        sym_lay.addWidget(self._sym_lbl)
        self._content_lay.addWidget(self._sym_card)
        self._content_lay.addSpacing(16)

        # Escalation strip
        self._esc_card = QFrame()
        esc_lay = QHBoxLayout(self._esc_card)
        esc_lay.setContentsMargins(20, 16, 20, 16)
        esc_lay.setSpacing(14)
        esc_icon = QLabel("\u26a0\ufe0f")
        esc_icon.setStyleSheet("font-size:24px; background:transparent; border:none;")
        esc_icon.setFixedWidth(32)
        esc_lay.addWidget(esc_icon, 0, Qt.AlignTop)
        self._esc_lbl = QLabel()
        self._esc_lbl.setWordWrap(True)
        self._esc_lbl.setStyleSheet(
            "color:#7A5700; font-size:15px; font-weight:600; background:transparent; border:none;"
        )
        esc_lay.addWidget(self._esc_lbl, 1)
        self._content_lay.addWidget(self._esc_card)
        self._content_lay.addStretch()

        scroll.setWidget(content_widget)
        root.addWidget(scroll, 1)

        # Nav bar
        self._done_btn = _nav_btn("\u21bb  Start Again")
        self._done_btn.clicked.connect(self.home_clicked)
        self._emg_btn = _nav_btn("\u26a0\ufe0f  Emergency", danger=True)
        self._emg_btn.clicked.connect(self.emergency_clicked)
        root.addWidget(_nav_bar(self._done_btn, self._emg_btn))

    def update(self, triage: str, steps: List[str], symptoms: List[str],
               esc_text: str, done_text: str, todo_title: str, found_title: str):
        p = _P[triage]
        self._todo_heading.setText(todo_title)
        self._found_heading.setText(found_title)

        # Steps
        while self._steps_lay.count():
            item = self._steps_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for idx, step in enumerate(steps[:5]):
            row = QFrame()
            row.setStyleSheet(
                f"QFrame {{ background:{p['step_bg']}; border-radius:14px; border:none; }}"
            )
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(10)
            shadow.setOffset(0, 2)
            shadow.setColor(QColor(0, 0, 0, 14))
            row.setGraphicsEffect(shadow)
            row_lay = QHBoxLayout(row)
            row_lay.setContentsMargins(18, 14, 18, 14)
            row_lay.setSpacing(16)
            num = QLabel(str(idx + 1))
            num.setFixedSize(36, 36)
            num.setAlignment(Qt.AlignCenter)
            num.setStyleSheet(
                f"QLabel {{ background:{p['step_num']}; color:white; border-radius:18px;"
                "font-size:16px; font-weight:800; border:none; }}"
            )
            row_lay.addWidget(num, 0, Qt.AlignVCenter)
            lbl = QLabel(step)
            lbl.setWordWrap(True)
            lbl.setStyleSheet(
                "color:#1C1C1C; font-size:32px; font-weight:600;"
                "background:transparent; border:none;"
            )
            row_lay.addWidget(lbl, 1)
            self._steps_lay.addWidget(row)

        # Symptoms
        sym_text = "  \u00b7  ".join(symptoms[:6]) if symptoms else "\u2014"
        self._sym_lbl.setText(sym_text)

        # Escalation
        self._esc_card.setStyleSheet(
            f"QFrame {{ background:{p['esc_bg']}; border-radius:14px;"
            f"border:1.5px solid {p['esc_border']}; }}"
        )
        self._esc_lbl.setStyleSheet(
            f"color:{p['esc_text']}; font-size:15px; font-weight:600;"
            "background:transparent; border:none;"
        )
        self._esc_lbl.setText(esc_text)
        self._done_btn.setText(done_text)

    def paintEvent(self, e):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#FDFAF6"))


# ── Hero panel (left — same across both steps) ────────────────────────────────

class _HeroPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(300)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        # Semi-transparent dark panel so white text stays readable over the pattern background
        self.setStyleSheet(
            "background: rgba(90, 31, 22, 0.82);"
            "border-right: 1px solid rgba(255,255,255,0.08);"
        )
        self.setAttribute(Qt.WA_StyledBackground, True)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 0, 28, 0)
        lay.setSpacing(0)
        lay.setAlignment(Qt.AlignHCenter)

        # Equal stretches above and below to vertically centre content
        lay.addStretch(1)

        bar = QWidget()
        bar.setFixedSize(48, 4)
        bar.setStyleSheet("background:#D4A017; border-radius:2px;")
        lay.addWidget(bar, 0, Qt.AlignHCenter)
        lay.addSpacing(28)

        self._icon = _FadeInLabel("", duration=500)
        self._icon.setAlignment(Qt.AlignCenter)
        self._icon.setStyleSheet("font-size:64px; background:transparent; border:none;")
        lay.addWidget(self._icon)
        lay.addSpacing(16)

        self._verdict = _FadeInLabel("", duration=600)
        self._verdict.setAlignment(Qt.AlignCenter)
        self._verdict.setWordWrap(True)
        self._verdict.setStyleSheet(
            "color:#FDFAF6; font-size:20px; font-weight:800;"
            "background:transparent; border:none;"
        )
        lay.addWidget(self._verdict)
        lay.addSpacing(8)

        self._condition = _FadeInLabel("", duration=600)
        self._condition.setAlignment(Qt.AlignCenter)
        self._condition.setWordWrap(True)
        self._condition.setStyleSheet(
            "color:rgba(253,250,246,0.70); font-size:14px; font-weight:500;"
            "background:transparent; border:none;"
        )
        lay.addWidget(self._condition)

        lay.addStretch(1)  # equal bottom stretch → true vertical centre

    def update(self, triage: str, condition: str, conf: str, is_kriol: bool):
        self._icon.setText(_ICONS[triage])
        en, kr = _LABELS[triage]
        self._verdict.setText(kr if is_kriol else en)
        self._condition.setText(condition)
        # Staggered fade-in matching questions page style
        self._icon.play(delay=0)
        self._verdict.play(delay=120)
        self._condition.play(delay=240)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        g = QLinearGradient(0, 0, 0, self.height())
        g.setColorAt(0.0, QColor("#8B3A2E"))
        g.setColorAt(1.0, QColor("#5A1F16"))
        p.fillRect(self.rect(), g)


# ── ResultsPage ───────────────────────────────────────────────────────────────

class ResultsPage(QWidget):
    back_clicked = Signal()   # unused externally but kept for compat
    home_clicked = Signal()
    emergency_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.strings: Dict = {}
        self._result_data: Dict = {}
        self._nlp_data: Dict = {}
        self._answers: Dict = {}

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._hero = _HeroPanel()
        root.addWidget(self._hero)

        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background:#FDFAF6;")

        self._s1 = _Step1()
        self._s2 = _Step2()
        self._stack.addWidget(self._s1)  # 0
        self._stack.addWidget(self._s2)  # 1
        root.addWidget(self._stack, 1)

        # Wiring — animated transitions
        self._s1.next_clicked.connect(self._on_what_to_do_clicked)
        self._s1.emergency_clicked.connect(self.emergency_clicked)

        self._s2.back_clicked.connect(lambda: self._go_to(0))
        self._s2.home_clicked.connect(self.home_clicked)
        self._s2.emergency_clicked.connect(self.emergency_clicked)

    # ── Fade transition helpers (same pattern as questions page) ──────────

    _FADE_STEPS    = 10
    _FADE_INTERVAL = 18   # ms

    def _fade_widget(self, widget, out: bool, done=None, _step: int = 0, _fx=None):
        from PySide6.QtWidgets import QGraphicsOpacityEffect as _OFX
        steps = self._FADE_STEPS
        if _step == 0:
            _fx = _OFX(widget)
            widget.setGraphicsEffect(_fx)
        opacity = (1.0 - _step / steps) if out else (_step / steps)
        _fx.setOpacity(opacity)
        if _step >= steps:
            if out:
                widget.hide()
            if done:
                done()
            return
        QTimer.singleShot(
            self._FADE_INTERVAL,
            lambda: self._fade_widget(widget, out, done, _step + 1, _fx)
        )

    def _go_to(self, index: int):
        current = self._stack.currentWidget()
        def _swap():
            self._stack.setCurrentIndex(index)
            nxt = self._stack.currentWidget()
            nxt.show()
            self._fade_widget(nxt, out=False)
        self._fade_widget(current, out=True, done=_swap)

    # ── Public API ────────────────────────────────────────────────────────

    def set_strings(self, strings: Dict):
        self.strings = strings or {}
        is_kriol = self.strings.get("back", "Back").strip().lower() == "bek"
        emg_text = "⚠️  Imijensi" if is_kriol else "⚠️  Emergency"
        # Step 1
        self._s1._emg_btn.setText(emg_text)
        # Step 2
        self._s2._back_btn.setText("← Bek" if is_kriol else "← Back")
        self._s2._emg_btn.setText(emg_text)
        self._s2._sym_hdr.setText(
            "Sikwan sain bin faindim:" if is_kriol else "Symptoms detected:"
        )
        self._s2._help_btn.set_kriol(is_kriol)

    def set_result(self, result_data: Dict):
        self._result_data = (result_data or {}).get("result", result_data or {})
        self._nlp_data    = (result_data or {}).get("nlp", {}) or {}
        self._answers     = (result_data or {}).get("answers", {}) or {}
        # Reset any leftover hide()/opacity effects from a previous _go_to fade
        for w in (self._s1, self._s2):
            w.setGraphicsEffect(None)
            w.show()
        self._stack.setCurrentIndex(0)
        self._render()

    # ── Internal ──────────────────────────────────────────────────────────

    def _is_kriol(self) -> bool:
        return str(self._nlp_data.get("ui_language", "")).lower() in {"kriol", "kr"}

    def _t(self, en: str, kr: str) -> str:
        return kr if self._is_kriol() else en

    def _triage(self) -> str:
        t = str(self._result_data.get("triage_level", "mild")).lower().strip()
        return t if t in _P else "mild"

    def _detected_symptoms(self) -> List[str]:
        syms = self._result_data.get("detected_symptoms") or self._nlp_data.get("display_symptoms") or []
        kr = self._is_kriol()
        out = []
        for s in syms:
            if isinstance(s, dict):
                out.append(s.get("kriol_label" if kr else "label") or s.get("display") or "")
            elif isinstance(s, str):
                out.append(s)
        return [x for x in out if x]

    def _render(self):
        triage   = self._triage()
        kr       = self._is_kriol()

        # Play severity audio → hero bounce, then tapmore audio → CTA button bounce
        _stop_all()
        prefix = "Kriol" if kr else "English"
        if triage == "mild":
            sev_audio = f"{prefix}-low.mp3"
        elif triage == "moderate":
            sev_audio = f"{prefix}-mid.mp3"
        else:  # critical
            sev_audio = f"{prefix}-high.mp3"
        tapmore_audio = f"{prefix}-tapmore.mp3"

        def _after_severity():
            self._animate_severity_hero()
            _play_sequence([tapmore_audio], on_complete=self._animate_cta_btn)

        _play_sequence([sev_audio], on_complete=_after_severity)

        content  = self._result_data.get("result_content", {}) or {}
        condition = self._result_data.get("predicted_disease") or self._t(
            "General health problem", "Jeneral helt trabul"
        )
        conf = self._result_data.get("confidence_label") or "Medium"
        symptoms = self._detected_symptoms()

        en_cta, kr_cta = _CTA[triage]
        steps = content.get("what_to_do") or [
            self._t("Rest", "Rest"),
            self._t("Drink water", "Dringgim woda"),
            self._t("Monitor your symptoms", "Lukluk yu simptom"),
        ]
        en_esc, kr_esc = _ESC[triage]

        # Hero (persistent left panel)
        self._hero.update(triage, condition, conf, kr)

        # Step 1
        self._s1.update(
            triage    = triage,
            condition = condition,
            cta_text  = kr_cta if kr else en_cta,
            kr        = kr,
        )

        # Step 2 (combined: what to do + what we found)
        self._s2.update(
            triage      = triage,
            steps       = steps,
            symptoms    = symptoms,
            esc_text    = kr_esc if kr else en_esc,
            done_text   = self._t("↻  Start Again", "↻  Stat Agen"),
            todo_title  = self._t("What to do", "Wanim fo du"),
            found_title = self._t("What we found", "Wanim bin faindim"),
        )

    def _on_what_to_do_clicked(self):
        """Transition to step 2 then speak the details aloud."""
        import src.utils.audio as _audio_mod
        _stop_all()
        _audio_mod._stopped = False   # allow TTS to start after transition
        self._go_to(1)
        # Wait for fade transition to finish before speaking
        QTimer.singleShot(300, self._speak_step2)

    def _speak_step2(self):
        """TTS: detected symptoms → what to do steps → recommendation."""
        import threading
        import src.utils.audio as _audio_mod
        if _audio_mod._stopped:
            return
        symptoms = self._detected_symptoms()
        triage   = self._triage()
        content  = self._result_data.get("result_content", {}) or {}
        steps    = content.get("what_to_do") or []
        condition = self._result_data.get("predicted_disease") or "a general health problem"
        en_esc, kr_esc = _ESC[triage]
        kr = self._is_kriol()

        parts = []
        if symptoms:
            sym_str = ", ".join(symptoms)
            parts.append(
                f"Mifela bin faindim {sym_str} from yu tok." if kr
                else f"We have detected {sym_str} from your input."
            )
        else:
            parts.append(
                "Mifela no bin faindim sikwan sain." if kr
                else "We could not detect specific symptoms."
            )

        if steps:
            steps_str = ". ".join(steps[:3])
            parts.append(
                f"Yu mas {steps_str}." if kr
                else f"You should {steps_str}."
            )

        parts.append(
            f"Mifela rekamend: {condition}." if kr
            else f"Our recommendation is {condition}."
        )

        full_text = "  ".join(parts)
        threading.Thread(target=self._speak_text, args=(full_text,), daemon=True).start()

    def _speak_text(self, text: str):
        """Speak using macOS 'say' command, falling back to pyttsx3."""
        import subprocess, sys
        import src.utils.audio as _audio_mod
        try:
            if sys.platform == "darwin":
                proc = subprocess.Popen(["say", text])
                _audio_mod._tts_proc = proc
                proc.wait()
                if _audio_mod._tts_proc is proc:
                    _audio_mod._tts_proc = None
            else:
                import pyttsx3
                engine = pyttsx3.init()
                engine.setProperty("rate", 150)
                engine.say(text)
                engine.runAndWait()
        except Exception:
            pass

    def _animate_severity_hero(self):
        widget = self._hero
        orig   = widget.geometry()
        nudged = orig.translated(0, -14)
        a1 = QPropertyAnimation(widget, b"geometry", widget)
        a1.setDuration(150)
        a1.setStartValue(orig)
        a1.setEndValue(nudged)
        a1.setEasingCurve(QEasingCurve.OutQuad)
        a2 = QPropertyAnimation(widget, b"geometry", widget)
        a2.setDuration(300)
        a2.setStartValue(nudged)
        a2.setEndValue(orig)
        a2.setEasingCurve(QEasingCurve.OutBack)
        a1.finished.connect(a2.start)
        a1.start()
        widget._sev_a1 = a1
        widget._sev_a2 = a2

    def _animate_cta_btn(self):
        """Bounce the 'What should I do?' button after tapmore audio finishes."""
        btn = self._s1._cta_btn
        orig   = btn.geometry()
        nudged = orig.translated(0, -12)
        a1 = QPropertyAnimation(btn, b"geometry", btn)
        a1.setDuration(130)
        a1.setStartValue(orig)
        a1.setEndValue(nudged)
        a1.setEasingCurve(QEasingCurve.OutQuad)
        a2 = QPropertyAnimation(btn, b"geometry", btn)
        a2.setDuration(260)
        a2.setStartValue(nudged)
        a2.setEndValue(orig)
        a2.setEasingCurve(QEasingCurve.OutBack)
        a1.finished.connect(a2.start)
        a1.start()
        btn._cta_a1 = a1
        btn._cta_a2 = a2
