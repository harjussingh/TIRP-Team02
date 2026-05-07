from __future__ import annotations

from typing import Dict, List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class ResultCard(QFrame):
    def __init__(self, title: str = ""):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.outer_layout = QVBoxLayout(self)
        self.outer_layout.setContentsMargins(26, 22, 26, 22)
        self.outer_layout.setSpacing(16)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(
            "font-size: 22px; font-weight: 900; color: #5B433B; background: transparent;"
        )
        self.outer_layout.addWidget(self.title_label)

        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(14)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.outer_layout.addLayout(self.content_layout)
        self.outer_layout.addStretch()

    def set_title(self, title: str):
        self.title_label.setText(title)

    def clear_items(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def add_item(self, widget: QWidget):
        self.content_layout.addWidget(widget)


class BulletRow(QFrame):
    def __init__(self, text: str, bg: str, text_color: str, leading: str | None = None):
        super().__init__()
        self.setMinimumHeight(72)
        self.setStyleSheet(f"QFrame {{ background: {bg}; border: none; border-radius: 16px; }}")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 12, 18, 12)
        lay.setSpacing(14)

        if leading is not None:
            lead = QLabel(leading)
            lead.setAlignment(Qt.AlignCenter)
            lead.setFixedSize(42, 42)
            lead.setStyleSheet(
                """
                QLabel {
                    background: #D53C31;
                    color: white;
                    border-radius: 21px;
                    font-size: 18px;
                    font-weight: 900;
                }
                """
            )
            lay.addWidget(lead)

        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet(
            f"font-size: 18px; font-weight: 800; color: {text_color}; background: transparent;"
        )
        lay.addWidget(label, 1)


