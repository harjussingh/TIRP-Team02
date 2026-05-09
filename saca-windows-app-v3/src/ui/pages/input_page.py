import tempfile
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QThread
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


# ==========================================================
# Voice worker for first Speak screen
# Records short audio, transcribes using local Whisper,
# then sends text back to the input page.
# ==========================================================
class InitialVoiceWorker(QThread):
    status_changed = Signal(str)
    transcription_ready = Signal(str)
    error = Signal(str)

    _cached_model = None

    def __init__(self, duration_seconds=5, whisper_model_name="small"):
        super().__init__()
        self.duration_seconds = duration_seconds
        self.whisper_model_name = whisper_model_name

    def run(self):
        try:
            self.status_changed.emit("listening")

            try:
                import sounddevice as sd
                from scipy.io.wavfile import write
            except Exception:
                self.error.emit("Voice recording needs sounddevice and scipy.")
                return

            sample_rate = 16000
            audio = sd.rec(
                int(self.duration_seconds * sample_rate),
                samplerate=sample_rate,
                channels=1,
                dtype="float32",
            )
            sd.wait()

            self.status_changed.emit("processing")

            temp_path = Path(tempfile.gettempdir()) / "saca_initial_voice.wav"
            write(str(temp_path), sample_rate, audio)

            try:
                import whisper
            except Exception:
                self.error.emit("Whisper is not installed.")
                return

            if InitialVoiceWorker._cached_model is None:
                InitialVoiceWorker._cached_model = whisper.load_model(self.whisper_model_name)

            result = InitialVoiceWorker._cached_model.transcribe(str(temp_path), fp16=False)
            text = (result.get("text") or "").strip()

            if not text:
                self.error.emit("I could not hear clearly. Please try again.")
                return

            self.transcription_ready.emit(text)

        except Exception as e:
            self.error.emit(str(e))


