from __future__ import annotations

"""
SACA Results Page
=================
Use this file as: src/ui/pages/results_page.py

This UI follows your Figma result screens:
- Green: rest at home
- Orange: contact clinic soon
- Red: emergency help now

The result is driven by NLP + ML result_data from triage_orchestrator.py.
It does NOT use the old pain-scale rule 1-3 / 4-7 / 8-10.
"""

from typing import Dict, List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class InfoCard(QFrame):
    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(245)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 22, 24, 20)
        self.layout.setSpacing(14)

        self.title = QLabel("")
        self.title.setWordWrap(True)
        self.title.setStyleSheet(
            "font-size: 24px; font-weight: 900; color: #1C1C1C; background: transparent;"
        )
        self.layout.addWidget(self.title)

        self.items_layout = QVBoxLayout()
        self.items_layout.setSpacing(12)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addLayout(self.items_layout)
        self.layout.addStretch()

        self.setStyleSheet(
            """
            QFrame {
                background: rgba(255, 255, 255, 0.94);
                border: none;
                border-radius: 16px;
            }
            """
        )

    def set_title(self, text: str):
        self.title.setText(text)

    def clear(self):
        while self.items_layout.count():
            item = self.items_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def add_item(self, widget: QWidget):
        self.items_layout.addWidget(widget)


class SoftRow(QFrame):
    def __init__(
        self,
        text: str,
        bg: str,
        text_color: str = "#1C1C1C",
        icon: str | None = None,
        subtitle: str | None = None,
        number: str | None = None,
        border: str | None = None,
        compact: bool = False,
    ):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(58 if compact else 66)

        border_css = f"border: 1.5px solid {border};" if border else "border: none;"
        self.setStyleSheet(
            f"""
            QFrame {{
                background: {bg};
                {border_css}
                border-radius: 12px;
            }}
            """
        )

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 10, 16, 10)
        lay.setSpacing(12)

        if number is not None:
            badge = QLabel(number)
            badge.setAlignment(Qt.AlignCenter)
            badge.setFixedSize(36, 36)
            badge.setStyleSheet(
                """
                QLabel {
                    background: #C00000;
                    color: white;
                    border-radius: 18px;
                    font-size: 16px;
                    font-weight: 900;
                }
                """
            )
            lay.addWidget(badge, 0, Qt.AlignVCenter)
        elif icon:
            icon_label = QLabel(icon)
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setFixedWidth(44)
            icon_label.setStyleSheet(
                "font-size: 28px; font-weight: 900; background: transparent; border: none;"
            )
            lay.addWidget(icon_label, 0, Qt.AlignVCenter)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        text_col.setContentsMargins(0, 0, 0, 0)

        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet(
            f"font-size: {15 if compact else 18}px; font-weight: 900; color: {text_color}; background: transparent; border: none;"
        )
        text_col.addWidget(label)

        if subtitle:
            sub = QLabel(subtitle)
            sub.setWordWrap(True)
            sub.setStyleSheet(
                "font-size: 13px; font-weight: 800; color: #8B3A2E; background: transparent; border: none;"
            )
            text_col.addWidget(sub)

        lay.addLayout(text_col, 1)


class ConfidencePill(QLabel):
    def __init__(self, text: str):
        super().__init__(text)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(38)
        self.setMinimumWidth(160)
        self.setStyleSheet(
            """
            QLabel {
                background: #F2E1C9;
                color: #8B3A2E;
                border: none;
                border-radius: 19px;
                font-size: 13px;
                font-weight: 900;
                padding: 0px 18px;
            }
            """
        )