class ResultsPage(QWidget):
    back_clicked = Signal()
    home_clicked = Signal()
    emergency_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.strings: Dict = {}
        self.full_data: Dict = {}
        self.result_data: Dict = {}
        self.answers: Dict = {}
        self.mode = "green"

        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(34, 22, 34, 26)
        self.root.setSpacing(18)

        # Top banner
        self.top_banner = QFrame()
        self.top_banner.setStyleSheet("QFrame { border: none; border-radius: 24px; }")
        top_lay = QHBoxLayout(self.top_banner)
        top_lay.setContentsMargins(28, 18, 28, 18)
        top_lay.setSpacing(10)

        self.top_title = QLabel()
        self.top_title.setWordWrap(True)
        self.top_title.setStyleSheet(
            "font-size: 34px; font-weight: 900; color: white; background: transparent;"
        )
        top_lay.addWidget(self.top_title, 1)
        self.root.addWidget(self.top_banner)

        # Hero wrapper
        self.hero_wrapper = QFrame()
        self.hero_wrapper.setStyleSheet("QFrame { background: #F5F5F5; border-radius: 28px; }")
        hero_outer = QVBoxLayout(self.hero_wrapper)
        hero_outer.setContentsMargins(38, 34, 38, 34)
        hero_outer.setSpacing(22)

        self.hero_icon_tile = QLabel()
        self.hero_icon_tile.setAlignment(Qt.AlignCenter)
        self.hero_icon_tile.setFixedSize(170, 170)
        self.hero_icon_tile.hide()

        self.hero_button = QPushButton()
        self.hero_button.setCursor(Qt.PointingHandCursor)
        self.hero_button.clicked.connect(self._hero_action)
        self.hero_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        hero_outer.addWidget(self.hero_icon_tile, 0, Qt.AlignHCenter)
        hero_outer.addWidget(self.hero_button)
        self.root.addWidget(self.hero_wrapper)

        # Message strip
        self.message_strip = QFrame()
        self.message_strip.setStyleSheet("QFrame { border-radius: 22px; }")
        strip_lay = QHBoxLayout(self.message_strip)
        strip_lay.setContentsMargins(24, 20, 24, 20)
        strip_lay.setSpacing(12)

        self.message_label = QLabel()
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet(
            "font-size: 20px; font-weight: 800; color: #8B431F; background: transparent;"
        )
        strip_lay.addWidget(self.message_label)
        self.root.addWidget(self.message_strip)

        # Mid cards
        self.cards_row = QHBoxLayout()
        self.cards_row.setSpacing(22)

        self.left_card = ResultCard()
        self.right_card = ResultCard()
        self.cards_row.addWidget(self.left_card, 1)
        self.cards_row.addWidget(self.right_card, 1)
        self.root.addLayout(self.cards_row)

        # Bottom buttons
        self.buttons_row = QHBoxLayout()
        self.buttons_row.setSpacing(18)

        self.start_again_btn = QPushButton()
        self.change_answers_btn = QPushButton()
        self.emergency_btn = QPushButton()

        for btn in (self.start_again_btn, self.change_answers_btn, self.emergency_btn):
            btn.setMinimumHeight(68)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setCursor(Qt.PointingHandCursor)

        self.start_again_btn.clicked.connect(self.home_clicked.emit)
        self.change_answers_btn.clicked.connect(self.back_clicked.emit)
        self.emergency_btn.clicked.connect(self.emergency_clicked.emit)

        self.buttons_row.addWidget(self.start_again_btn)
        self.buttons_row.addWidget(self.change_answers_btn)
        self.buttons_row.addWidget(self.emergency_btn)
        self.root.addLayout(self.buttons_row)

        self._apply_ui()

    # ------------------------------ public ------------------------------
    def set_strings(self, strings: Dict):
        self.strings = strings or {}
        self._apply_ui()

    def set_result(self, result_data: Dict):
        self.full_data = result_data or {}
        self.result_data = self.full_data.get("result", self.full_data or {})
        self.answers = self.full_data.get("answers", self.result_data.get("answers", {})) or {}
        self._apply_ui()

    # ------------------------------ language ------------------------------
    def _is_kriol(self) -> bool:
        return str(self.strings.get("back", "Back")).strip().lower() == "bek"

    def _tr(self, en: str, kr: str) -> str:
        return kr if self._is_kriol() else en

    # ------------------------------ data ------------------------------
    def _pain_scale(self) -> int:
        for src in (self.answers, self.result_data, self.full_data):
            if isinstance(src, dict) and src.get("pain_scale") is not None:
                try:
                    return max(1, min(10, int(src.get("pain_scale"))))
                except Exception:
                    pass
        return 3

    def _mode(self) -> str:
        triage = str(self.result_data.get("triage_level") or "mild").lower().strip()
        ats = int(self.result_data.get("ats_level") or 5)
        pain = self._pain_scale()

        if triage == "critical" or ats <= 2 or pain >= 8:
            return "red"
        if triage in {"moderate", "medium", "high"} or ats == 3 or pain >= 4:
            return "orange"
        return "green"

    def _condition_text(self) -> str:
        disease = str(self.result_data.get("predicted_disease") or "common cold").replace("_", " ").strip().lower()

        if self.mode == "green":
            if "flu" in disease:
                return self._tr("A mild flu", "Liklik flu")
            return self._tr("A mild cold", "Liklik kol")

        if self._is_kriol():
            kriol_map = {
                "common cold": "Kol",
                "flu": "Flu",
                "viral infection": "Vairas infekshan",
                "infection": "Infekshan",
                "pneumonia": "Nyumonia",
            }
            return kriol_map.get(disease, disease.title())

        return disease.title()

    def _symptoms(self) -> List[str]:
        raw = self.full_data.get("nlp", {}).get("symptoms", []) or []
        if not raw:
            raw = ["fever", "tired"]

        en = {
            "headache": "Head hurting",
            "fever": "Body hot",
            "weak": "Very tired",
            "tired": "Very tired",
            "body_pain": "Body pain",
            "pain": "Body pain",
            "cough": "Cough",
            "sore_throat": "Sore throat",
            "stomach_pain": "Stomach pain",
            "vomiting": "Vomiting",
            "dizzy": "Dizzy",
            "breathing_problem": "Hard to breathe",
            "chest_pain": "Chest pain",
            "rash": "Skin problem",
        }
        kr = {
            "headache": "Hed sik",
            "fever": "Bodi hot",
            "weak": "Brabli tait",
            "tired": "Brabli tait",
            "body_pain": "Bodi pein",
            "pain": "Bodi pein",
            "cough": "Kof",
            "sore_throat": "Troat pein",
            "stomach_pain": "Beli pein",
            "vomiting": "Pukpuk",
            "dizzy": "Diji",
            "breathing_problem": "Had fo brith",
            "chest_pain": "Jes pein",
            "rash": "Skin nogud",
        }
        mapping = kr if self._is_kriol() else en
        return [mapping.get(str(item).lower(), str(item).replace("_", " ").title()) for item in raw]

    # ------------------------------ styles ------------------------------
    def _palette(self) -> Dict[str, str]:
        if self.mode == "green":
            return {
                "header": "#4FA74D",
                "hero": "#49984A",
                "outline": "#4FA74D",
                "page": "transparent",
                "card": "#F7F7F7",
                "item": "#D9EBD7",
                "notice": "#F2E3CB",
                "text": "#2D1B14",
                "panel_border": "#9F6434",
            }
        if self.mode == "orange":
            return {
                "header": "#E16828",
                "hero": "#D65E22",
                "outline": "#E16828",
                "page": "transparent",
                "card": "#F7F7F7",
                "item": "#F0DFC7",
                "notice": "#F2E3CB",
                "text": "#2D1B14",
                "panel_border": "#9F6434",
            }
        return {
            "header": "#D53D33",
            "hero": "#C92F28",
            "outline": "#D53D33",
            "page": "transparent",
            "card": "#F7F7F7",
            "item": "#F0DFC7",
            "notice": "#F7ECEA",
            "text": "#2D1B14",
            "panel_border": "#9F6434",
        }

    # ------------------------------ render ------------------------------
    def _apply_ui(self):
        self.mode = self._mode()
        p = self._palette()

        self.setStyleSheet("background: transparent;")

        self.top_banner.setStyleSheet(
            f"QFrame {{ background: {p['header']}; border: none; border-radius: 24px; }}"
        )
        self.hero_wrapper.setStyleSheet(
            f"QFrame {{ background: {p['card']}; border: 2px solid {p['outline']}; border-radius: 28px; }}"
        )
        self.message_strip.setStyleSheet(
            f"QFrame {{ background: {p['notice']}; border: 2px solid {p['outline']}; border-radius: 22px; }}"
        )

        self.left_card.setStyleSheet(
            f"QFrame {{ background: {p['card']}; border: 2px solid {p['panel_border']}; border-radius: 22px; }}"
        )
        self.right_card.setStyleSheet(
            f"QFrame {{ background: {p['card']}; border: 2px solid {p['panel_border']}; border-radius: 22px; }}"
        )

        self.start_again_btn.setText(self._tr("Start again", "Stat agen"))
        self.change_answers_btn.setText(self._tr("Change answers", "Jeinj ansa"))
        self.emergency_btn.setText(self._tr("Emergency Help", "Imijensi Elp"))

        self.start_again_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: white;
                color: {p['outline']};
                border: 2px solid {p['outline']};
                border-radius: 18px;
                font-size: 18px;
                font-weight: 900;
            }}
            """
        )
        self.change_answers_btn.setStyleSheet(
            """
            QPushButton {
                background: #EFEFEF;
                color: #6B5349;
                border: 2px solid #D7D7D7;
                border-radius: 18px;
                font-size: 18px;
                font-weight: 900;
            }
            """
        )
        self.emergency_btn.setStyleSheet(
            """
            QPushButton {
                background: #F22929;
                color: white;
                border: none;
                border-radius: 18px;
                font-size: 18px;
                font-weight: 900;
            }
            """
        )

        if self.mode == "green":
            self.top_title.setText(self._tr("You can rest at home for now", "Yu ken rest langa haus fo nau"))
            self.hero_icon_tile.show()
            self.hero_icon_tile.setText("🛏️")
            self.hero_icon_tile.setStyleSheet(
                """
                QLabel {
                    background: #B7D1B0;
                    color: #2B2B2B;
                    border: none;
                    border-radius: 22px;
                    font-size: 72px;
                    font-weight: 900;
                }
                """
            )
            self.hero_button.setMinimumHeight(110)
            self.hero_button.setText(self._tr("You need to take a rest", "Yu nid fo rest"))
            self.hero_button.setStyleSheet(
                f"""
                QPushButton {{
                    background: {p['hero']};
                    color: white;
                    border: none;
                    border-radius: 24px;
                    font-size: 30px;
                    font-weight: 900;
                    padding: 18px 20px;
                }}
                """
            )
            self.message_label.setText(
                self._tr(
                    "If you get worse, come back or call the clinic.",
                    "If yu kam moa nogud, kambek o kolim klinik.",
                )
            )
            self.left_card.set_title(self._tr("What to do:", "Wanim fo du:"))
            self.right_card.set_title(self._tr("What it might be:", "Wanim mait bi:"))
        elif self.mode == "orange":
            self.top_title.setText(self._tr("Please see a doctor soon", "Plis lukim dokta sun"))
            self.hero_icon_tile.hide()
            self.hero_button.setMinimumHeight(210)
            self.hero_button.setText(self._tr("📞  CALL CLINIC\nNOW", "📞  KOL KLINIK\nNAU"))
            self.hero_button.setStyleSheet(
                f"""
                QPushButton {{
                    background: {p['hero']};
                    color: white;
                    border: none;
                    border-radius: 28px;
                    font-size: 50px;
                    font-weight: 900;
                    padding: 18px 20px;
                }}
                """
            )
            self.message_label.setText(
                self._tr(
                    "Call your health worker or the clinic today or tomorrow.",
                    "Kolim helt wokabala o klinik tidei o tumoro.",
                )
            )
            self.left_card.set_title(self._tr("Your symptoms:", "Yu simptom:"))
            self.right_card.set_title(self._tr("What it might be:", "Wanim mait bi:"))
        else:
            self.top_title.setText(self._tr("Get emergency help now", "Garr imijensi elp nau"))
            self.hero_icon_tile.hide()
            self.hero_button.setMinimumHeight(240)
            self.hero_button.setText(self._tr("🚑\nCALL 000\nNOW", "🚑\nKOL 000\nNAU"))
            self.hero_button.setStyleSheet(
                f"""
                QPushButton {{
                    background: {p['hero']};
                    color: white;
                    border: none;
                    border-radius: 28px;
                    font-size: 56px;
                    font-weight: 900;
                    padding: 18px 20px;
                }}
                """
            )
            self.message_label.setText(
                self._tr(
                    "Do not drive. Ask someone nearby to help you.",
                    "No draib. Askim sambodi neba fo helpim yu.",
                )
            )
            self.left_card.set_title(self._tr("What to do:", "Wanim fo du:"))
            self.right_card.set_title(self._tr("Why?", "Wai?"))

        self._populate_cards(p)

    def _populate_cards(self, palette: Dict[str, str]):
        self.left_card.clear_items()
        self.right_card.clear_items()
        symptoms = self._symptoms()
        condition = self._condition_text()

        if self.mode == "green":
            self.left_card.add_item(BulletRow(self._tr("Rest", "Rest"), palette['item'], palette['text'], "🛏️"))
            self.left_card.add_item(BulletRow(self._tr("Drink water", "Dringgim woda"), palette['item'], palette['text'], "💧"))
            self.right_card.add_item(BulletRow(condition, palette['item'], palette['text']))
        elif self.mode == "orange":
            for symptom in symptoms[:3]:
                self.left_card.add_item(BulletRow(symptom, palette['item'], palette['text']))
            self.right_card.add_item(BulletRow(condition, palette['item'], palette['text']))
        else:
            self.left_card.add_item(BulletRow(self._tr("Call 000", "Kol 000"), palette['item'], palette['text'], "1"))
            self.left_card.add_item(BulletRow(self._tr("Go to hospital", "Go langa hospital"), palette['item'], palette['text'], "2"))
            self.right_card.add_item(
                BulletRow(
                    self._tr(
                        f"This looks like a serious infection.",
                        f"Diswan luk laik bigwan siknis.",
                    ),
                    palette['item'],
                    palette['text'],
                )
            )

    # ------------------------------ actions ------------------------------
    def _hero_action(self):
        if self.mode in {"orange", "red"}:
            self.emergency_clicked.emit()

