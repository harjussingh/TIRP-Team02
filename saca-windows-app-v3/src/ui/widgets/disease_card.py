import os
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel


class DiseaseCard(QFrame):
    def __init__(self, title: str, why: str, severity: str, image_path: str):
        super().__init__()
        self.setObjectName("diseaseCard")
        self.setMinimumHeight(250)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        image_label = QLabel()
        image_label.setObjectName("imageBox")
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setFixedHeight(120)

        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            image_label.setPixmap(
                pixmap.scaled(220, 110, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        else:
            image_label.setText("Image")

        title_label = QLabel(title)
        title_label.setObjectName("diseaseTitle")
        title_label.setWordWrap(True)

        why_label = QLabel(why)
        why_label.setObjectName("diseaseDescription")
        why_label.setWordWrap(True)

        severity_label = QLabel(f"Level: {severity}")
        severity_label.setObjectName("diseaseMeta")

        layout.addWidget(image_label)
        layout.addWidget(title_label)
        layout.addWidget(why_label)
        layout.addWidget(severity_label)
        layout.addStretch()