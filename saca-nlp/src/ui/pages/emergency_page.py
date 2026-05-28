"""Emergency Help – popup modal styled like SymptomPopup."""
from __future__ import annotations
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QDialog, QScrollArea,
)


def _divider() -> QFrame:
    d = QFrame(); d.setFixedHeight(1)
    d.setStyleSheet("background:#E8D5CC; border:none;")
    return d


def _section_title(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        "font-size:12px; font-weight:900; letter-spacing:1.2px;"
        "color:#8B6B5A; background:transparent;"
    )
    return lbl


def _sign_row(icon: str, text: str) -> QWidget:
    row = QWidget(); row.setStyleSheet("background:transparent;")
    lay = QHBoxLayout(row); lay.setContentsMargins(0,0,0,0); lay.setSpacing(12)
    dot = QLabel(icon); dot.setFixedWidth(28); dot.setAlignment(Qt.AlignCenter)
    dot.setStyleSheet("font-size:18px; background:transparent;")
    lbl = QLabel(text); lbl.setWordWrap(True)
    lbl.setStyleSheet("font-size:15px; font-weight:700; color:#2D1810; background:transparent;")
    lay.addWidget(dot); lay.addWidget(lbl, 1)
    return row


def _call_card(number: str, label: str, sub: str, color: str) -> QFrame:
    card = QFrame()
    card.setStyleSheet(f"QFrame {{ background:{color}; border-radius:14px; border:none; }}")
    lay = QVBoxLayout(card); lay.setContentsMargins(16,14,16,14); lay.setSpacing(2)
    n = QLabel(number); n.setAlignment(Qt.AlignCenter)
    n.setStyleSheet("font-size:36px; font-weight:900; color:#FFFFFF; background:transparent;")
    la = QLabel(label); la.setAlignment(Qt.AlignCenter)
    la.setStyleSheet("font-size:13px; font-weight:800; color:rgba(255,255,255,0.95); background:transparent;")
    sb = QLabel(sub); sb.setAlignment(Qt.AlignCenter); sb.setWordWrap(True)
    sb.setStyleSheet("font-size:11px; font-weight:500; color:rgba(255,255,255,0.70); background:transparent;")
    lay.addWidget(n); lay.addWidget(la); lay.addWidget(sb)
    return card


