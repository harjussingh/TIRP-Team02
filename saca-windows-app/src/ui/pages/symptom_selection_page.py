from pathlib import Path

from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QFrame,
    QGraphicsDropShadowEffect,
    QSizePolicy,
)


ASSETS_DIR = Path(__file__).resolve().parents[3] / "assets" / "symptoms"

SYMPTOM_ITEMS = [
    {
        "key": "headache",
        "query": "headache",
        "label": "Headache",
        "image": "headache.png",
    },
    {
        "key": "chest_pain",
        "query": "chest pain",
        "label": "Chest pain",
        "image": "chest_pain.png",
    },
    {
        "key": "stomach_pain",
        "query": "stomach pain",
        "label": "Stomach pain",
        "image": "stomach_pain.png",
    },
    {
        "key": "skin_problem",
        "query": "skin problem",
        "label": "Skin problem",
        "image": "skin_problem.png",
    },
    {
        "key": "sore_throat",
        "query": "sore throat",
        "label": "Sore throat",
        "image": "sore_throat.png",
    },
    {
        "key": "body_pain",
        "query": "body pain",
        "label": "Body pain",
        "image": "body_pain.png",
    },
    {
        "key": "cough",
        "query": "cough",
        "label": "Cough",
        "image": "cough.png",
    },
    {
        "key": "fever",
        "query": "fever",
        "label": "Fever",
        "image": "fever.png",
    },
]


class SymptomCard(QFrame):
    clicked = Signal(str)

    def __init__(self, key: str, label_text: str, query_text: str, image_path: Path):
        super().__init__()

        self.key = key
        self.label_text = label_text
        self.query_text = query_text
        self.image_path = image_path
        self.is_selected = False

        self.setObjectName("symptomCard")
        self.setProperty("hovered", False)
        self.setProperty("selected", False)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(280, 220)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(14)
        self.shadow.setOffset(0, 4)
        self.shadow.setColor(QColor(0, 0, 0, 35))
        self.setGraphicsEffect(self.shadow)

        self.blur_anim = QPropertyAnimation(self.shadow, b"blurRadius")
        self.blur_anim.setDuration(160)
        self.blur_anim.setEasingCurve(QEasingCurve.OutCubic)

        self.offset_anim = QPropertyAnimation(self.shadow, b"yOffset")
        self.offset_anim.setDuration(160)
        self.offset_anim.setEasingCurve(QEasingCurve.OutCubic)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.image_label = QLabel()
        self.image_label.setObjectName("symptomCardImage")
        self.image_label.setFixedHeight(160)
        self.image_label.setAlignment(Qt.AlignCenter)

        self.text_label = QLabel(label_text)
        self.text_label.setObjectName("symptomCardTitle")
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setFixedHeight(60)

        root.addWidget(self.image_label)
        root.addWidget(self.text_label)

        self._load_image()

    def _load_image(self):
        if self.image_path.exists():
            pixmap = QPixmap(str(self.image_path))
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    278,
                    158,
                    Qt.KeepAspectRatioByExpanding,
                    Qt.SmoothTransformation,
                )
                self.image_label.setPixmap(scaled)
                return

        self.image_label.setText("No image")

    def set_label(self, text: str):
        self.label_text = text
        self.text_label.setText(text)

    def set_selected(self, value: bool):
        self.is_selected = value
        self.setProperty("selected", value)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def enterEvent(self, event):
        self.setProperty("hovered", True)
        self.style().unpolish(self)
        self.style().polish(self)

        self.blur_anim.stop()
        self.blur_anim.setStartValue(self.shadow.blurRadius())
        self.blur_anim.setEndValue(26)
        self.blur_anim.start()

        self.offset_anim.stop()
        self.offset_anim.setStartValue(self.shadow.yOffset())
        self.offset_anim.setEndValue(9)
        self.offset_anim.start()

        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setProperty("hovered", False)
        self.style().unpolish(self)
        self.style().polish(self)

        self.blur_anim.stop()
        self.blur_anim.setStartValue(self.shadow.blurRadius())
        self.blur_anim.setEndValue(14)
        self.blur_anim.start()

        self.offset_anim.stop()
        self.offset_anim.setStartValue(self.shadow.yOffset())
        self.offset_anim.setEndValue(4)
        self.offset_anim.start()

        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.key)
        super().mousePressEvent(event)


