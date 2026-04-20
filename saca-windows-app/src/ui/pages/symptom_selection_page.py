from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QFrame, QGridLayout
)


class SymptomSelectionPage(QWidget):
    back_clicked = Signal()
    emergency_clicked = Signal()
    continue_clicked = Signal(str)

    def __init__(self):
        super().__init__()
        self.selected = set()
        self.symptom_buttons = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(55, 35, 55, 35)
        root.setSpacing(20)

        self.title_label = QLabel("Choose pictures that match your symptoms")
        self.title_label.setObjectName("mainTitle")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setWordWrap(True)

        self.subtitle_label = QLabel("You can choose more than one")
        self.subtitle_label.setObjectName("mainSubtitle")
        self.subtitle_label.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setObjectName("contentCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 22, 22, 22)
        card_layout.setSpacing(16)

        self.count_label = QLabel("0 selected")
        self.count_label.setObjectName("cardBody")
        self.count_label.setAlignment(Qt.AlignCenter)

        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(16)
        self.grid.setVerticalSpacing(16)

        symptoms = [
            ("headache", "🧠 Headache"),
            ("chest_pain", "❤️ Chest pain"),
            ("stomach_pain", "🫃 Stomach pain"),
            ("skin_problem", "🖐 Skin problem"),
            ("sore_throat", "🗣 Sore throat"),
            ("body_pain", "🦴 Body pain"),
            ("cough", "🫁 Cough"),
            ("fever", "🌡 Fever"),
        ]

        for i, (key, label) in enumerate(symptoms):
            btn = QPushButton(label)
            btn.setObjectName("optionButton")
            btn.setCheckable(True)
            btn.setMinimumHeight(100)
            btn.clicked.connect(lambda checked, symptom_key=key: self._toggle_symptom(symptom_key))
            self.symptom_buttons[key] = btn
            self.grid.addWidget(btn, i // 2, i % 2)

        buttons = QHBoxLayout()
        self.back_btn = QPushButton("Back")
        self.back_btn.setObjectName("secondaryButton")
        self.back_btn.setMinimumHeight(50)

        self.emergency_btn = QPushButton("Emergency Help")
        self.emergency_btn.setObjectName("secondaryButton")
        self.emergency_btn.setMinimumHeight(50)

        self.continue_btn = QPushButton("Continue")
        self.continue_btn.setObjectName("primaryButton")
        self.continue_btn.setMinimumHeight(50)
        self.continue_btn.setEnabled(False)

        buttons.addWidget(self.back_btn)
        buttons.addWidget(self.emergency_btn)
        buttons.addStretch()
        buttons.addWidget(self.continue_btn)

        card_layout.addWidget(self.count_label)
        card_layout.addLayout(self.grid)
        card_layout.addLayout(buttons)

        root.addWidget(self.title_label)
        root.addWidget(self.subtitle_label)
        root.addWidget(card)

        self.back_btn.clicked.connect(self.back_clicked.emit)
        self.emergency_btn.clicked.connect(self.emergency_clicked.emit)
        self.continue_btn.clicked.connect(self._emit_selection)

    def set_strings(self, s: dict):
        self.title_label.setText(s.get("pictures_title", "Choose pictures that match your symptoms"))
        self.subtitle_label.setText(s.get("pictures_subtitle", "You can choose more than one"))
        self.back_btn.setText(s.get("back", "Back"))
        self.emergency_btn.setText(s.get("emergency", "Emergency Help"))
        self.continue_btn.setText(s.get("continue", "Continue"))

        labels = {
            "headache": s.get("symptom_headache", "Headache"),
            "chest_pain": s.get("symptom_chest_pain", "Chest pain"),
            "stomach_pain": s.get("symptom_stomach_pain", "Stomach pain"),
            "skin_problem": s.get("symptom_skin_problem", "Skin problem"),
            "sore_throat": s.get("symptom_sore_throat", "Sore throat"),
            "body_pain": s.get("symptom_body_pain", "Body pain"),
            "cough": s.get("symptom_cough", "Cough"),
            "fever": s.get("symptom_fever", "Fever"),
        }

        emoji = {
            "headache": "🧠",
            "chest_pain": "❤️",
            "stomach_pain": "🫃",
            "skin_problem": "🖐",
            "sore_throat": "🗣",
            "body_pain": "🦴",
            "cough": "🫁",
            "fever": "🌡"
        }

        for key, btn in self.symptom_buttons.items():
            btn.setText(f"{emoji[key]} {labels[key]}")

        self._update_count_label()

    def _toggle_symptom(self, symptom_key: str):
        btn = self.symptom_buttons[symptom_key]
        if btn.isChecked():
            self.selected.add(symptom_key)
        else:
            self.selected.discard(symptom_key)

        self.continue_btn.setEnabled(bool(self.selected))
        self._update_count_label()

    def _update_count_label(self):
        count = len(self.selected)
        self.count_label.setText(f"{count} selected")

    def _emit_selection(self):
        if not self.selected:
            return

        mapping = {
            "headache": "headache",
            "chest_pain": "chest pain",
            "stomach_pain": "stomach pain",
            "skin_problem": "skin problem",
            "sore_throat": "sore throat",
            "body_pain": "body pain",
            "cough": "cough",
            "fever": "fever",
        }

        text = ", ".join(mapping[key] for key in self.selected)
        self.continue_clicked.emit(text)