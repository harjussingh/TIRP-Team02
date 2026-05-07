from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFrame


class EmergencyPage(QWidget):
    back_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.strings = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(70, 50, 70, 50)
        root.setSpacing(22)
        root.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setObjectName("emergencyCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        self.title_label = QLabel("🚨 Emergency Help")
        self.title_label.setObjectName("emergencyTitle")
        self.title_label.setAlignment(Qt.AlignCenter)

        self.signs_title = QLabel("Call 000 if you have:")
        self.signs_title.setObjectName("fieldLabel")
        self.signs_title.setAlignment(Qt.AlignLeft)

        self.item_1 = QLabel("Trouble breathing")
        self.item_1.setObjectName("emergencyListItem")

        self.item_2 = QLabel("Chest pain")
        self.item_2.setObjectName("emergencyListItem")

        self.item_3 = QLabel("Heavy bleeding")
        self.item_3.setObjectName("emergencyListItem")

        self.item_4 = QLabel("Passed out / Unconscious")
        self.item_4.setObjectName("emergencyListItem")

        self.item_5 = QLabel("Hard to wake up")
        self.item_5.setObjectName("emergencyListItem")

        self.help_label = QLabel("Call 000 now or go to nearest clinic immediately")
        self.help_label.setObjectName("emergencyBody")
        self.help_label.setAlignment(Qt.AlignCenter)
        self.help_label.setWordWrap(True)

        self.back_btn = QPushButton("Go Back")
        self.back_btn.setObjectName("bigSecondaryButton")
        self.back_btn.setMinimumHeight(72)

        layout.addWidget(self.title_label)
        layout.addSpacing(4)
        layout.addWidget(self.signs_title)
        layout.addWidget(self.item_1)
        layout.addWidget(self.item_2)
        layout.addWidget(self.item_3)
        layout.addWidget(self.item_4)
        layout.addWidget(self.item_5)
        layout.addSpacing(8)
        layout.addWidget(self.help_label)
        layout.addWidget(self.back_btn)

        root.addWidget(card)
        self.back_btn.clicked.connect(self.back_clicked.emit)

    def set_strings(self, s: dict):
        self.strings = s
        is_kriol = s.get("back", "Back").strip().lower() == "bek"

        self.title_label.setText(s.get("emergency", "🚨 Emergency Help"))
        self.signs_title.setText(
            s.get("emergency_signs_title", "Kolim 000 if yu gat:" if is_kriol else "Call 000 if you have:")
        )

        self.item_1.setText(s.get("emergency_item_1", "Kandubala brid" if is_kriol else "Trouble breathing"))
        self.item_2.setText(s.get("emergency_item_2", "Ches bala" if is_kriol else "Chest pain"))
        self.item_3.setText(s.get("emergency_item_3", "Blad kamaut tumas" if is_kriol else "Heavy bleeding"))
        self.item_4.setText(
            s.get("emergency_item_4", "Pasautkol / Nomo weikap" if is_kriol else "Passed out / Unconscious")
        )
        self.item_5.setText(s.get("emergency_item_5", "Kandubala weikap" if is_kriol else "Hard to wake up"))
        self.help_label.setText(
            s.get(
                "emergency_instruction",
                "Kolim 000 nau o gowei klinik kwikwan" if is_kriol else "Call 000 now or go to nearest clinic immediately",
            )
        )
        self.back_btn.setText(s.get("go_back_label", "Gobek" if is_kriol else "Go Back"))
