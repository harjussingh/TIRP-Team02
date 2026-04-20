import os
import sys
from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow


def load_stylesheet(app: QApplication) -> None:
    qss_path = os.path.join("assets", "styles", "main.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())


def main() -> int:
    app = QApplication(sys.argv)
    load_stylesheet(app)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())