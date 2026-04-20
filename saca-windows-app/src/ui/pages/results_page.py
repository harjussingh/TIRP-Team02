from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QFrame, QGridLayout, QScrollArea
)
from src.ui.widgets.disease_card import DiseaseCard
import re


class ResultsPage(QWidget):
    home_clicked = Signal()
    emergency_clicked = Signal()
    back_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.strings = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(40, 30, 40, 30)
        root.setSpacing(18)

        self.title_label = QLabel("Result")
        self.title_label.setObjectName("pageTitle")

        self.summary_card = QFrame()
        self.summary_card.setObjectName("contentCard")
        summary_layout = QVBoxLayout(self.summary_card)
        summary_layout.setContentsMargins(20, 20, 20, 20)
        summary_layout.setSpacing(10)

        self.original_label = QLabel("")
        self.original_label.setObjectName("cardBody")
        self.original_label.setWordWrap(True)

        self.english_label = QLabel("")
        self.english_label.setObjectName("cardBody")
        self.english_label.setWordWrap(True)

        self.symptoms_label = QLabel("")
        self.symptoms_label.setObjectName("cardBody")
        self.symptoms_label.setWordWrap(True)

        summary_layout.addWidget(self.original_label)
        summary_layout.addWidget(self.english_label)
        summary_layout.addWidget(self.symptoms_label)

        self.conditions_card = QFrame()
        self.conditions_card.setObjectName("contentCard")
        conditions_layout = QVBoxLayout(self.conditions_card)
        conditions_layout.setContentsMargins(20, 20, 20, 20)

        self.cond_title = QLabel("Related conditions")
        self.cond_title.setObjectName("cardTitle")

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setMinimumHeight(260)

        self.cards_container = QWidget()
        self.cards_grid = QGridLayout(self.cards_container)
        self.cards_grid.setSpacing(16)

        self.scroll.setWidget(self.cards_container)

        conditions_layout.addWidget(self.cond_title)
        conditions_layout.addWidget(self.scroll)

        self.action_card = QFrame()
        self.action_card.setObjectName("actionCard")
        action_layout = QVBoxLayout(self.action_card)
        action_layout.setContentsMargins(20, 20, 20, 20)
        action_layout.setSpacing(12)

        self.level_label = QLabel("")
        self.level_label.setObjectName("resultLevel")

        self.pain_label = QLabel("")
        self.pain_label.setObjectName("cardBody")

        self.advice_label = QLabel("")
        self.advice_label.setObjectName("resultAdvice")
        self.advice_label.setWordWrap(True)

        action_layout.addWidget(self.level_label)
        action_layout.addWidget(self.pain_label)
        action_layout.addWidget(self.advice_label)

        buttons = QHBoxLayout()
        self.back_btn = QPushButton("Back")
        self.back_btn.setObjectName("secondaryButton")

        self.emergency_btn = QPushButton("Emergency Help")
        self.emergency_btn.setObjectName("secondaryButton")

        self.home_btn = QPushButton("Start New Assessment")
        self.home_btn.setObjectName("primaryButton")

        buttons.addWidget(self.back_btn)
        buttons.addWidget(self.emergency_btn)
        buttons.addStretch()
        buttons.addWidget(self.home_btn)

        root.addWidget(self.title_label)
        root.addWidget(self.summary_card)
        root.addWidget(self.conditions_card, 1)
        root.addWidget(self.action_card)
        root.addLayout(buttons)

        self.home_btn.clicked.connect(self.home_clicked.emit)
        self.back_btn.clicked.connect(self.back_clicked.emit)
        self.emergency_btn.clicked.connect(self.emergency_clicked.emit)

    def _is_kriol_mode(self) -> bool:
        return self.strings.get("back", "Back").strip().lower() == "bek"

    def _translate_display_text(self, text: str) -> str:
        if not self._is_kriol_mode() or not text:
            return text

        display_map = {
            "headache": self.strings.get("symptom_headache", "Hedake"),
            "fever": self.strings.get("symptom_fever", "Fiba"),
            "cough": self.strings.get("symptom_cough", "Kof"),
            "stomach pain": self.strings.get("symptom_stomach_pain", "Beli pein"),
            "sore throat": self.strings.get("symptom_sore_throat", "Throt pein"),
            "body pain": self.strings.get("symptom_body_pain", "Bodi pein"),
            "tired": self.strings.get("symptom_tired", "Taid"),
            "dizzy": self.strings.get("symptom_dizzy", "Dizi"),
            "chest pain": self.strings.get("symptom_chest_pain", "Jes pein"),
            "skin problem": self.strings.get("symptom_skin_problem", "Skin trabul"),
            "pain": "pein",
            "weak": "wik",
            "vomiting": "spyu",
            "diarrhea": "ranishit",
            "rash": "rash",
            "breathing problem": "brithin trabul",
            "mild": "lilit",
            "moderate": "medel",
            "serious": "brabli nogud",
            "visit clinic soon": "Go klinik kwikbala",
            "get urgent help now": "Garrim kwikwan elp nau",
            "rest and monitor": "Res en wajim",
            "matched with rash symptoms": "Mached wet rash sikwan sain",
            "matched with cough symptoms": "Mached wet kof sikwan sain",
            "matched with fever symptoms": "Mached wet fiba sikwan sain",
            "matched with stomach symptoms": "Mached wet beli sikwan sain",
            "skin / rash problem": "Skin / rash trabul",
            "level": "Lebul"

        }

        result = text
        for eng, kriol in sorted(display_map.items(), key=lambda x: len(x[0]), reverse=True):
            result = re.sub(rf"\b{re.escape(eng)}\b", kriol, result, flags=re.IGNORECASE)

        return result

    def set_strings(self, s: dict):
        self.strings = s
        self.title_label.setText(s.get("result", "Result"))
        self.back_btn.setText(s.get("back", "Back"))
        self.home_btn.setText(s.get("start_new_assessment", "Start New Assessment"))
        self.emergency_btn.setText(s.get("emergency", "Emergency Help"))
        self.cond_title.setText(s.get("related_conditions", "Related conditions"))

    def set_result(self, data: dict):
        nlp = data["nlp"]
        result = data["result"]

        you_said = self.strings.get("you_said_label", "You said")
        english_meaning = self.strings.get("english_meaning_label", "English meaning")
        symptoms_found = self.strings.get("symptoms_found_label", "Symptoms found")
        pain_level = self.strings.get("pain_level_label", "Pain level")
        triage_level = self.strings.get("triage_level_label", "Triage level")

        display_original = self._translate_display_text(nlp["original_text"])
        display_meaning = self._translate_display_text(nlp["translated_text_en"])
        display_symptoms = self._translate_display_text(", ".join(nlp["symptoms"]))
        display_level = self._translate_display_text(result["triage_level"].upper())
        display_advice = self._translate_display_text(result["advice"])

        self.original_label.setText(f"{you_said}: {display_original}")
        self.english_label.setText(f"{english_meaning}: {display_meaning}")
        self.symptoms_label.setText(f"{symptoms_found}: {display_symptoms}")
        self.pain_label.setText(f"{pain_level}: {result['pain_scale']} / 10")
        self.level_label.setText(f"{triage_level}: {display_level}")
        self.advice_label.setText(display_advice)

        level = result["triage_level"].lower()
        if level == "mild":
            self.level_label.setStyleSheet("color: #0072B2; font-size: 30px; font-weight: 800;")
        elif level == "moderate":
            self.level_label.setStyleSheet("color: #E69F00; font-size: 30px; font-weight: 800;")
        elif level in ("high", "serious"):
            self.level_label.setStyleSheet("color: #D55E00; font-size: 30px; font-weight: 800;")
        else:
            self.level_label.setStyleSheet("color: #B10000; font-size: 30px; font-weight: 800;")

        while self.cards_grid.count():
            item = self.cards_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        row = 0
        col = 0
        for item in result["possible_conditions"]:
            card = DiseaseCard(
                title=self._translate_display_text(item["name"]),
                why=self._translate_display_text(item["why"]),
                severity=self._translate_display_text(item["severity"]),
                image_path=item["image"],
            )
            self.cards_grid.addWidget(card, row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1