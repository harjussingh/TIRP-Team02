"""
Human Body Symptom Selection Page
===================================
Interactive human body diagram — user taps a body zone, a symptom
popup appears, they select symptoms, chips are shown.
Matches the hero + right-panel design system used throughout SACA.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple

from PySide6.QtCore import Qt, Signal, QPointF, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import (
    QPainter, QPen, QColor, QPainterPath, QLinearGradient, QFont,
)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy, QDialog, QScrollArea, QGridLayout,
)
from src.ui.widgets.help_popup import HelpButton
from src.utils.audio import play_sequence as _play_sequence, stop_all as _stop_all


# ── Body region → symptoms data ───────────────────────────────────────────────
# Each tuple: (vocab_name, English label, Kriol label)
BODY_REGION_SYMPTOMS: Dict[str, List[Tuple[str, str, str]]] = {
    "head": [
        ("headache",         "Headache",           "Hedake"),
        ("severe_headache",  "Severe headache",    "Brabli hedake"),
        ("dizziness",        "Dizziness",          "Dizi"),
        ("confusion",        "Confusion",          "Konfius"),
        ("blurred_vision",   "Blurred vision",     "No si gud"),
        ("ear_pain",         "Ear pain",           "Ia pein"),
        ("eye_pain",         "Eye pain",           "Ai pein"),
        ("runny_nose",       "Runny nose",         "Nos ron"),
        ("facial_drooping",  "Face drooping",      "Fes poldaun"),
    ],
    "throat": [
        ("sore_throat",            "Sore throat",           "Throt pein"),
        ("difficulty_swallowing",  "Difficulty swallowing", "Had fo swalo"),
        ("swollen_lymph_nodes",    "Swollen neck glands",   "Nek swelin"),
        ("stiff_neck",             "Stiff neck",            "Nek tait"),
    ],
    "chest": [
        ("chest_pain",            "Chest pain",           "Jes pein"),
        ("severe_chest_pain",     "Severe chest pain",    "Brabli jes pein"),
        ("chest_tightness",       "Chest tightness",      "Jes tait"),
        ("shortness_of_breath",   "Shortness of breath",  "Short brith"),
        ("difficulty_breathing",  "Difficulty breathing", "Had fo brith"),
        ("cough",                 "Cough",                "Kof"),
        ("productive_cough",      "Cough with mucus",     "Kof wit gris"),
        ("wheezing",              "Wheezing",             "Wizing"),
        ("palpitations",          "Heart racing",         "Hat rantawei"),
        ("coughing_blood",        "Coughing blood",       "Kof blad"),
    ],
    "abdomen": [
        ("abdominal_pain",         "Stomach pain",        "Beli pein"),
        ("severe_abdominal_pain",  "Severe stomach pain", "Brabli beli pein"),
        ("nausea",                 "Nausea",              "Fil laik spyu"),
        ("vomiting",               "Vomiting",            "Spyu"),
        ("vomiting_blood",         "Vomiting blood",      "Spyu blad"),
        ("diarrhea",               "Diarrhea",            "Ranishit"),
        ("bloating",               "Bloating",            "Beli big ap"),
        ("loss_of_appetite",       "No appetite",         "No laik kakae"),
        ("constipation",           "Constipation",        "Had fo pus"),
    ],
    "back": [
        ("back_pain",         "Back pain",        "Bek pein"),
        ("severe_back_pain",  "Severe back pain", "Brabli bek pein"),
        ("shoulder_pain",     "Shoulder pain",    "Sholda pein"),
    ],
    "left_arm": [
        ("arm_pain",      "Arm pain",     "Aam pein"),
        ("arm_weakness",  "Arm weakness", "Aam wik"),
        ("swelling",      "Swelling",     "Swelin"),
        ("bruising",      "Bruising",     "Brus"),
    ],
    "right_arm": [
        ("arm_pain",      "Arm pain",     "Aam pein"),
        ("arm_weakness",  "Arm weakness", "Aam wik"),
        ("swelling",      "Swelling",     "Swelin"),
        ("bruising",      "Bruising",     "Brus"),
    ],
    "left_leg": [
        ("leg_pain",           "Leg pain",           "Leg pein"),
        ("leg_swelling",       "Leg swelling",       "Leg swelin"),
        ("ankle_swelling",     "Ankle swelling",     "Enkol swelin"),
        ("difficulty_walking", "Difficulty walking", "Had fo wokabat"),
        ("bruising",           "Bruising",           "Brus"),
    ],
    "right_leg": [
        ("leg_pain",           "Leg pain",           "Leg pein"),
        ("leg_swelling",       "Leg swelling",       "Leg swelin"),
        ("ankle_swelling",     "Ankle swelling",     "Enkol swelin"),
        ("difficulty_walking", "Difficulty walking", "Had fo wokabat"),
        ("bruising",           "Bruising",           "Brus"),
    ],
    "whole_body": [
        ("fever",        "Fever",        "Fiba"),
        ("high_fever",   "High fever",   "Brabli fiba"),
        ("fatigue",      "Fatigue",      "Brabli taid"),
        ("body_aches",   "Body aches",   "Bodi pein"),
        ("chills",       "Chills",       "Kolkol"),
        ("sweating",     "Sweating",     "Swet"),
        ("weakness",     "Weakness",     "Wik"),
        ("rash",         "Rash",         "Skin trabul"),
        ("itching",      "Itching",      "Isi isi"),
        ("dehydration",  "Dehydration",  "No wota"),
    ],
}

# (English label, Kriol label, emoji)
BODY_REGION_LABELS: Dict[str, Tuple[str, str, str]] = {
    "head":       ("Head",        "Hed",       "🧠"),
    "throat":     ("Throat",      "Throt",     "🦷"),
    "chest":      ("Chest",       "Jes",       "🫀"),
    "abdomen":    ("Stomach",     "Beli",      "🫃"),
    "back":       ("Back",        "Bek",       "🔙"),
    "left_arm":   ("Left arm",    "Lef aam",   "💪"),
    "right_arm":  ("Right arm",   "Rait aam",  "💪"),
    "left_leg":   ("Left leg",    "Lef leg",   "🦵"),
    "right_leg":  ("Right leg",   "Rait leg",  "🦵"),
    "whole_body": ("Whole body",  "Ol bodi",   "🌡"),
}


# ── Hero panel (same gradient as all other pages) ─────────────────────────────
class _HeroPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(300)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, QColor("#8B3A2E"))
        grad.setColorAt(1.0, QColor("#5A1F16"))
        p.fillRect(0, 0, w, h, grad)
        for cx, cy, r, alpha in [(260, 80, 90, 18), (40, 400, 120, 12), (180, 580, 60, 10)]:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(255, 255, 255, alpha))
            p.drawEllipse(int(cx - r), int(cy - r), int(r * 2), int(r * 2))
        p.setBrush(QColor("#D4A017"))
        p.drawRect(0, h - 6, w, 6)


# ── Interactive body diagram ──────────────────────────────────────────────────
class BodyDiagramWidget(QWidget):
    """
    Human body diagram with anatomically correct proportions fitted to a
    200×400 canvas using the 8-head rule (head unit ≈ 47 px).
    Arms end at hip/wrist level (~y 220).  Feet stay within y 394.
    All limb contours use cubic bezier curves — no straight edges.
    """
    region_clicked = Signal(str)

    _CW, _CH = 200, 400

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(self._CW, self._CH)
        self.setMouseTracking(True)
        self._hovered: Optional[str] = None
        self._active:  Set[str]      = set()
        self._cached_silhouette: Optional[QPainterPath] = None
        self._cached_paths:      Optional[Dict[str, QPainterPath]] = None

    def set_active_regions(self, regions: Set[str]):
        self._active = regions
        self.update()

    # ── silhouette ────────────────────────────────────────────────────────
    def _silhouette(self) -> QPainterPath:
        if self._cached_silhouette is not None:
            return self._cached_silhouette

        # Head – natural oval (center y=27, rx=19, ry=23 → top y=4, chin y=50)
        head = QPainterPath()
        head.addEllipse(QPointF(100.0, 27.0), 19.0, 23.0)

        # Small ear bumps
        le = QPainterPath(); le.addEllipse(QPointF(81.0, 29.0), 3.5, 5.5)
        re = QPainterPath(); re.addEllipse(QPointF(119.0, 29.0), 3.5, 5.5)

        # ── Full body path – clockwise from left neck base ──
        # Key y landmarks (8-head, H≈47):
        #   neck-base  y=50   shoulder y=65   chest y=112
        #   navel      y=159  hip      y=206  crotch y=222
        #   knee       y=312  ankle    y=372  foot   y=392
        # Key x landmarks (shoulder-to-shoulder ≈ 116 px, centred at 100):
        #   left arm outer x=26  left arm inner x=46
        #   right arm inner x=154  right arm outer x=174
        #   waist x=65–135   hip x=55–145

        body = QPainterPath()
        body.moveTo(91, 50)  # left neck base

        # ── left shoulder sweep ──
        body.cubicTo(80, 50, 46, 60, 33, 70)
        body.cubicTo(28, 74, 26, 80, 26, 88)  # deltoid

        # ── left outer arm (going down, slight outward bow mid-arm) ──
        body.cubicTo(24, 110, 22, 148, 24, 186)
        body.cubicTo(24, 196, 24, 206, 26, 212)

        # ── left wrist (rounded, going right) ──
        body.cubicTo(26, 218, 30, 222, 36, 222)
        body.cubicTo(42, 222, 46, 222, 48, 222)
        body.cubicTo(52, 222, 54, 218, 54, 212)

        # ── left inner arm (going up) ──
        body.cubicTo(54, 202, 52, 162, 50, 124)
        body.cubicTo(50, 102, 52, 88, 58, 80)

        # ── left armpit corner ──
        body.cubicTo(60, 78, 64, 76, 67, 76)

        # ── left torso side: chest → waist → hip ──
        body.cubicTo(65, 100, 63, 136, 62, 162)   # chest (gentle inward)
        body.cubicTo(61, 182, 59, 200, 57, 212)   # waist
        body.cubicTo(56, 220, 54, 226, 53, 232)   # hip flare

        # ── left outer leg (slight bow outward at knee) ──
        body.cubicTo(49, 252, 45, 290, 43, 322)
        body.cubicTo(41, 350, 42, 366, 43, 374)

        # ── left foot (rounded, going right) ──
        body.cubicTo(43, 382, 47, 390, 54, 392)
        body.cubicTo(62, 394, 70, 394, 78, 394)
        body.cubicTo(85, 394, 88, 390, 88, 382)

        # ── left inner leg (going up) ──
        body.cubicTo(87, 366, 85, 348, 84, 318)
        body.cubicTo(83, 285, 83, 258, 86, 242)

        # ── crotch curve ──
        body.cubicTo(88, 234, 93, 230, 100, 230)
        body.cubicTo(107, 230, 112, 234, 114, 242)

        # ── right inner leg (going down) ──
        body.cubicTo(117, 258, 117, 285, 116, 318)
        body.cubicTo(115, 348, 113, 366, 112, 382)

        # ── right foot ──
        body.cubicTo(112, 390, 115, 394, 122, 394)
        body.cubicTo(130, 394, 138, 394, 146, 392)
        body.cubicTo(153, 390, 157, 382, 157, 374)

        # ── right outer leg (going up) ──
        body.cubicTo(158, 366, 159, 350, 157, 322)
        body.cubicTo(155, 290, 151, 252, 147, 232)

        # ── right torso side: hip → waist → chest ──
        body.cubicTo(146, 226, 144, 220, 143, 212)
        body.cubicTo(141, 200, 139, 182, 138, 162)
        body.cubicTo(137, 136, 135, 100, 133, 76)

        # ── right armpit corner ──
        body.cubicTo(136, 76, 140, 78, 142, 80)

        # ── right inner arm (going down) ──
        body.cubicTo(148, 88, 150, 102, 150, 124)
        body.cubicTo(148, 162, 146, 202, 146, 212)

        # ── right wrist (going right: inner → outer) ──
        body.cubicTo(146, 218, 148, 222, 152, 222)
        body.cubicTo(158, 222, 164, 222, 166, 222)
        body.cubicTo(170, 222, 174, 218, 174, 212)

        # ── right outer arm (going up) ──
        body.cubicTo(176, 206, 176, 196, 176, 186)
        body.cubicTo(178, 148, 176, 110, 174, 88)
        body.cubicTo(174, 80, 172, 74, 167, 70)

        # ── right shoulder back to right neck ──
        body.cubicTo(154, 60, 120, 50, 109, 50)
        body.closeSubpath()

        sil = head.united(body)
        sil = sil.united(le)
        sil = sil.united(re)
        self._cached_silhouette = sil
        return self._cached_silhouette

    # ── zone paths ────────────────────────────────────────────────────────
    def _paths(self) -> Dict[str, QPainterPath]:
        if self._cached_paths is not None:
            return self._cached_paths

        sil = self._silhouette()

        def clip(x: float, y: float, w: float, h: float) -> QPainterPath:
            box = QPainterPath()
            box.addRect(x, y, w, h)
            return box.intersected(sil)

        self._cached_paths = {
            "head":      clip(81,   4, 38, 46),   # head (x=81–119, y=4–50)
            "throat":    clip(88,  50, 24, 28),   # neck
            "chest":     clip(62,  78, 76, 86),   # upper torso (armpit to navel)
            "abdomen":   clip(57, 164, 86, 68),   # lower torso (navel to hip)
            "left_arm":  clip(22,  76, 48, 150),  # left arm (x=22–70, y=76–226)
            "right_arm": clip(130, 76, 48, 150),  # right arm (x=130–178, y=76–226)
            "left_leg":  clip(43, 232, 50, 164),  # left leg (y=232–396)
            "right_leg": clip(107, 232, 50, 164), # right leg
        }
        return self._cached_paths

    def _region_at(self, pos: QPointF) -> Optional[str]:
        for region, path in self._paths().items():
            if path.contains(pos):
                return region
        return None

    # ── painting ──────────────────────────────────────────────────────────
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        sil   = self._silhouette()
        paths = self._paths()

        # 1 ── drop shadow
        p.save()
        p.translate(3, 4)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(60, 20, 10, 28))
        p.drawPath(sil)
        p.restore()

        # 2 ── warm skin fill
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#F2DDD0"))
        p.drawPath(sil)

        # 3 ── active zone overlays
        for region, path in paths.items():
            if region in self._active and region != self._hovered:
                p.setBrush(QColor(196, 97, 74, 100))
                p.drawPath(path)

        # 4 ── hover zone overlay
        if self._hovered and self._hovered in paths:
            p.setBrush(QColor(139, 58, 46, 145))
            p.drawPath(paths[self._hovered])

        # 5 ── anatomy detail lines
        p.setBrush(Qt.NoBrush)

        # Collarbone arcs
        p.setPen(QPen(QColor(160, 108, 85, 90), 0.9))
        cl = QPainterPath()
        cl.moveTo(100, 76)
        cl.cubicTo(88, 75, 76, 76, 67, 80)
        p.drawPath(cl)
        cr = QPainterPath()
        cr.moveTo(100, 76)
        cr.cubicTo(112, 75, 124, 76, 133, 80)
        p.drawPath(cr)

        # Pectoral hint
        p.setPen(QPen(QColor(160, 108, 85, 48), 0.8))
        pec = QPainterPath()
        pec.moveTo(64, 108)
        pec.cubicTo(78, 118, 122, 118, 136, 108)
        p.drawPath(pec)

        # Centre midline
        p.setPen(QPen(QColor(160, 108, 85, 40), 0.7, Qt.DashLine))
        p.drawLine(100, 78, 100, 230)

        # Navel
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(150, 100, 78, 115))
        p.drawEllipse(QPointF(100.0, 190.0), 2.6, 2.6)

        # Kneecaps
        p.setBrush(QColor(160, 108, 85, 52))
        p.setPen(QPen(QColor(160, 108, 85, 70), 0.9))
        p.drawEllipse(QPointF(67.0, 316.0), 9.0, 7.0)
        p.drawEllipse(QPointF(133.0, 316.0), 9.0, 7.0)

        # Ear inner
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(180, 128, 105, 75))
        p.drawEllipse(QPointF(81.0, 29.0), 1.8, 3.0)
        p.drawEllipse(QPointF(119.0, 29.0), 1.8, 3.0)

        # 6 ── outline
        p.setPen(QPen(QColor("#A06858"), 1.5))
        p.setBrush(Qt.NoBrush)
        p.drawPath(sil)

        # 7 ── zone separator hints
        p.setPen(QPen(QColor(168, 110, 88, 48), 0.8, Qt.DashLine))
        p.drawLine(88, 78, 112, 78)    # neck / chest
        p.drawLine(62, 164, 138, 164)  # chest / abdomen
        p.drawLine(57, 232, 143, 232)  # abdomen / legs

        # 8 ── active dot indicators
        for region, path in paths.items():
            if region in self._active:
                bb = path.boundingRect()
                cx = bb.right() - 9
                cy = bb.top() + 9
                p.setPen(Qt.NoPen)
                p.setBrush(QColor("#FFFFFF"))
                p.drawEllipse(QPointF(cx, cy), 7.0, 7.0)
                p.setBrush(QColor("#8B3A2E"))
                p.drawEllipse(QPointF(cx, cy), 4.5, 4.5)

        # 9 ── hover label pill
        if self._hovered and self._hovered in BODY_REGION_LABELS:
            lbl  = BODY_REGION_LABELS[self._hovered][0]
            path = paths[self._hovered]
            bb   = path.boundingRect()
            lx   = int(bb.right()) + 6
            ly   = int(bb.center().y())
            f    = QFont()
            f.setPointSize(8)
            f.setBold(True)
            p.setFont(f)
            fm = p.fontMetrics()
            tw = fm.horizontalAdvance(lbl)
            th = fm.height()
            if lx + tw + 18 > self._CW:
                lx = int(bb.left()) - tw - 24
            pill = QPainterPath()
            pill.addRoundedRect(lx - 2, ly - th / 2 - 5, tw + 16, th + 10, 8, 8)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(40, 18, 12, 225))
            p.drawPath(pill)
            p.setFont(f)
            p.setPen(QColor("#FFFFFF"))
            p.drawText(lx + 6, ly + th // 2 - 2, lbl)

    def mouseMoveEvent(self, event):
        pos = QPointF(float(event.x()), float(event.y()))
        region = self._region_at(pos)
        if region != self._hovered:
            self._hovered = region
            self.setCursor(Qt.PointingHandCursor if region else Qt.ArrowCursor)
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self._hovered = None
        self.setCursor(Qt.ArrowCursor)
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            region = self._region_at(QPointF(float(event.x()), float(event.y())))
            if region:
                self.region_clicked.emit(region)
        super().mousePressEvent(event)


# ── Symptom picker popup ──────────────────────────────────────────────────────
class SymptomPopup(QDialog):
    symptoms_confirmed = Signal(str, list)

    def __init__(self, region_key: str, already_selected: List[str],
                 language: str = "en", parent=None):
        super().__init__(parent)
        self._region_key = region_key
        self._language   = language
        self._checked: Set[str] = set(already_selected)

        is_kriol = language == "kriol"
        info     = BODY_REGION_LABELS.get(region_key, ("Symptoms", "Simptom", "\U0001fa7a"))
        icon     = info[2]
        title    = info[1] if is_kriol else info[0]
        symptoms = BODY_REGION_SYMPTOMS.get(region_key, [])

        self.setWindowTitle(f"{icon}  {title}")
        self.setFixedWidth(440)
        self.setStyleSheet("QDialog { background: #FDFAF6; }")

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 22, 28, 24)
        root.setSpacing(14)

        lbl = QLabel(f"{icon}  {title}")
        lbl.setStyleSheet(
            "font-size: 24px; font-weight: 900; color: #2D1810; background: transparent;"
        )
        root.addWidget(lbl)

        hint_text = ("Tap to select, tap again to remove."
                     if not is_kriol else "Klik fo selektem. Klik agen fo remouvim.")
        hint = QLabel(hint_text)
        hint.setStyleSheet("font-size: 13px; color: #8B6B5A; background: transparent;")
        root.addWidget(hint)

        div = QFrame(); div.setFixedHeight(1)
        div.setStyleSheet("background: #E8D5CC; border: none;")
        root.addWidget(div)

        self._btns: Dict[str, QPushButton] = {}
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)

        for idx, (vocab, en_lbl, kr_lbl) in enumerate(symptoms):
            label = kr_lbl if is_kriol else en_lbl
            btn   = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(vocab in self._checked)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumHeight(44)
            self._style_toggle(btn, btn.isChecked())
            btn.toggled.connect(lambda checked, v=vocab, b=btn: self._on_toggle(v, checked, b))
            self._btns[vocab] = btn
            grid.addWidget(btn, idx // 2, idx % 2)

        root.addLayout(grid)

        bottom = QHBoxLayout(); bottom.setSpacing(12)

        cancel = QPushButton("Cancel" if not is_kriol else "Kansol")
        cancel.setFixedHeight(48); cancel.setCursor(Qt.PointingHandCursor)
        cancel.setStyleSheet("""
            QPushButton { background:#F2E1C9; color:#8B3A2E; border:2px solid #D4B8B0;
                          border-radius:12px; font-size:15px; font-weight:800; }
            QPushButton:hover { background:#E8D0B5; }
        """)
        cancel.clicked.connect(self.reject)

        confirm_text = "Add symptoms  \u2192" if not is_kriol else "Aded simptom  \u2192"
        confirm = QPushButton(confirm_text)
        confirm.setFixedHeight(48); confirm.setCursor(Qt.PointingHandCursor)
        confirm.setStyleSheet("""
            QPushButton { background:#8B3A2E; color:#FFFFFF; border:none;
                          border-radius:12px; font-size:15px; font-weight:900; }
            QPushButton:hover { background:#6B2A1E; }
        """)
        confirm.clicked.connect(self._confirm)

        bottom.addWidget(cancel, 1)
        bottom.addWidget(confirm, 2)
        root.addLayout(bottom)

    def _style_toggle(self, btn: QPushButton, checked: bool):
        if checked:
            btn.setStyleSheet("""
                QPushButton { background:#8B3A2E; color:#FFFFFF; border:2px solid #8B3A2E;
                              border-radius:10px; font-size:14px; font-weight:800;
                              padding:4px 10px; }
                QPushButton:hover { background:#6B2A1E; }
            """)
        else:
            btn.setStyleSheet("""
                QPushButton { background:#FDF3EE; color:#5A2A1E; border:1.5px solid #D4B8B0;
                              border-radius:10px; font-size:14px; font-weight:700;
                              padding:4px 10px; }
                QPushButton:hover { background:#F2E1D5; }
            """)

    def _on_toggle(self, vocab: str, checked: bool, btn: QPushButton):
        if checked:
            self._checked.add(vocab)
        else:
            self._checked.discard(vocab)
        self._style_toggle(btn, checked)

    def _confirm(self):
        self.symptoms_confirmed.emit(self._region_key, list(self._checked))
        self.accept()


# ── Symptom chip ─────────────────────────────────────────────────────────────
class SymptomChip(QPushButton):
    removed = Signal(str)

    def __init__(self, vocab_name: str, label: str, parent=None):
        super().__init__(f"{label}  ×", parent)
        self.vocab_name = vocab_name
        self.setCursor(Qt.PointingHandCursor)

        # Bigger chip so text does not cut
        self.setFixedHeight(46)
        self.setMinimumWidth(155)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.setStyleSheet("""
            QPushButton {
                background:#8B3A2E;
                color:#FFFFFF;
                border:none;
                border-radius:23px;
                font-size:13px;
                font-weight:800;
                padding:8px 18px;
                text-align:center;
            }
            QPushButton:hover {
                background:#6B2A1E;
            }
        """)

        self.clicked.connect(lambda: self.removed.emit(vocab_name))


# ── Main page ─────────────────────────────────────────────────────────────────
class SymptomSelectionPage(QWidget):
    back_clicked      = Signal()
    emergency_clicked = Signal()
    continue_clicked  = Signal(str)

    def __init__(self):
        super().__init__()
        self.strings:   dict           = {}
        self._language: str            = "en"
        self._selected: Dict[str, str] = {}

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Hero
        hero = _HeroPanel()
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(32, 44, 24, 36)
        hero_layout.setSpacing(0)
        hero_layout.setAlignment(Qt.AlignTop)

        self._hero_title = QLabel("Show us\nwhere it hurts")
        self._hero_title.setWordWrap(True)
        self._hero_title.setStyleSheet(
            "font-size:34px; font-weight:900; color:#FFFFFF; background:transparent;"
        )
        self._hero_tag = QLabel("Tap a body part,\nthen pick\nyour symptoms")
        self._hero_tag.setWordWrap(True)
        self._hero_tag.setStyleSheet(
            "font-size:17px; font-weight:700; color:rgba(255,255,255,0.82); background:transparent;"
        )
        hero_layout.addStretch(1)
        hero_layout.addWidget(self._hero_title)
        hero_layout.addSpacing(16)
        hero_layout.addWidget(self._hero_tag)
        hero_layout.addStretch(2)
        dot_row = QHBoxLayout()
        for c in ["#D4A017", "#C65D2E", "#F2E6D8"]:
            dot = QFrame(); dot.setFixedSize(10, 10)
            dot.setStyleSheet(f"background:{c}; border-radius:5px;")
            dot_row.addWidget(dot)
        dot_row.addStretch()
        hero_layout.addLayout(dot_row)
        outer.addWidget(hero)

        # Right panel
        right = QWidget()
        right.setObjectName("homeRightPanel")
        right.setStyleSheet("QWidget#homeRightPanel { background: #FDFAF6; }")
        right.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        rl = QVBoxLayout(right)
        rl.setContentsMargins(32, 20, 32, 20)
        rl.setSpacing(0)

        self.back_btn = QPushButton("\u2190  Back")
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
        self.back_btn.clicked.connect(_stop_all)
        self.back_btn.clicked.connect(self.back_clicked.emit)
        self._help_btn = HelpButton(
            en_title="Body Map",
            en_text="Use the body diagram to show where you have pain or discomfort.\n\n"
                    "• Tap a body part on the diagram, OR\n"
                    "• Use the buttons on the right side to select a region.\n\n"
                    "After selecting a body part, choose your specific symptoms from the popup that appears.\n\n"
                    "Press Continue when you have selected all your symptoms.",
            kr_title="Bodi Mep",
            kr_text="Yusum bodi pikja blong shoim we i pein o yu fil nogud.\n\n"
                    "• Tapim wan pat bodi langa pikja, O\n"
                    "• Yusum batnit long rait sait blong jusum wan son.\n\n"
                    "Afta jusum wan pat bodi, jusum yu simptom long popup we bai kamap.\n\n"
                    "Pres Kontiniu taim yu jusum olgeta simptom.",
        )
        _top = QHBoxLayout()
        _top.setSpacing(0)
        _top.addWidget(self.back_btn, 0, Qt.AlignVCenter)
        _top.addStretch()
        _top.addWidget(self._help_btn, 0, Qt.AlignVCenter)
        rl.addLayout(_top)
        rl.addSpacing(8)

        self._heading = QLabel("Tap where it hurts")
        self._heading.setStyleSheet(
            "font-size:30px; font-weight:900; color:#2D1810; background:transparent;"
        )
        rl.addWidget(self._heading)

        self._subheading = QLabel("Select a body part then choose your symptoms")
        self._subheading.setStyleSheet(
            "font-size:14px; font-weight:700; color:#8B6B5A; background:transparent;"
        )
        rl.addWidget(self._subheading)
        rl.addSpacing(12)

        body_row = QHBoxLayout()
        body_row.setSpacing(20)
        body_row.setAlignment(Qt.AlignTop)

        # Body diagram — left aligned
        self._body = BodyDiagramWidget()
        body_row.addWidget(self._body, 0, Qt.AlignTop | Qt.AlignLeft)

        # Right side: zone hint + 2-column grid of zone buttons
        zones_panel = QVBoxLayout()
        zones_panel.setSpacing(6)
        zones_panel.setAlignment(Qt.AlignTop)
        zones_panel.addSpacing(4)

        self._zone_hint_lbl = QLabel("Tap a zone:")
        self._zone_hint_lbl.setStyleSheet(
            "font-size:12px; font-weight:900; color:#8B3A2E; background:transparent;"
        )
        zones_panel.addWidget(self._zone_hint_lbl)

        zones_grid = QGridLayout()
        zones_grid.setHorizontalSpacing(8)
        zones_grid.setVerticalSpacing(6)

        self._zone_btns: Dict[str, QPushButton] = {}
        zone_keys = ["head", "throat", "chest", "abdomen", "back",
                     "left_arm", "right_arm", "left_leg", "right_leg"]
        for idx, key in enumerate(zone_keys):
            info = BODY_REGION_LABELS[key]
            zbtn = QPushButton(f"{info[2]}  {info[0]}")
            zbtn.setCursor(Qt.PointingHandCursor)
            zbtn.setFixedHeight(34)
            zbtn.setStyleSheet("""
                QPushButton { background:#F2E8E3; color:#5A2A1E; border:1px solid #D4B8B0;
                              border-radius:8px; font-size:12px; font-weight:700;
                              padding:0px 10px; text-align:left; }
                QPushButton:hover { background:#E8D0C2; }
            """)
            zbtn.clicked.connect(lambda _, k=key: self._open_popup(k))
            self._zone_btns[key] = zbtn
            zones_grid.addWidget(zbtn, idx // 2, idx % 2)

        zones_panel.addLayout(zones_grid)
        zones_panel.addSpacing(8)

        self._whole_btn = QPushButton("\U0001f321  Whole body / General")
        self._whole_btn.setCursor(Qt.PointingHandCursor)
        self._whole_btn.setFixedHeight(36)
        self._whole_btn.setStyleSheet("""
            QPushButton { background:#8B3A2E; color:white; border:none;
                          border-radius:10px; font-size:12px; font-weight:900;
                          padding:0px 12px; }
            QPushButton:hover { background:#6B2A1E; }
        """)
        self._whole_btn.clicked.connect(lambda: self._open_popup("whole_body"))
        zones_panel.addWidget(self._whole_btn)
        zones_panel.addStretch()

        body_row.addLayout(zones_panel, 1)
        rl.addLayout(body_row)
        rl.addSpacing(12)

        div = QFrame(); div.setFixedHeight(1)
        div.setStyleSheet("background:#E8D5CC; border:none;")
        rl.addWidget(div)
        rl.addSpacing(8)

        self._count_label = QLabel("No symptoms selected yet")
        self._count_label.setStyleSheet(
            "font-size:13px; font-weight:800; color:#8B6B5A; background:transparent;"
        )
        rl.addWidget(self._count_label)
        rl.addSpacing(6)

        self._chips_scroll = QScrollArea()
        self._chips_scroll.setFixedHeight(62)
        self._chips_scroll.setWidgetResizable(True)
        self._chips_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._chips_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._chips_scroll.setStyleSheet(
            "QScrollArea { background:transparent; border:none; }"
            "QScrollBar:horizontal { height:4px; background:#E8D5CC; border-radius:2px; }"
            "QScrollBar::handle:horizontal { background:#C4987A; border-radius:2px; }"
        )
        self._chips_widget = QWidget()
        self._chips_widget.setStyleSheet("background:transparent;")
        self._chips_layout = QHBoxLayout(self._chips_widget)
        self._chips_layout.setContentsMargins(0, 4, 0, 4)
        self._chips_layout.setSpacing(8)
        self._chips_layout.addStretch()
        self._chips_scroll.setWidget(self._chips_widget)
        rl.addWidget(self._chips_scroll)
        rl.addSpacing(10)

        bottom_row = QHBoxLayout(); bottom_row.setSpacing(14)

        self.emergency_btn = QPushButton("\U0001f6a8  Emergency Help")
        self.emergency_btn.setFixedHeight(52)
        self.emergency_btn.setCursor(Qt.PointingHandCursor)
        self.emergency_btn.setStyleSheet("""
            QPushButton { background:transparent; color:#8B3A2E; border:2px solid #8B3A2E;
                          border-radius:14px; font-size:15px; font-weight:900; }
            QPushButton:hover { background:#FDF3EE; }
        """)
        self.emergency_btn.clicked.connect(_stop_all)
        self.emergency_btn.clicked.connect(self.emergency_clicked.emit)

        self.continue_btn = QPushButton("Continue  →")
        self.continue_btn.setFixedHeight(52)
        self.continue_btn.setEnabled(False)
        self.continue_btn.setCursor(Qt.PointingHandCursor)
        self._style_continue(False)
        self.continue_btn.clicked.connect(_stop_all)
        self.continue_btn.clicked.connect(self._emit_continue)

        bottom_row.addWidget(self.emergency_btn, 1)
        bottom_row.addWidget(self.continue_btn, 2)
        rl.addLayout(bottom_row)

        outer.addWidget(right)
        self._body.region_clicked.connect(self._open_popup)

    def _open_popup(self, region_key: str):
        region_vocab = {s[0] for s in BODY_REGION_SYMPTOMS.get(region_key, [])}
        already      = [v for v in self._selected if v in region_vocab]
        popup        = SymptomPopup(region_key, already, self._language, parent=self.window())
        popup.symptoms_confirmed.connect(self._on_symptoms_confirmed)
        popup.exec()

    def _on_symptoms_confirmed(self, region_key: str, vocab_names: List[str]):
        is_kriol        = self._language == "kriol"
        region_symptoms = {s[0]: (s[1], s[2]) for s in BODY_REGION_SYMPTOMS.get(region_key, [])}
        for v in [v for v in list(self._selected) if v in region_symptoms]:
            del self._selected[v]
        for vocab in vocab_names:
            if vocab in region_symptoms:
                label = region_symptoms[vocab][1] if is_kriol else region_symptoms[vocab][0]
                self._selected[vocab] = label
        self._refresh_chips()
        self._body.set_active_regions(self._active_regions())

    def _active_regions(self) -> Set[str]:
        active = set()
        for rk, symptoms in BODY_REGION_SYMPTOMS.items():
            if {s[0] for s in symptoms} & set(self._selected.keys()):
                active.add(rk)
        return active

    def _refresh_chips(self):
        while self._chips_layout.count() > 1:
            item = self._chips_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for vocab, label in self._selected.items():
            chip = SymptomChip(vocab, label)
            chip.removed.connect(self._remove_symptom)
            self._chips_layout.insertWidget(self._chips_layout.count() - 1, chip)
        count = len(self._selected)
        is_kriol = self._language == "kriol"
        if count == 0:
            self._count_label.setText(
                "No sikwan sain jusum yet" if is_kriol else "No symptoms selected yet"
            )
        elif count == 1:
            self._count_label.setText(
                "1 sikwan sain jusum  \u2014  klik moa pat bodi" if is_kriol
                else "1 symptom selected  \u2014  tap more body parts to add"
            )
        else:
            self._count_label.setText(
                f"{count} sikwan sain jusum" if is_kriol else f"{count} symptoms selected"
            )
        self.continue_btn.setEnabled(count > 0)
        self._style_continue(count > 0)

    def _remove_symptom(self, vocab_name: str):
        self._selected.pop(vocab_name, None)
        self._refresh_chips()
        self._body.set_active_regions(self._active_regions())

    def _style_continue(self, enabled: bool):
        if enabled:
            self.continue_btn.setStyleSheet("""
                QPushButton { background:#8B3A2E; color:#FFFFFF; border:none;
                              border-radius:14px; font-size:16px; font-weight:900; }
                QPushButton:hover { background:#6B2A1E; }
            """)
        else:
            self.continue_btn.setStyleSheet("""
                QPushButton { background:#D4B8B0; color:#FFFFFF; border:none;
                              border-radius:14px; font-size:16px; font-weight:900; }
            """)

    def _emit_continue(self):
        if self._selected:
            self.continue_clicked.emit(", ".join(self._selected.keys()))

    def clear_selection(self):
        self._selected.clear()
        self._refresh_chips()
        self._body.set_active_regions(set())

    def play_entry_animations(self):
        """Called by MainWindow after the page becomes visible."""
        audio = "Kriol-bodymap.mp3" if self._language == "kriol" else "English-bodymap.mp3"
        QTimer.singleShot(300, lambda: _play_sequence([audio], on_complete=self._animate_zone_buttons))

    def _animate_zone_buttons(self):
        """Nudge all zone buttons + whole-body button in a staggered bounce."""
        buttons = list(self._zone_btns.values()) + [self._whole_btn]
        for i, btn in enumerate(buttons):
            delay = i * 100
            def _nudge(b=btn):
                orig = b.geometry()
                nudged = orig.translated(0, 8)
                a1 = QPropertyAnimation(b, b"geometry", b)
                a1.setDuration(110)
                a1.setStartValue(orig)
                a1.setEndValue(nudged)
                a1.setEasingCurve(QEasingCurve.OutQuad)
                a2 = QPropertyAnimation(b, b"geometry", b)
                a2.setDuration(220)
                a2.setStartValue(nudged)
                a2.setEndValue(orig)
                a2.setEasingCurve(QEasingCurve.OutBack)
                a1.finished.connect(a2.start)
                a1.start()
                b._nudge_a1 = a1
                b._nudge_a2 = a2
            QTimer.singleShot(delay, _nudge)

    def set_language(self, language: str):
        self._language = language

    def set_strings(self, s: dict):
        self.strings   = s or {}
        is_kriol       = self._language == "kriol"
        self._help_btn.set_kriol(is_kriol)
        self._heading.setText(
            s.get("body_map_title", "Tap where it hurts" if not is_kriol else "Klik we i hati")
        )
        self._subheading.setText(
            s.get("body_map_subtitle",
                  "Select a body part then choose your symptoms"
                  if not is_kriol else "Selektem wan pat bodi, den jusum yu simptom")
        )
        self._hero_title.setText(
            "Show us\nwhere it hurts" if not is_kriol else "Shoim mi\nwe i hati"
        )
        self._hero_tag.setText(
            "Tap a body part,\nthen pick\nyour symptoms"
            if not is_kriol else "Klik wan pat bodi\nden jusum\nyu simptom"
        )
        self.back_btn.setText(s.get("back", "\u2190 Back" if not is_kriol else "\u2190 Bek"))
        self.emergency_btn.setText(
            s.get("emergency", "\U0001f6a8  Emergency Help"
                  if not is_kriol else "\U0001f6a8  Imijensi Elp")
        )
        self.continue_btn.setText(
            s.get("continue", "Continue  \u2192" if not is_kriol else "Kontiniu  \u2192")
        )
        # Zone hint label
        self._zone_hint_lbl.setText("Tapim wan son:" if is_kriol else "Tap a zone:")
        # Zone buttons
        for key, zbtn in self._zone_btns.items():
            info = BODY_REGION_LABELS[key]
            label = info[1] if is_kriol else info[0]
            zbtn.setText(f"{info[2]}  {label}")
        # Whole body button
        self._whole_btn.setText(
            "\U0001f321  Ol bodi / Jeneral" if is_kriol else "\U0001f321  Whole body / General"
        )
        # Refresh count label with correct language
        self._refresh_chips()
