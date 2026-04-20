from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFrame


class EmergencyPage(QWidget):
    back_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.strings = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(90, 60, 90, 60)
        root.setSpacing(22)
        root.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setObjectName("emergencyCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(18)

        self.title_label = QLabel("🚨 Emergency Help")
        self.title_label.setObjectName("emergencyTitle")
        self.title_label.setAlignment(Qt.AlignCenter)

        self.warning_label = QLabel(
            "Trouble breathing?\nChest pain?\nHeavy bleeding?\nPassed out?"
        )
        self.warning_label.setObjectName("emergencyBody")
        self.warning_label.setAlignment(Qt.AlignCenter)
        self.warning_label.setWordWrap(True)

        self.help_label = QLabel(
            "Get emergency help now or go to the nearest clinic."
        )
        self.help_label.setObjectName("emergencyBody")
        self.help_label.setAlignment(Qt.AlignCenter)
        self.help_label.setWordWrap(True)

        self.back_btn = QPushButton("Back")
        self.back_btn.setObjectName("bigSecondaryButton")
        self.back_btn.setMinimumHeight(70)

        layout.addWidget(self.title_label)
        layout.addWidget(self.warning_label)
        layout.addWidget(self.help_label)
        layout.addWidget(self.back_btn)

        root.addWidget(card)

        self.back_btn.clicked.connect(self.back_clicked.emit)

    def set_strings(self, s: dict):
        self.strings = s
        self.title_label.setText(s.get("emergency", "🚨 Emergency Help"))
        self.warning_label.setText(
            s.get(
                "emergency_warning_list",
                "Trouble breathing?\nChest pain?\nHeavy bleeding?\nPassed out?"
            )
        )
        self.help_label.setText(
            s.get(
                "emergency_instruction",
                "Get emergency help now or go to the nearest clinic."
            )
        )
        self.back_btn.setText(s.get("back", "Back"))