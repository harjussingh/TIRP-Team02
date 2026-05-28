"""
Reusable help button + popup for all SACA screens.

Usage
-----
    btn = HelpButton(
        en_text="English help text for this screen.",
        kr_text="Kriol help text blong diswan skrin.",
        parent=self,
    )
    # Place btn anywhere in your layout.
    # Call btn.set_kriol(True/False) from set_strings().
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QPainter, QPainterPath, QFont
from PySide6.QtWidgets import (
    QWidget, QPushButton, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QSizePolicy, QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
)


# ── Popup dialog ──────────────────────────────────────────────────────────────
class HelpPopup(QDialog):
    def __init__(self, title: str, body: str, close_label: str = "Got it", parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self.setMinimumWidth(420)
        self.setMaximumWidth(520)

        # ── outer shadow/overlay container ──
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setAlignment(Qt.AlignCenter)

        card = QWidget()
        card.setObjectName("helpCard")
        card.setStyleSheet("""
            QWidget#helpCard {
                background: #FDFAF6;
                border-radius: 20px;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 60))
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # ── header ──
        header = QWidget()
        header.setFixedHeight(72)
        header.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #8B3A2E, stop:1 #5A1F16);"
            "border-top-left-radius: 20px; border-top-right-radius: 20px;"
        )
        header_lay = QHBoxLayout(header)
        header_lay.setContentsMargins(24, 0, 24, 0)

        icon_lbl = QLabel("❓")
        icon_lbl.setStyleSheet(
            "font-size:28px; background:transparent; color:white;"
        )
        self._title_lbl = QLabel(title)
        self._title_lbl.setStyleSheet(
            "font-size:20px; font-weight:900; color:white; background:transparent;"
        )
        header_lay.addWidget(icon_lbl)
        header_lay.addSpacing(12)
        header_lay.addWidget(self._title_lbl, 1)

        card_layout.addWidget(header)

        # ── body ──
        self._body_lbl = QLabel(body)
        self._body_lbl.setWordWrap(True)
        self._body_lbl.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self._body_lbl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self._body_lbl.setStyleSheet(
            "font-size:15px; font-weight:600; color:#3D2B1F; "
            "background:transparent;"
        )

        body_wrapper = QWidget()
        body_wrapper.setStyleSheet("background:transparent;")
        bw_lay = QVBoxLayout(body_wrapper)
        bw_lay.setContentsMargins(24, 16, 24, 16)
        bw_lay.addWidget(self._body_lbl)

        card_layout.addWidget(body_wrapper)

        # ── divider ──
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background:#E8D5CC; border:none;")
        card_layout.addWidget(div)

        # ── close button ──
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(24, 16, 24, 20)
        self._close_btn = QPushButton(close_label)
        self._close_btn.setFixedHeight(46)
        self._close_btn.setCursor(Qt.PointingHandCursor)
        self._close_btn.setStyleSheet("""
            QPushButton {
                background:#8B3A2E; color:#FFFFFF; border:none;
                border-radius:12px; font-size:15px; font-weight:900;
            }
            QPushButton:hover { background:#6B2A1E; }
        """)
        self._close_btn.clicked.connect(self.accept)
        btn_row.addStretch()
        btn_row.addWidget(self._close_btn, 2)
        btn_row.addStretch()

        bottom = QWidget()
        bottom.setStyleSheet("background:transparent;")
        bottom.setLayout(btn_row)
        card_layout.addWidget(bottom)

        outer.addWidget(card)

        # fade-in animation
        self._fx = QGraphicsOpacityEffect(self)
        self._fx.setOpacity(0.0)
        self.setGraphicsEffect(self._fx)
        self._anim = QPropertyAnimation(self._fx, b"opacity", self)
        self._anim.setDuration(180)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

    def showEvent(self, event):
        super().showEvent(event)
        self._anim.start()

    def update_content(self, title: str, body: str, close_label: str = "Got it"):
        self._title_lbl.setText(title)
        self._body_lbl.setText(body)
        self._close_btn.setText(close_label)

    # click outside the card to close
    def mousePressEvent(self, event):
        self.accept()


# ── Help button ───────────────────────────────────────────────────────────────
class HelpButton(QPushButton):
    """
    Round '?' button. Pass en_text and kr_text; call set_kriol() from set_strings().
    """
    def __init__(self, en_title: str, en_text: str,
                 kr_title: str, kr_text: str,
                 parent=None):
        super().__init__("", parent)   # no text — we paint it manually
        self._en_title = en_title
        self._en_text  = en_text
        self._kr_title = kr_title
        self._kr_text  = kr_text
        self._is_kriol = False

        self.setFixedSize(36, 36)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Help / Elp")
        # Flat stylesheet — no text-related properties so macOS doesn't swallow them
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
        """)
        self.clicked.connect(self._show_popup)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        pressed = self.isDown()
        hovered = self.underMouse()

        # Circle fill
        if pressed:
            fill = QColor(139, 58, 46, 90)
        elif hovered:
            fill = QColor(139, 58, 46, 60)
        else:
            fill = QColor(139, 58, 46, 30)

        p.setPen(Qt.NoPen)
        p.setBrush(fill)
        p.drawEllipse(1, 1, 34, 34)

        # Circle border
        from PySide6.QtGui import QPen as _QPen
        border_pen = _QPen(QColor("#8B3A2E"), 2)
        p.setPen(border_pen)
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(1, 1, 34, 34)

        # "?" text
        f = QFont()
        f.setPixelSize(18)
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor("#8B3A2E"))
        p.drawText(self.rect(), Qt.AlignCenter, "?")
        p.end()

    def set_kriol(self, kriol: bool):
        self._is_kriol = kriol

    def _show_popup(self):
        if self._is_kriol:
            title = self._kr_title
            body  = self._kr_text
            close = "Orait, Tenk yu"
        else:
            title = self._en_title
            body  = self._en_text
            close = "Got it, thanks"
        parent = self.window()
        popup = HelpPopup(title, body, close, parent=parent)
        popup.exec()