class ResultsPage(QWidget):
    back_clicked = Signal()
    home_clicked = Signal()
    emergency_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.strings: Dict = {}
        self.full_data: Dict = {}
        self.result_data: Dict = {}
        self.nlp_data: Dict = {}
        self.answers: Dict = {}

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addStretch()

        self.content = QWidget()
        self.content.setMaximumWidth(980)
        self.content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        outer.addWidget(self.content)
        outer.addStretch()

        self.root = QVBoxLayout(self.content)
        self.root.setContentsMargins(26, 18, 26, 18)
        self.root.setSpacing(16)
        self.root.setAlignment(Qt.AlignTop)

        # Header banner
        self.header = QFrame()
        self.header.setFixedHeight(92)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(28, 10, 28, 10)

        self.header_label = QLabel("")
        self.header_label.setAlignment(Qt.AlignCenter)
        self.header_label.setWordWrap(True)
        self.header_label.setStyleSheet(
            "font-size: 34px; font-weight: 900; color: white; background: transparent; border: none;"
        )
        header_layout.addWidget(self.header_label)
        self.root.addWidget(self.header)

        # Hero card
        self.hero = QFrame()
        self.hero.setFixedHeight(300)
        hero_layout = QVBoxLayout(self.hero)
        hero_layout.setContentsMargins(38, 30, 38, 30)
        hero_layout.setSpacing(18)
        hero_layout.setAlignment(Qt.AlignCenter)

        self.hero_icon = QLabel("")
        self.hero_icon.setAlignment(Qt.AlignCenter)
        self.hero_icon.setFixedSize(112, 112)
        self.hero_icon.setStyleSheet("background: transparent; border: none;")
        hero_layout.addWidget(self.hero_icon, 0, Qt.AlignHCenter)

        self.hero_title = QLabel("")
        self.hero_title.setAlignment(Qt.AlignCenter)
        self.hero_title.setWordWrap(True)
        self.hero_title.setStyleSheet(
            "font-size: 34px; font-weight: 900; color: #1C1C1C; background: transparent; border: none;"
        )
        hero_layout.addWidget(self.hero_title)

        self.hero_button = QPushButton("")
        self.hero_button.setCursor(Qt.PointingHandCursor)
        self.hero_button.setFixedHeight(92)
        self.hero_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.hero_button.clicked.connect(self._hero_clicked)
        hero_layout.addWidget(self.hero_button)
        self.root.addWidget(self.hero)

        # Cards row
        self.cards_row = QHBoxLayout()
        self.cards_row.setSpacing(24)
        self.left_card = InfoCard()
        self.right_card = InfoCard()
        self.cards_row.addWidget(self.left_card)
        self.cards_row.addWidget(self.right_card)
        self.root.addLayout(self.cards_row)

        # Warning strip
        self.warning = QFrame()
        self.warning.setFixedHeight(64)
        warning_layout = QHBoxLayout(self.warning)
        warning_layout.setContentsMargins(22, 8, 22, 8)

        self.warning_label = QLabel("")
        self.warning_label.setAlignment(Qt.AlignCenter)
        self.warning_label.setWordWrap(True)
        self.warning_label.setStyleSheet(
            "font-size: 18px; font-weight: 900; color: #1C1C1C; background: transparent; border: none;"
        )
        warning_layout.addWidget(self.warning_label)
        self.root.addWidget(self.warning)

        # Bottom buttons
        self.bottom_row = QHBoxLayout()
        self.bottom_row.setSpacing(18)
        self.start_btn = QPushButton("↻  Start again")
        self.change_btn = QPushButton("✎  Change answers")
        self.emergency_btn = QPushButton("ⓘ  Emergency Help")
        for btn in (self.start_btn, self.change_btn, self.emergency_btn):
            btn.setFixedHeight(60)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.start_btn.clicked.connect(self.home_clicked.emit)
        self.change_btn.clicked.connect(self.back_clicked.emit)
        self.emergency_btn.clicked.connect(self.emergency_clicked.emit)
        self.bottom_row.addWidget(self.start_btn)
        self.bottom_row.addWidget(self.change_btn)
        self.bottom_row.addWidget(self.emergency_btn)
        self.root.addLayout(self.bottom_row)

        self._render()

    # ------------------------------------------------------------------
    # Public API used by MainWindow
    # ------------------------------------------------------------------
    def set_strings(self, strings: Dict):
        self.strings = strings or {}
        self._render()

    def set_result(self, result_data: Dict):
        self.full_data = result_data or {}
        self.result_data = self.full_data.get("result", self.full_data or {})
        self.nlp_data = self.full_data.get("nlp", {}) or {}
        self.answers = self.full_data.get("answers", {}) or {}
        self._render()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _is_kriol(self) -> bool:
        if str(self.nlp_data.get("ui_language", "")).lower() in {"kriol", "kr"}:
            return True
        return str(self.strings.get("back", "Back")).strip().lower() == "bek"

    def _t(self, en: str, kriol: str) -> str:
        return kriol if self._is_kriol() else en

    def _mode(self) -> str:
        triage = str(self.result_data.get("triage_level", "mild")).lower().strip()
        if triage == "critical":
            return "red"
        if triage == "moderate":
            return "orange"
        return "green"

    def _content_dict(self) -> Dict:
        return self.result_data.get("result_content", {}) or {}

    def _detected_symptoms(self) -> List[Dict[str, str]]:
        symptoms = self.result_data.get("detected_symptoms") or self.nlp_data.get("display_symptoms") or []
        if isinstance(symptoms, list):
            return [s for s in symptoms if isinstance(s, dict)]
        return []

    def _confidence_text(self) -> str:
        label = self.result_data.get("confidence_label") or "Medium"
        return self._t(f"Confidence: {label}", f"Konfidens: {label}")

    def _palettes(self) -> Dict[str, Dict[str, str]]:
        return {
            "green": {
                "header": "#1CA34A",
                "main": "#1A8F3F",
                "border": "#1CA34A",
                "item": "#D8F4DF",
                "warning": "#D9A514",
                "warning_text": "#1C1C1C",
                "soft": "#FFFFFF",
                "outline": "#1C1C1C",
            },
            "orange": {
                "header": "#C65D2E",
                "main": "#B64C35",
                "border": "#C65D2E",
                "item": "#FFF3ED",
                "warning": "#C65D2E",
                "warning_text": "#FFFFFF",
                "soft": "#FFFFFF",
                "outline": "#C65D2E",
            },
            "red": {
                "header": "#C00000",
                "main": "#A90000",
                "border": "#C00000",
                "item": "#FFE0E0",
                "warning": "#C00000",
                "warning_text": "#FFFFFF",
                "soft": "#FFFFFF",
                "outline": "#C00000",
            },
        }

    def _clear_cards(self):
        self.left_card.clear()
        self.right_card.clear()

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------
    def _render(self):
        mode = self._mode()
        p = self._palettes()[mode]
        content = self._content_dict()

        self.setStyleSheet("background: transparent;")
        self.header.setStyleSheet(
            f"QFrame {{ background: {p['header']}; border: none; border-radius: 16px; }}"
        )
        self.hero.setStyleSheet(
            f"QFrame {{ background: rgba(255, 255, 255, 0.94); border: 3px solid {p['border']}; border-radius: 16px; }}"
        )
        self.warning.setStyleSheet(
            f"QFrame {{ background: {p['warning']}; border: none; border-radius: 14px; }}"
        )
        self.warning_label.setStyleSheet(
            f"font-size: 18px; font-weight: 900; color: {p['warning_text']}; background: transparent; border: none;"
        )

        self.left_card.setStyleSheet(
            "QFrame { background: rgba(255,255,255,0.94); border: none; border-radius: 16px; }"
        )
        self.right_card.setStyleSheet(
            "QFrame { background: rgba(255,255,255,0.94); border: none; border-radius: 16px; }"
        )

        self.start_btn.setText(self._t("↻  Start again", "↻  Stat agen"))
        self.change_btn.setText(self._t("✎  Change answers", "✎  Jeinj ansa"))
        self.emergency_btn.setText(self._t("ⓘ  Emergency Help", "ⓘ  Imijensi Elp"))
        self._style_bottom_buttons(p)

        if mode == "green":
            self._render_green(p, content)
        elif mode == "orange":
            self._render_orange(p, content)
        else:
            self._render_red(p, content)

    def _render_green(self, p: Dict[str, str], content: Dict):
        self._clear_cards()
        self.header_label.setText(content.get("header") or self._t("You can rest at home for now", "Yu ken rest langa haus fo nau"))

        self.hero_icon.setText("▱")
        self.hero_icon.setStyleSheet(
            f"""
            QLabel {{
                background: {p['header']};
                color: white;
                border-radius: 56px;
                font-size: 58px;
                font-weight: 900;
                border: none;
            }}
            """
        )
        self.hero_title.show()
        self.hero_title.setText(content.get("main_action") or self._t("You need to take a rest", "Yu nid fo rest"))
        self.hero_button.setText(self._t("I understand", "Mi save"))
        self.hero_button.setStyleSheet(self._hero_button_css(p['main'], font_size=26))

        self.left_card.set_title(content.get("left_title") or self._t("What to do:", "Wanim fo du:"))
        self.right_card.set_title(content.get("right_title") or self._t("Why this result:", "Wai dis result:"))

        steps = content.get("what_to_do") or [
            self._t("Rest", "Rest"),
            self._t("Drink water", "Dringgim woda"),
            self._t("Monitor symptoms", "Lukluk simptom"),
        ]
        icons = ["🛏️", "💧", "👀"]
        for idx, step in enumerate(steps[:3]):
            self.left_card.add_item(SoftRow(step, p['item'], icon=icons[idx] if idx < len(icons) else None))

        why = content.get("why") or self._t("Based on your symptoms, this looks mild", "Bikos langa yu simptom, diswan luk liklik")
        self.right_card.add_item(SoftRow(why, p['item'], compact=True))
        pill = ConfidencePill(self._confidence_text())
        self.right_card.add_item(pill)

        self.warning_label.setText(content.get("warning") or self._t("ℹ If you get worse, call the clinic.", "ℹ If yu kam nogud, kolim klinik."))

    def _render_orange(self, p: Dict[str, str], content: Dict):
        self._clear_cards()
        self.header_label.setText(content.get("header") or self._t("Please contact the clinic soon", "Plis kolim klinik sun"))

        self.hero_icon.hide()
        self.hero_title.hide()
        self.hero_button.setText(content.get("main_action") or self._t("☎  CALL CLINIC\nNOW", "☎  KOL KLINIK\nNAU"))
        self.hero_button.setStyleSheet(self._hero_button_css(p['main'], font_size=46))

        self.left_card.set_title(content.get("left_title") or self._t("Your symptoms:", "Yu simptom:"))
        self.right_card.set_title(content.get("right_title") or self._t("What to do next:", "Wanim fo du nekis:"))

        symptoms = self._detected_symptoms()[:3]
        if not symptoms:
            symptoms = [{"label": self._t("Symptoms detected", "Simptom bin faindim"), "kriol_label": ""}]
        for symptom in symptoms:
            label = symptom.get("label") or symptom.get("display") or "Symptom"
            sub = symptom.get("kriol_label") if not self._is_kriol() else symptom.get("label")
            self.left_card.add_item(SoftRow(label, p['item'], subtitle=sub, border=p['border']))

        steps = content.get("what_to_do") or [
            self._t("Call clinic today or tomorrow", "Kol klinik tidei o tumoro"),
            self._t("Rest while waiting", "Rest wen yu weit"),
            self._t("Seek help faster if symptoms get worse", "Garr elp kwik if simptom kam nogud"),
        ]
        icons = ["☎", "🛏️", "⚠"]
        for idx, step in enumerate(steps[:3]):
            self.right_card.add_item(SoftRow(step, "transparent", icon=icons[idx] if idx < len(icons) else None, compact=True))

        why = content.get("why") or self._t("Your symptoms may need health worker review.", "Yu simptom mait nid helt wokabala lukluk.")
        self.right_card.add_item(SoftRow(why, "#FFF1DE", text_color="#8B3A2E", compact=True))

        pill = ConfidencePill(self._confidence_text())
        self.left_card.add_item(pill)
        self.warning_label.setText(content.get("warning") or self._t(
            "⚠ If breathing becomes hard, chest pain starts, or you collapse, use Emergency Help.",
            "⚠ If brith kam had, jes pein stat, o yu poldaun, yusim Imijensi Elp.",
        ))

    def _render_red(self, p: Dict[str, str], content: Dict):
        self._clear_cards()
        self.header_label.setText(content.get("header") or self._t("Get emergency help now", "Garr imijensi elp nau"))

        self.hero_icon.hide()
        self.hero_title.hide()
        self.hero_button.setText(content.get("main_action") or self._t("☎\nCALL 000 NOW", "☎\nKOL 000 NAU"))
        self.hero_button.setStyleSheet(self._hero_button_css(p['main'], font_size=50))

        self.left_card.set_title(content.get("left_title") or self._t("What to do:", "Wanim fo du:"))
        self.right_card.set_title(content.get("right_title") or self._t("Why this result:", "Wai dis result:"))

        steps = content.get("what_to_do") or [
            self._t("Call 000", "Kol 000"),
            self._t("Do not drive yourself", "No draib yuself"),
            self._t("Ask someone nearby for help", "Askim sambodi neba fo help"),
        ]
        for idx, step in enumerate(steps[:3], start=1):
            self.left_card.add_item(SoftRow(step, "transparent", number=str(idx), compact=True))

        symptoms = self._detected_symptoms()[:4]
        if symptoms:
            box = QFrame()
            box.setStyleSheet("QFrame { background: #FFE0E0; border: none; border-radius: 12px; }")
            box_layout = QVBoxLayout(box)
            box_layout.setContentsMargins(18, 16, 18, 16)
            box_layout.setSpacing(8)
            title = QLabel(self._t("Red-flag symptoms:", "Denja simptom:"))
            title.setStyleSheet("font-size: 16px; font-weight: 900; color: #C00000; background: transparent; border: none;")
            box_layout.addWidget(title)
            for symptom in symptoms:
                label = symptom.get("label") or symptom.get("display") or "Symptom"
                row = QLabel(f"• {label}")
                row.setStyleSheet("font-size: 15px; font-weight: 700; color: #1C1C1C; background: transparent; border: none;")
                box_layout.addWidget(row)
            self.right_card.add_item(box)
        else:
            why = content.get("why") or self._t("Red-flag symptoms detected.", "Bigwan denja simptom bin faindim.")
            self.right_card.add_item(SoftRow(why, "#FFE0E0", text_color="#C00000", compact=True))

        self.warning_label.setText(content.get("warning") or self._t("⚠ This may be serious. Get help now.", "⚠ Diswan mait bigwan. Garr elp nau."))

    # ------------------------------------------------------------------
    # Styles/actions
    # ------------------------------------------------------------------
    def _hero_button_css(self, color: str, font_size: int) -> str:
        return f"""
            QPushButton {{
                background: {color};
                color: white;
                border: none;
                border-radius: 14px;
                font-size: {font_size}px;
                font-weight: 900;
                padding: 12px 18px;
                text-align: center;
            }}
            QPushButton:hover {{
                background: {color};
            }}
            QPushButton:pressed {{
                background: {color};
            }}
        """

    def _style_bottom_buttons(self, p: Dict[str, str]):
        outline = "#1C1C1C"
        self.start_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: white;
                color: #1C1C1C;
                border: 2px solid {outline};
                border-radius: 14px;
                font-size: 16px;
                font-weight: 900;
            }}
            QPushButton:hover {{ background: #F7F7F7; }}
            """
        )
        self.change_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: white;
                color: #1C1C1C;
                border: 2px solid {outline};
                border-radius: 14px;
                font-size: 16px;
                font-weight: 900;
            }}
            QPushButton:hover {{ background: #F7F7F7; }}
            """
        )
        self.emergency_btn.setStyleSheet(
            """
            QPushButton {
                background: #B10000;
                color: white;
                border: none;
                border-radius: 14px;
                font-size: 16px;
                font-weight: 900;
            }
            QPushButton:hover { background: #970000; }
            """
        )

    def _hero_clicked(self):
        mode = self._mode()
        if mode in {"orange", "red"}:
            self.emergency_clicked.emit()
