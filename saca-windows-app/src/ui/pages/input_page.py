from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QTextCursor, QPainter, QPen, QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QPushButton,
    QFrame,
    QSizePolicy,
    QStackedWidget,
)

from src.services.voice_service import VoiceService


class MicCircleButton(QPushButton):
    def __init__(self):
        super().__init__()
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(260, 260)
        self.setText("")

        self.setStyleSheet("""
            QPushButton {
                background-color: #0052A3;
                border: none;
                border-radius: 130px;
            }

            QPushButton:hover {
                background-color: #00468C;
            }

            QPushButton:pressed {
                background-color: #003A74;
            }
        """)

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        pen = QPen(QColor("#FFFFFF"), 8)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        painter.drawRoundedRect(108, 70, 44, 82, 22, 22)
        painter.drawArc(82, 112, 96, 88, 200 * 16, 140 * 16)
        painter.drawLine(130, 198, 130, 220)


class InputPage(QWidget):
    back_clicked = Signal()
    emergency_clicked = Signal()
    submit_clicked = Signal(str)

    def __init__(self):
        super().__init__()

        self.strings = {}
        self.current_mode = "type"

        # ---------- Full screen root ----------
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(0, 0, 0, 0)
        self.root.setSpacing(0)

        # ---------- Center content ----------
        self.content = QWidget()
        self.content.setMinimumWidth(900)
        self.content.setMaximumWidth(900)

        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(20)

        self.root.addStretch(1)
        self.root.addWidget(self.content, alignment=Qt.AlignHCenter)
        self.root.addStretch(1)

        # ---------- Page title for type mode ----------
        self.page_title = QLabel("Type Your Symptoms")
        self.page_title.setAlignment(Qt.AlignLeft)
        self.page_title.setStyleSheet("""
            QLabel {
                color: #0052A3;
                font-size: 36px;
                font-weight: 900;
                background: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """)
        self.content_layout.addWidget(self.page_title)

        # ---------- Mode stack ----------
        self.mode_stack = QStackedWidget()
        self.mode_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.content_layout.addWidget(self.mode_stack)

        self.type_page = self._build_type_page()
        self.voice_page = self._build_voice_page()

        self.mode_stack.addWidget(self.type_page)
        self.mode_stack.addWidget(self.voice_page)

        # Voice recording service for the mic button. It records audio and,
        # when Whisper is installed, fills the text box with transcription.
        self.voice_service = VoiceService(self)
        self._connect_voice_service()

        # ---------- Bottom buttons: kept as before ----------
        self.button_row = QHBoxLayout()
        self.button_row.setSpacing(18)

        self.back_btn = QPushButton("←  Back")
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.setFixedHeight(64)
        self.back_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #0052A3;
                border: 3px solid #0052A3;
                border-radius: 16px;
                font-size: 17px;
                font-weight: 900;
                padding: 12px 18px;
            }

            QPushButton:hover {
                background-color: #EEF4FB;
            }
        """)

        self.emergency_btn = QPushButton("ⓘ  Emergency")
        self.emergency_btn.setCursor(Qt.PointingHandCursor)
        self.emergency_btn.setFixedHeight(64)
        self.emergency_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.emergency_btn.setStyleSheet("""
            QPushButton {
                background-color: #B10000;
                color: #FFFFFF;
                border: none;
                border-radius: 16px;
                font-size: 17px;
                font-weight: 900;
                padding: 12px 18px;
            }

            QPushButton:hover {
                background-color: #970000;
            }
        """)

        self.next_btn = QPushButton("Next  →")
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.setFixedHeight(64)
        self.next_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.submit_btn = self.next_btn

        self.button_row.addWidget(self.back_btn)
        self.button_row.addWidget(self.emergency_btn)
        self.button_row.addWidget(self.next_btn)

        self.content_layout.addLayout(self.button_row)

        # ---------- Connections ----------
        self.back_btn.clicked.connect(self.back_clicked.emit)
        self.emergency_btn.clicked.connect(self.emergency_clicked.emit)
        self.next_btn.clicked.connect(self._submit)

        self._update_mode_ui()
        self._update_next_button()

    # --------------------------------------------------
    # Type page
    # --------------------------------------------------
    def _build_type_page(self):
        page = QFrame()
        page.setObjectName("typeInputCard")
        page.setFixedHeight(520)
        page.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        page.setStyleSheet("""
            QFrame#typeInputCard {
                background-color: #FFFFFF;
                border: 1px solid #D8C9BA;
                border-radius: 22px;
            }
        """)

        layout = QVBoxLayout(page)
        layout.setContentsMargins(42, 34, 42, 32)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignTop)

        self.section_label = QLabel("How do you feel?")
        self.section_label.setAlignment(Qt.AlignLeft)
        self.section_label.setStyleSheet("""
            QLabel {
                color: #2D1810;
                font-size: 19px;
                font-weight: 900;
                background: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """)
        layout.addWidget(self.section_label)

        self.input_box = QTextEdit()
        self.input_box.setPlaceholderText("Type your symptoms here...")
        self.input_box.setFixedHeight(170)
        self.input_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.input_box.setStyleSheet("""
            QTextEdit {
                background-color: #FFFFFF;
                border: 2px solid #D8C9BA;
                border-radius: 16px;
                padding: 18px 20px;
                color: #2D1810;
                font-size: 18px;
                font-weight: 700;
            }

            QTextEdit:focus {
                border: 2px solid #0052A3;
            }
        """)
        self.input_box.textChanged.connect(self._update_next_button)
        layout.addWidget(self.input_box)

        # Compatibility aliases
        self.type_box = self.input_box
        self.text_input = self.input_box

        layout.addSpacing(10)

        self.quick_label = QLabel("Quick select symptoms:")
        self.quick_label.setAlignment(Qt.AlignLeft)
        self.quick_label.setStyleSheet("""
            QLabel {
                color: #2D1810;
                font-size: 18px;
                font-weight: 900;
                background: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """)
        layout.addWidget(self.quick_label)

        layout.addSpacing(8)

        self.quick_area = QVBoxLayout()
        self.quick_area.setSpacing(12)
        self.quick_area.setContentsMargins(0, 0, 0, 0)

        self.quick_row_1 = QHBoxLayout()
        self.quick_row_1.setSpacing(12)

        self.quick_row_2 = QHBoxLayout()
        self.quick_row_2.setSpacing(12)

        self.quick_area.addLayout(self.quick_row_1)
        self.quick_area.addLayout(self.quick_row_2)

        layout.addLayout(self.quick_area)

        self.quick_buttons = []

        row_1 = [
            ("Headache", 130),
            ("Fever", 90),
            ("Cough", 100),
            ("Stomach pain", 160),
            ("Sore throat", 145),
        ]

        row_2 = [
            ("Body ache", 140),
            ("Tired", 95),
            ("Dizzy", 95),
        ]

        for text, width in row_1:
            btn = self._make_quick_button(text, width)
            self.quick_row_1.addWidget(btn)
            self.quick_buttons.append(btn)

        self.quick_row_1.addStretch()

        for text, width in row_2:
            btn = self._make_quick_button(text, width)
            self.quick_row_2.addWidget(btn)
            self.quick_buttons.append(btn)

        self.quick_row_2.addStretch()

        return page

    # --------------------------------------------------
    # Speak / voice page
    # --------------------------------------------------
    def _build_voice_page(self):
        page = QWidget()
        page.setFixedHeight(640)
        page.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignTop)

        self.voice_title = QLabel("What's wrong?")
        self.voice_title.setAlignment(Qt.AlignLeft)
        self.voice_title.setStyleSheet("""
            QLabel {
                color: #1D1D1D;
                font-size: 42px;
                font-weight: 900;
                background: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """)
        layout.addWidget(self.voice_title)

        self.voice_subtitle = QLabel("Tap and speak")
        self.voice_subtitle.setAlignment(Qt.AlignLeft)
        self.voice_subtitle.setStyleSheet("""
            QLabel {
                color: #7A6D62;
                font-size: 26px;
                font-weight: 700;
                background: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """)
        layout.addWidget(self.voice_subtitle)

        # Move mic slightly up
        layout.addSpacing(35)

        mic_row = QHBoxLayout()
        mic_row.addStretch()

        self.mic_btn = MicCircleButton()
        self.mic_btn.clicked.connect(self._handle_mic_click)

        mic_row.addWidget(self.mic_btn)
        mic_row.addStretch()

        layout.addLayout(mic_row)

        layout.addSpacing(28)

        self.voice_status_label = QLabel("Tap the mic")
        self.voice_status_label.setAlignment(Qt.AlignCenter)
        self.voice_status_label.setWordWrap(True)
        self.voice_status_label.setStyleSheet("""
            QLabel {
                color: #3B302A;
                font-size: 22px;
                font-weight: 900;
                background: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """)
        layout.addWidget(self.voice_status_label)

        layout.addSpacing(20)

        self.voice_text_box = QTextEdit()
        self.voice_text_box.setPlaceholderText("Your words will show here...")
        self.voice_text_box.setFixedHeight(150)
        self.voice_text_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.voice_text_box.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                border: 3px dashed #E2D8CD;
                border-radius: 22px;
                padding: 22px 26px;
                color: #2D1810;
                font-size: 24px;
                font-weight: 700;
            }

            QTextEdit:focus {
                border: 3px dashed #0052A3;
            }
        """)
        self.voice_text_box.textChanged.connect(self._update_next_button)
        layout.addWidget(self.voice_text_box)

        self.voice_box = self.voice_text_box

        return page

    # --------------------------------------------------
    # Quick symptom buttons
    # --------------------------------------------------
    def _make_quick_button(self, text: str, width: int):
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(46)
        btn.setMinimumWidth(width)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        btn.setStyleSheet("""
            QPushButton {
                background-color: #F7F3EE;
                color: #2D1810;
                border: 2px solid #9D5D2E;
                border-radius: 20px;
                font-size: 15px;
                font-weight: 900;
                padding: 0px 16px;
            }

            QPushButton:hover {
                background-color: #FFF5EA;
                border: 2px solid #0052A3;
            }

            QPushButton:pressed {
                background-color: #EADFD2;
            }
        """)

        btn.clicked.connect(lambda checked=False, symptom=text: self._add_symptom(symptom))
        return btn

    def _add_symptom(self, symptom: str):
        current = self.input_box.toPlainText().strip()

        if symptom.lower() in current.lower():
            return

        new_text = f"{current}, {symptom}" if current else symptom
        self.input_box.setPlainText(new_text)

        cursor = self.input_box.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.input_box.setTextCursor(cursor)

        self._update_next_button()

    # --------------------------------------------------
    # Mic button
    # --------------------------------------------------
    def _connect_voice_service(self):
        self.voice_service.status.connect(self.voice_status_label.setText)
        self.voice_service.recording_started.connect(self._on_voice_recording_started)
        self.voice_service.recording_stopped.connect(self._on_voice_recording_stopped)
        self.voice_service.transcription_ready.connect(self._on_voice_transcription_ready)
        self.voice_service.error.connect(self._on_voice_error)

    def _handle_mic_click(self):
        if self.voice_service.is_recording:
            self.voice_service.stop_recording()
            return

        self.voice_text_box.clear()
        self.voice_text_box.setPlaceholderText(
            self.strings.get("voice_placeholder", "Your words will show here...")
        )
        self.voice_service.start_recording(seconds=5)

    def _on_voice_recording_started(self):
        self.voice_status_label.setText(self.strings.get("listening", "Listening... speak now"))
        self.next_btn.setEnabled(False)
        self.mic_btn.setProperty("recording", True)
        self.mic_btn.style().unpolish(self.mic_btn)
        self.mic_btn.style().polish(self.mic_btn)

    def _on_voice_recording_stopped(self, audio_path: str):
        self.voice_status_label.setText("Processing voice...")
        self.mic_btn.setProperty("recording", False)
        self.mic_btn.style().unpolish(self.mic_btn)
        self.mic_btn.style().polish(self.mic_btn)

    def _on_voice_transcription_ready(self, text: str):
        self.voice_text_box.setPlainText(text)
        self.voice_status_label.setText("Voice captured. Check the text, then press Next.")
        self._update_next_button()

    def _on_voice_error(self, message: str):
        self.voice_status_label.setText(message)
        self.voice_text_box.setFocus()
        self._update_next_button()

    # --------------------------------------------------
    # Mode / language
    # --------------------------------------------------
    def set_mode(self, mode: str, strings=None):
        self.current_mode = mode

        if strings is not None:
            self.strings = strings or {}

        self.clear_input()
        self._update_mode_ui()

    def set_strings(self, strings: dict):
        self.strings = strings or {}
        self._update_mode_ui()

    def _is_kriol(self) -> bool:
        return self.strings.get("back", "Back").strip().lower() == "bek"

    def _update_mode_ui(self):
        is_kriol = self._is_kriol()

        if self.current_mode == "voice":
            self.page_title.hide()
            self.mode_stack.setFixedHeight(640)
            self.mode_stack.setCurrentWidget(self.voice_page)

            self.voice_title.setText(
                "Wanem rong?" if is_kriol else "What's wrong?"
            )

            self.voice_subtitle.setText(
                "Tap en tok" if is_kriol else "Tap and speak"
            )

            self.voice_status_label.setText(
                "Tapim maik" if is_kriol else "Tap the mic"
            )

            self.voice_text_box.setPlaceholderText(
                "Yu tok bai so iya..." if is_kriol else "Your words will show here..."
            )

        else:
            self.page_title.show()
            self.mode_stack.setFixedHeight(520)
            self.mode_stack.setCurrentWidget(self.type_page)

            self.page_title.setText(
                "Raitim Yu Simptom" if is_kriol else "Type Your Symptoms"
            )

            self.input_box.setPlaceholderText(
                "Raitim yu simptom iya..." if is_kriol else "Type your symptoms here..."
            )

        self.section_label.setText(
            "Wanim yu fil?" if is_kriol else "How do you feel?"
        )

        self.quick_label.setText(
            "Kwik simptom:" if is_kriol else "Quick select symptoms:"
        )

        self.back_btn.setText(
            "←  Bek" if is_kriol else "←  Back"
        )

        self.emergency_btn.setText(
            "ⓘ  Imijensi" if is_kriol else "ⓘ  Emergency"
        )

        self.next_btn.setText(
            "Nekis  →" if is_kriol else "Next  →"
        )

        quick_labels = [
            "Hedake" if is_kriol else "Headache",
            "Fiba" if is_kriol else "Fever",
            "Kof" if is_kriol else "Cough",
            "Beli pein" if is_kriol else "Stomach pain",
            "Throt pein" if is_kriol else "Sore throat",
            "Bodi pein" if is_kriol else "Body ache",
            "Taid" if is_kriol else "Tired",
            "Dizi" if is_kriol else "Dizzy",
        ]

        for btn, label in zip(self.quick_buttons, quick_labels):
            btn.setText(label)

        self._update_next_button()

    # --------------------------------------------------
    # Current text
    # --------------------------------------------------
    def _current_text(self) -> str:
        if self.current_mode == "voice":
            return self.voice_text_box.toPlainText().strip()

        return self.input_box.toPlainText().strip()

    # --------------------------------------------------
    # Next button
    # --------------------------------------------------
    def _update_next_button(self):
        has_text = bool(self._current_text())
        self.next_btn.setEnabled(has_text)

        if has_text:
            self.next_btn.setStyleSheet("""
                QPushButton {
                    background-color: #0052A3;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 16px;
                    font-size: 17px;
                    font-weight: 900;
                    padding: 12px 18px;
                }

                QPushButton:hover {
                    background-color: #00468C;
                }
            """)
        else:
            self.next_btn.setStyleSheet("""
                QPushButton {
                    background-color: #93A7CF;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 16px;
                    font-size: 17px;
                    font-weight: 900;
                    padding: 12px 18px;
                }
            """)

        self.next_btn.style().unpolish(self.next_btn)
        self.next_btn.style().polish(self.next_btn)

    # --------------------------------------------------
    # Submit
    # --------------------------------------------------
    def _submit(self):
        text = self._current_text()

        if not text:
            return

        self.submit_clicked.emit(text)

    def clear_input(self):
        if hasattr(self, "input_box"):
            self.input_box.clear()

        if hasattr(self, "voice_text_box"):
            self.voice_text_box.clear()

        self._update_next_button()