class EmergencyPopup(QDialog):
    def __init__(self, strings: dict, parent=None):
        super().__init__(parent, Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)

        s     = strings
        is_kr = s.get("back", "Back").strip().lower() == "bek"

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)

        card = QFrame(); card.setObjectName("emgCard"); card.setFixedWidth(520)
        card.setStyleSheet("""
            QFrame#emgCard {
                background: #FDFAF6;
                border-radius: 20px;
                border: 1px solid rgba(139,58,46,0.18);
            }
        """)
        outer.addWidget(card, 0, Qt.AlignCenter)

        root = QVBoxLayout(card)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(0)

        # Header
        header = QFrame()
        header.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #C00000, stop:1 #8B0000); border-radius:12px; border:none;"
        )
        h_lay = QHBoxLayout(header); h_lay.setContentsMargins(18,14,18,14); h_lay.setSpacing(10)
        emg_icon = QLabel("🚨"); emg_icon.setStyleSheet("font-size:28px; background:transparent;")
        h_lay.addWidget(emg_icon)
        title_lbl = QLabel(s.get("emergency", "Emergency Help"))
        title_lbl.setStyleSheet("font-size:20px; font-weight:900; color:#FFFFFF; background:transparent;")
        h_lay.addWidget(title_lbl, 1)
        close_x = QPushButton("✕"); close_x.setFixedSize(30,30); close_x.setCursor(Qt.PointingHandCursor)
        close_x.setStyleSheet("""
            QPushButton { background:rgba(255,255,255,0.22); color:#FFF;
                border:none; border-radius:15px; font-size:13px; font-weight:700; }
            QPushButton:hover { background:rgba(255,255,255,0.38); }
        """)
        close_x.clicked.connect(self.reject)
        h_lay.addWidget(close_x)
        root.addWidget(header)
        root.addSpacing(18)

        # Call cards
        cr = QHBoxLayout(); cr.setSpacing(12)
        cr.addWidget(_call_card("000",
            "Ambulance / Police / Fire" if not is_kr else "Ambyulens / Polis / Faia",
            "Australia emergency" if not is_kr else "Ostrelia emajensii", "#C00000"))
        cr.addWidget(_call_card("131 450",
            "Interpreter Service" if not is_kr else "Interprita Sevis",
            "Free 24/7 translation" if not is_kr else "Fri translesen", "#8B3A2E"))
        root.addLayout(cr)
        root.addSpacing(18)
        root.addWidget(_divider())
        root.addSpacing(14)

        # Warning signs
        root.addWidget(_section_title(
            "CALL 000 IMMEDIATELY IF YOU HAVE:" if not is_kr else "KOLIM 000 KWIKWAN IF YU GAT:"))
        root.addSpacing(10)

        signs = [
            ("🫁", s.get("emergency_item_1", "Kandubala brid" if is_kr else "Trouble breathing")),
            ("💔",  s.get("emergency_item_2", "Jes bala" if is_kr else "Chest pain or pressure")),
            ("🩸",  s.get("emergency_item_3", "Blad kamaut tumas" if is_kr else "Heavy or uncontrolled bleeding")),
            ("😵",  s.get("emergency_item_4", "Pasautkol / Nomo weikap" if is_kr else "Passed out or unconscious")),
            ("😴",  s.get("emergency_item_5", "Kandubala weikap" if is_kr else "Difficult to wake up")),
            ("⚡",      "Seizures or convulsions" if not is_kr else "Sisis o konvulsin"),
            ("🗣",  "Sudden speech difficulty" if not is_kr else "Kandubala toktok"),
            ("👁",  "Sudden vision loss" if not is_kr else "Kandubala no si"),
        ]

        scroll = QScrollArea(); scroll.setFixedHeight(200); scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background:transparent; border:none; }")
        sw = QWidget(); sw.setStyleSheet("background:transparent;")
        sl = QVBoxLayout(sw); sl.setContentsMargins(0,0,0,0); sl.setSpacing(6)
        for ico, txt in signs:
            sl.addWidget(_sign_row(ico, txt))
        scroll.setWidget(sw)
        root.addWidget(scroll)
        root.addSpacing(14)
        root.addWidget(_divider())
        root.addSpacing(14)

        # Bottom note
        note = QFrame()
        note.setStyleSheet("QFrame { background:#FFF5F5; border-radius:12px; border:1.5px solid #FFAAAA; }")
        nl = QHBoxLayout(note); nl.setContentsMargins(14,10,14,10); nl.setSpacing(10)
        pin_icon = QLabel("📍"); pin_icon.setStyleSheet("font-size:18px; background:transparent;")
        nl.addWidget(pin_icon)
        nt = QLabel(s.get("emergency_instruction",
            "If you cannot call, go to the nearest clinic or hospital immediately."
            if not is_kr else "If yu no ken kolim, gowei klinik o hospital kwikwan."))
        nt.setWordWrap(True)
        nt.setStyleSheet("font-size:13px; font-weight:700; color:#8B0000; background:transparent;")
        nl.addWidget(nt, 1)
        root.addWidget(note)
        root.addSpacing(18)

        # Action buttons
        br = QHBoxLayout(); br.setSpacing(12)
        back_lbl = s.get("go_back_label", "Gobek" if is_kr else "Close")
        back_btn = QPushButton(f"←  {back_lbl}")
        back_btn.setFixedHeight(48); back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setStyleSheet("""
            QPushButton { background:#F2E1C9; color:#8B3A2E; border:2px solid #D4B8B0;
                border-radius:12px; font-size:15px; font-weight:800; }
            QPushButton:hover { background:#E8D0B5; }
        """)
        back_btn.clicked.connect(self.reject)

        call_btn = QPushButton(("📞  Call 000 Now") if not is_kr else ("📞  Kolim 000 Nau"))
        call_btn.setFixedHeight(48); call_btn.setCursor(Qt.PointingHandCursor)
        call_btn.setStyleSheet("""
            QPushButton { background:#C00000; color:#FFFFFF; border:none;
                border-radius:12px; font-size:15px; font-weight:900; }
            QPushButton:hover { background:#990000; }
        """)
        br.addWidget(back_btn, 1); br.addWidget(call_btn, 2)
        root.addLayout(br)


# Page stub for MainWindow stack
class EmergencyPage(QWidget):
    back_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.strings: dict = {}

    def show_popup(self, parent=None) -> None:
        EmergencyPopup(self.strings, parent=parent).exec()

    def set_strings(self, s: dict):
        self.strings = s