class SymptomSelectionPage(QWidget):
    back_clicked = Signal()
    emergency_clicked = Signal()
    continue_clicked = Signal(str)

    def __init__(self):
        super().__init__()

        self.strings = {}
        self.selected_keys = []
        self.cards = {}
        self.item_map = {item["key"]: item for item in SYMPTOM_ITEMS}

        root = QVBoxLayout(self)
        root.setContentsMargins(48, 20, 48, 26)
        root.setSpacing(0)
        root.setAlignment(Qt.AlignTop)

        self.title_label = QLabel("Select Your Symptoms")
        self.title_label.setObjectName("selectionPageTitle")
        self.title_label.setAlignment(Qt.AlignLeft)

        self.subtitle_label = QLabel("Tap on the pictures that match how you feel")
        self.subtitle_label.setObjectName("selectionPageSubtitle")
        self.subtitle_label.setAlignment(Qt.AlignLeft)

        self.helper_label = QLabel("You can choose more than one")
        self.helper_label.setObjectName("selectionPageHelper")
        self.helper_label.setAlignment(Qt.AlignLeft)

        root.addWidget(self.title_label)
        root.addSpacing(4)
        root.addWidget(self.subtitle_label)
        root.addSpacing(8)
        root.addWidget(self.helper_label)
        root.addSpacing(24)

        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(18)
        self.grid.setVerticalSpacing(18)
        self.grid.setContentsMargins(0, 0, 0, 0)

        for index, item in enumerate(SYMPTOM_ITEMS):
            row = index // 4
            col = index % 4

            image_path = ASSETS_DIR / item["image"]

            card = SymptomCard(
                key=item["key"],
                label_text=item["label"],
                query_text=item["query"],
                image_path=image_path,
            )
            card.clicked.connect(self._toggle_symptom)

            self.cards[item["key"]] = card
            self.grid.addWidget(card, row, col)

        root.addLayout(self.grid)
        root.addSpacing(28)

        button_row = QHBoxLayout()
        button_row.setContentsMargins(0, 0, 0, 0)
        button_row.setSpacing(20)

        self.back_btn = QPushButton("Back")
        self.back_btn.setObjectName("backWideButton")
        self.back_btn.setFixedSize(300, 64)
        self.back_btn.clicked.connect(self.back_clicked.emit)

        self.emergency_btn = QPushButton("🚨 Emergency Help")
        self.emergency_btn.setObjectName("emergencyWideButton")
        self.emergency_btn.setFixedSize(300, 64)
        self.emergency_btn.clicked.connect(self.emergency_clicked.emit)

        self.continue_btn = QPushButton("Continue")
        self.continue_btn.setObjectName("continueWideButton")
        self.continue_btn.setFixedSize(300, 64)
        self.continue_btn.setEnabled(False)
        self.continue_btn.clicked.connect(self._emit_selection)

        button_row.addWidget(self.back_btn)
        button_row.addWidget(self.emergency_btn)
        button_row.addWidget(self.continue_btn)

        root.addLayout(button_row)

    def _toggle_symptom(self, key: str):
        if key in self.selected_keys:
            self.selected_keys.remove(key)
        else:
            self.selected_keys.append(key)

        for card_key, card in self.cards.items():
            card.set_selected(card_key in self.selected_keys)

        count = len(self.selected_keys)
        if count == 0:
            self.helper_label.setText("You can choose more than one")
            self.continue_btn.setEnabled(False)
        elif count == 1:
            self.helper_label.setText("1 symptom selected")
            self.continue_btn.setEnabled(True)
        else:
            self.helper_label.setText(f"{count} symptoms selected")
            self.continue_btn.setEnabled(True)

    def _emit_selection(self):
        if not self.selected_keys:
            return

        ordered_queries = []
        for item in SYMPTOM_ITEMS:
            if item["key"] in self.selected_keys:
                ordered_queries.append(item["query"])

        self.continue_clicked.emit(", ".join(ordered_queries))

    def clear_selection(self):
        self.selected_keys = []
        for card in self.cards.values():
            card.set_selected(False)
        self.helper_label.setText("You can choose more than one")
        self.continue_btn.setEnabled(False)

    def set_strings(self, s: dict):
        self.strings = s or {}

        self.title_label.setText(
            self.strings.get("symptom_selection_title", "Select Your Symptoms")
        )
        self.subtitle_label.setText(
            self.strings.get(
                "symptom_selection_subtitle",
                "Tap on the pictures that match how you feel",
            )
        )

        if len(self.selected_keys) == 0:
            self.helper_label.setText(
                self.strings.get(
                    "symptom_selection_helper",
                    "You can choose more than one",
                )
            )

        self.back_btn.setText(self.strings.get("back", "Back"))
        self.emergency_btn.setText(self.strings.get("emergency", "🚨 Emergency Help"))
        self.continue_btn.setText(self.strings.get("continue", "Continue"))

        symptom_text_map = {
            "headache": self.strings.get("symptom_headache", "Headache"),
            "chest_pain": self.strings.get("symptom_chest_pain", "Chest pain"),
            "stomach_pain": self.strings.get("symptom_stomach_pain", "Stomach pain"),
            "skin_problem": self.strings.get("symptom_skin_problem", "Skin problem"),
            "sore_throat": self.strings.get("symptom_sore_throat", "Sore throat"),
            "body_pain": self.strings.get("symptom_body_pain", "Body pain"),
            "cough": self.strings.get("symptom_cough", "Cough"),
            "fever": self.strings.get("symptom_fever", "Fever"),
        }

        for key, card in self.cards.items():
            if key in symptom_text_map:
                card.set_label(symptom_text_map[key])