class MicCircleButton(QPushButton):
    def __init__(self):
        super().__init__()

        self.state = "ready"
        self.bg_color = "#8B3A2E"
        self.icon_color = "#FFFFFF"

        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(260, 260)
        self.setText("")
        self._apply_state_style()

    def set_state(self, state: str):
        self.state = state

        if state == "ready":
            self.bg_color = "#8B3A2E"      # Deep Ochre Red
            self.icon_color = "#FFFFFF"
        elif state == "listening":
            self.bg_color = "#C65D2E"      # Burnt Orange
            self.icon_color = "#FFFFFF"
        elif state == "processing":
            self.bg_color = "#D4A017"      # Yellow Ochre
            self.icon_color = "#1C1C1C"
        elif state == "done":
            self.bg_color = "#1C1C1C"      # Charcoal Black
            self.icon_color = "#FFFFFF"
        elif state == "error":
            self.bg_color = "#B10000"      # Emergency red
            self.icon_color = "#FFFFFF"
        else:
            self.bg_color = "#8B3A2E"
            self.icon_color = "#FFFFFF"

        self._apply_state_style()
        self.update()

    def _apply_state_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.bg_color};
                border: none;
                border-radius: 130px;
            }}

            QPushButton:hover {{
                background-color: {self.bg_color};
                border: 6px solid rgba(242, 230, 216, 0.75);
            }}

            QPushButton:pressed {{
                border: 8px solid rgba(242, 230, 216, 0.95);
            }}

            QPushButton:disabled {{
                background-color: {self.bg_color};
            }}
        """)

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        pen = QPen(QColor(self.icon_color), 8)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        # Microphone icon
        painter.drawRoundedRect(108, 68, 44, 82, 22, 22)
        painter.drawArc(82, 108, 96, 92, 200 * 16, 140 * 16)
        painter.drawLine(130, 198, 130, 220)

        # Extra visual mark for states
        if self.state == "listening":
            pulse_pen = QPen(QColor("#F2E6D8"), 5)
            painter.setPen(pulse_pen)
            painter.drawEllipse(28, 28, 204, 204)

        elif self.state == "processing":
            painter.setPen(QPen(QColor("#1C1C1C"), 7))
            painter.drawArc(44, 44, 172, 172, 30 * 16, 270 * 16)

        elif self.state == "done":
            painter.setPen(QPen(QColor("#FFFFFF"), 10))
            painter.drawLine(82, 132, 114, 164)
            painter.drawLine(114, 164, 184, 92)

        elif self.state == "error":
            painter.setPen(QPen(QColor("#FFFFFF"), 10))
            painter.drawLine(92, 92, 168, 168)
            painter.drawLine(168, 92, 92, 168)


class InputPage(QWidget):
    back_clicked = Signal()
    emergency_clicked = Signal()
    submit_clicked = Signal(str)

    def __init__(self):
        super().__init__()

        self.strings = {}
        self.current_mode = "type"
        self._voice_worker = None

        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(0, 0, 0, 0)
        self.root.setSpacing(0)

        self.content = QWidget()
        self.content.setMinimumWidth(900)
        self.content.setMaximumWidth(900)

        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(20)

        self.root.addStretch(1)
        self.root.addWidget(self.content, alignment=Qt.AlignHCenter)
        self.root.addStretch(1)

        self.page_title = QLabel("Type Your Symptoms")
        self.page_title.setAlignment(Qt.AlignLeft)
        self.page_title.setStyleSheet("""
            QLabel {
                color: #0052A3;
                font-size: 36px;
                font-weight: 900;
                background: transparent;
                border: none;
            }
        """)
        self.content_layout.addWidget(self.page_title)

        self.mode_stack = QStackedWidget()
        self.mode_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.content_layout.addWidget(self.mode_stack)

        self.type_page = self._build_type_page()
        self.voice_page = self._build_voice_page()

        self.mode_stack.addWidget(self.type_page)
        self.mode_stack.addWidget(self.voice_page)

        # Bottom buttons
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
            }
        """)
        layout.addWidget(self.quick_label)

        layout.addSpacing(8)

        self.quick_area = QVBoxLayout()
        self.quick_area.setSpacing(12)

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
    # Speak page
    # --------------------------------------------------
    def _build_voice_page(self):
        page = QWidget()
        page.setFixedHeight(640)
        page.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignTop)

        self.voice_title = QLabel("What's wrong?")
        self.voice_title.setAlignment(Qt.AlignLeft)
        self.voice_title.setStyleSheet("""
            QLabel {
                color: #1C1C1C;
                font-size: 42px;
                font-weight: 900;
                background: transparent;
                border: none;
            }
        """)
        layout.addWidget(self.voice_title)

        self.voice_subtitle = QLabel("Tap and speak")
        self.voice_subtitle.setAlignment(Qt.AlignLeft)
        self.voice_subtitle.setStyleSheet("""
            QLabel {
                color: #7A6D62;
                font-size: 26px;
                font-weight: 800;
                background: transparent;
                border: none;
            }
        """)
        layout.addWidget(self.voice_subtitle)

        layout.addSpacing(30)

        mic_row = QHBoxLayout()
        mic_row.addStretch()

        self.mic_btn = MicCircleButton()
        self.mic_btn.clicked.connect(self._handle_mic_click)

        mic_row.addWidget(self.mic_btn)
        mic_row.addStretch()

        layout.addLayout(mic_row)

        layout.addSpacing(18)

        self.voice_status_label = QLabel("Tap the mic")
        self.voice_status_label.setAlignment(Qt.AlignCenter)
        self.voice_status_label.setStyleSheet("""
            QLabel {
                color: #3B302A;
                font-size: 28px;
                font-weight: 900;
                background: transparent;
                border: none;
            }
        """)
        layout.addWidget(self.voice_status_label)

        self.voice_helper_label = QLabel("")
        self.voice_helper_label.setAlignment(Qt.AlignCenter)
        self.voice_helper_label.setWordWrap(True)
        self.voice_helper_label.setStyleSheet("""
            QLabel {
                color: #8B3A2E;
                font-size: 17px;
                font-weight: 800;
                background: transparent;
                border: none;
            }
        """)
        layout.addWidget(self.voice_helper_label)

        layout.addSpacing(8)

        self.voice_text_box = QTextEdit()
        self.voice_text_box.setPlaceholderText("Your words will show here...")
        self.voice_text_box.setFixedHeight(150)
        self.voice_text_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.voice_text_box.setStyleSheet("""
            QTextEdit {
                background-color: rgba(242, 230, 216, 0.30);
                border: 3px dashed #D8C9BA;
                border-radius: 22px;
                padding: 22px 26px;
                color: #2D1810;
                font-size: 24px;
                font-weight: 700;
            }
            QTextEdit:focus {
                border: 3px dashed #8B3A2E;
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
    # Mic logic
    # --------------------------------------------------
    def _handle_mic_click(self):
        if self._voice_worker is not None and self._voice_worker.isRunning():
            return

        self.mic_btn.setEnabled(False)
        self.mic_btn.set_state("listening")

        self.voice_status_label.setText(
            "Lisin..." if self._is_kriol() else "Listening..."
        )
        self.voice_helper_label.setText(
            "Tok klia nau. Mi bai raitim yu wod." if self._is_kriol()
            else "Speak clearly now. Your words will appear below."
        )

        self.voice_text_box.setPlaceholderText(
            "Lisin nau..." if self._is_kriol() else "Listening now..."
        )

        self._voice_worker = InitialVoiceWorker(duration_seconds=5, whisper_model_name="small")
        self._voice_worker.status_changed.connect(self._on_voice_status)
        self._voice_worker.transcription_ready.connect(self._on_voice_text)
        self._voice_worker.error.connect(self._on_voice_error)
        self._voice_worker.finished.connect(self._on_voice_finished)
        self._voice_worker.start()

    def _on_voice_status(self, status: str):
        if status == "listening":
            self.mic_btn.set_state("listening")
            self.voice_status_label.setText(
                "Lisin..." if self._is_kriol() else "Listening..."
            )

        elif status == "processing":
            self.mic_btn.set_state("processing")
            self.voice_status_label.setText(
                "Wokabat..." if self._is_kriol() else "Processing..."
            )
            self.voice_helper_label.setText(
                "Wet liklik. Mi tanim yu vois." if self._is_kriol()
                else "Please wait. I am converting your voice."
            )

    def _on_voice_text(self, text: str):
        self.mic_btn.set_state("done")
        self.voice_status_label.setText(
            "Ansa bin faindim" if self._is_kriol() else "Voice detected"
        )
        self.voice_helper_label.setText(
            "Yu ken nekis, o tap maik gen." if self._is_kriol()
            else "You can continue, or tap the mic again."
        )

        self.voice_text_box.setPlainText(text)

        cursor = self.voice_text_box.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.voice_text_box.setTextCursor(cursor)

        self._update_next_button()

    def _on_voice_error(self, message: str):
        self.mic_btn.set_state("error")
        self.voice_status_label.setText(
            "Trai agen" if self._is_kriol() else "Try again"
        )
        self.voice_helper_label.setText(message)

    def _on_voice_finished(self):
        self.mic_btn.setEnabled(True)

        if self.mic_btn.state != "done" and self.mic_btn.state != "error":
            self.mic_btn.set_state("ready")

        self._voice_worker = None

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

            self.voice_helper_label.setText("")

            self.voice_text_box.setPlaceholderText(
                "Yu tok bai so iya..." if is_kriol else "Your words will show here..."
            )

            self.mic_btn.set_state("ready")

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

        if hasattr(self, "mic_btn"):
            self.mic_btn.set_state("ready")

        if hasattr(self, "voice_status_label"):
            self.voice_status_label.setText(
                "Tapim maik" if self._is_kriol() else "Tap the mic"
            )

        if hasattr(self, "voice_helper_label"):
            self.voice_helper_label.setText("")

        self._update_next_button()