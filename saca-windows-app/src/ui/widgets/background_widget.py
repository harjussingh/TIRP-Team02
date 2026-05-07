from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QWidget


class PatternBackgroundWidget(QWidget):
    """Paints the SACA pattern behind the application pages.

    The emergency page can switch this widget into plain-background mode so the
    emergency screen stays calmer and easier to read.
    """

    def __init__(self, image_path: str | Path, parent: QWidget | None = None):
        super().__init__(parent)
        self.image_path = Path(image_path)
        self.pixmap = QPixmap(str(self.image_path))
        self.emergency_mode = False
        self.setObjectName("patternBackgroundWidget")
        self.setAttribute(Qt.WA_StyledBackground, True)

        if self.pixmap.isNull():
            print(f"[SACA] Background image could not be loaded: {self.image_path}")

    def set_emergency_mode(self, enabled: bool) -> None:
        self.emergency_mode = enabled
        self.update()

    def paintEvent(self, event):  # noqa: N802 - Qt override name
        painter = QPainter(self)

        if self.emergency_mode or self.pixmap.isNull():
            painter.fillRect(self.rect(), QColor("#F2E6D8"))
            return

        # Cover the whole window without distorting the image.
        scaled = self.pixmap.scaled(
            self.size(),
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation,
        )
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)
