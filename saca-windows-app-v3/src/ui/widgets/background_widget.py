from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QWidget


class PatternBackgroundWidget(QWidget):
    """Paints the SACA pattern behind the app pages.

    - Normal pages: image fills the whole window and is shown at 50% opacity.
    - Emergency page: plain clay background for readability.
    """

    def __init__(self, image_path: str | Path, parent: QWidget | None = None):
        super().__init__(parent)
        self.image_path = Path(image_path)
        self.pixmap = QPixmap(str(self.image_path))
        self.emergency_mode = False
        self.background_opacity = 0.50
        self.setObjectName("patternBackgroundWidget")
        self.setAttribute(Qt.WA_StyledBackground, True)

        if self.pixmap.isNull():
            print(f"[SACA] Background image could not be loaded: {self.image_path}")

    def set_emergency_mode(self, enabled: bool) -> None:
        self.emergency_mode = enabled
        self.update()

    def set_background_opacity(self, opacity: float) -> None:
        self.background_opacity = max(0.0, min(1.0, float(opacity)))
        self.update()

    def paintEvent(self, event):  # noqa: N802 - Qt override name
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # Base colour under the pattern. This makes 50% opacity look soft,
        # not dark or busy.
        painter.fillRect(self.rect(), QColor("#F2E6D8"))

        if self.emergency_mode or self.pixmap.isNull():
            return

        # Cover the whole window while keeping the image ratio.
        scaled = self.pixmap.scaled(
            self.size(),
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation,
        )
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2

        painter.setOpacity(self.background_opacity)
        painter.drawPixmap(x, y, scaled)
        painter.setOpacity(1.0)
