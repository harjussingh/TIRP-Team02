from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, QComboBox,
    QHBoxLayout
)


class HomePage(QWidget):
    speak_clicked = Signal()
    type_clicked = Signal()
    pictures_clicked = Signal()
    emergency_clicked = Signal()
    language_changed = Signal(str)

    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)
        root.setContentsMargins(70, 40, 70, 40)
        root.setSpacing(24)
        root.setAlignment(Qt.AlignCenter)

        header = QHBoxLayout()
        header.addStretch()

        self.language_picker = QComboBox()
        self.language_picker.addItem("English", "en")
        self.language_picker.addItem("Kriol", "kriol")
        self.language_picker.setMinimumHeight(50)
        self.language_picker.setMinimumWidth(170)

        header.addWidget(self.language_picker)
        root.addLayout(header)

        card = QFrame()
        card.setObjectName("mainSimpleCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(50, 40, 50, 40)
        card_layout.setSpacing(20)

        self.icon_label = QLabel("💜")
        self.icon_label.setObjectName("micIcon")
        self.icon_label.setAlignment(Qt.AlignCenter)

        self.title_label = QLabel("Tell us how you feel")
        self.title_label.setObjectName("mainTitle")
        self.title_label.setAlignment(Qt.AlignCenter)

        self.subtitle_label = QLabel("Choose one")
        self.subtitle_label.setObjectName("mainSubtitle")
        self.subtitle_label.setAlignment(Qt.AlignCenter)

        self.speak_btn = QPushButton("🎤 Speak")
        self.speak_btn.setObjectName("bigPrimaryButton")
        self.speak_btn.setMinimumHeight(88)

        self.type_btn = QPushButton("⌨️ Type")
        self.type_btn.setObjectName("bigSecondaryButton")
        self.type_btn.setMinimumHeight(88)

        self.pictures_btn = QPushButton("🖼️ Pictures")
        self.pictures_btn.setObjectName("bigSecondaryButton")
        self.pictures_btn.setMinimumHeight(88)

        self.emergency_btn = QPushButton("🚨 Emergency Help")
        self.emergency_btn.setObjectName("emergencyButton")
        self.emergency_btn.setMinimumHeight(88)

        self.footer_label = QLabel("Simple health support prototype for Ngukurr community")
        self.footer_label.setObjectName("cardBody")
        self.footer_label.setAlignment(Qt.AlignCenter)
        self.footer_label.setWordWrap(True)

        card_layout.addWidget(self.icon_label)
        card_layout.addWidget(self.title_label)
        card_layout.addWidget(self.subtitle_label)
        card_layout.addSpacing(4)
        card_layout.addWidget(self.speak_btn)
        card_layout.addWidget(self.type_btn)
        card_layout.addWidget(self.pictures_btn)
        card_layout.addWidget(self.emergency_btn)
        card_layout.addSpacing(8)
        card_layout.addWidget(self.footer_label)

        root.addWidget(card)

        self.speak_btn.clicked.connect(self.speak_clicked.emit)
        self.type_btn.clicked.connect(self.type_clicked.emit)
        self.pictures_btn.clicked.connect(self.pictures_clicked.emit)
        self.emergency_btn.clicked.connect(self.emergency_clicked.emit)
        self.language_picker.currentIndexChanged.connect(self._emit_language)

    def _emit_language(self):
        self.language_changed.emit(self.language_picker.currentData())

    def set_strings(self, s: dict):
        self.title_label.setText(s.get("home_title", "Tell us how you feel"))
        self.subtitle_label.setText(s.get("home_subtitle", "Choose one"))
        self.speak_btn.setText(s.get("speak", "🎤 Speak"))
        self.type_btn.setText(s.get("type", "⌨️ Type"))
        self.pictures_btn.setText(s.get("pictures", "🖼️ Pictures"))
        self.emergency_btn.setText(s.get("emergency", "🚨 Emergency Help"))
        self.footer_label.setText(
            s.get("home_footer", "Simple health support prototype for Ngukurr community")
        )