import re
import tempfile
import threading
from pathlib import Path
from difflib import SequenceMatcher

from PySide6.QtCore import Signal, Qt, QThread
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QFrame,
    QProgressBar,
    QGridLayout,
    QSizePolicy,
)


# ==========================================================
# Voice answer worker
# Records short audio, transcribes with local Whisper,
# then returns text to the question page.
# ==========================================================
class QuestionVoiceWorker(QThread):
    status_changed = Signal(str)
    transcription_ready = Signal(str)
    error = Signal(str)

    def __init__(self, duration_seconds=4, whisper_model_name="small"):
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
                self.error.emit(
                    "Voice recording needs sounddevice and scipy. Run: pip install sounddevice scipy"
                )
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

            temp_path = Path(tempfile.gettempdir()) / "saca_question_voice.wav"
            write(str(temp_path), sample_rate, audio)

            try:
                import whisper
            except Exception:
                self.error.emit(
                    "Whisper is not installed. Run: pip install openai-whisper"
                )
                return

            model = whisper.load_model(self.whisper_model_name)
            result = model.transcribe(str(temp_path), fp16=False)
            text = (result.get("text") or "").strip()

            if not text:
                self.error.emit("I could not hear clearly. Please try again.")
                return

            self.transcription_ready.emit(text)

        except Exception as e:
            self.error.emit(str(e))


class QuestionsPage(QWidget):
    back_clicked = Signal()
    next_clicked = Signal(dict)
    emergency_clicked = Signal()

    def __init__(self):
        super().__init__()

        self.answers = {}
        self.questions = []
        self.current_index = 0
        self.strings = {}

        self.entry_mode = "type"
        self.auto_speak_enabled = False

        self._tts_thread = None
        self._voice_worker = None
        self._current_question_id = None

        root = QVBoxLayout(self)
        root.setContentsMargins(70, 34, 70, 40)
        root.setSpacing(24)

        # ---------- Top progress ----------
        top_row = QHBoxLayout()

        self.progress_label = QLabel("Question 1 of 1")
        self.progress_label.setStyleSheet("""
            font-size: 26px;
            font-weight: 900;
            color: #6B6B6B;
            background: transparent;
        """)

        self.percent_label = QLabel("0%")
        self.percent_label.setAlignment(Qt.AlignRight)
        self.percent_label.setStyleSheet("""
            font-size: 26px;
            font-weight: 900;
            color: #0052A3;
            background: transparent;
        """)

        top_row.addWidget(self.progress_label)
        top_row.addStretch()
        top_row.addWidget(self.percent_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMinimumHeight(18)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: #E5DED5;
                border: none;
                border-radius: 9px;
            }
            QProgressBar::chunk {
                background: #005BB8;
                border-radius: 9px;
            }
        """)

        root.addLayout(top_row)
        root.addWidget(self.progress_bar)

        # ---------- Summary ----------
        self.summary_label = QLabel("")
        self.summary_label.setAlignment(Qt.AlignCenter)
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("""
            font-size: 18px;
            font-weight: 700;
            color: #6B6B6B;
            background: transparent;
        """)

        root.addWidget(self.summary_label)

        # ---------- Normal question card ----------
        self.question_card = QFrame()
        self.question_card.setStyleSheet("""
            QFrame {
                background-color: rgba(255,255,255,0.92);
                border-radius: 28px;
                border: none;
            }
        """)

        question_layout = QVBoxLayout(self.question_card)
        question_layout.setContentsMargins(44, 38, 44, 38)
        question_layout.setSpacing(24)

        self.question_label = QLabel("")
        self.question_label.setAlignment(Qt.AlignCenter)
        self.question_label.setWordWrap(True)
        self.question_label.setStyleSheet("""
            font-size: 38px;
            font-weight: 900;
            color: #2D1810;
            background: transparent;
        """)

        # Speak-mode controls: speaker + mic
        self.voice_controls_row = QHBoxLayout()
        self.voice_controls_row.setSpacing(18)
        self.voice_controls_row.setAlignment(Qt.AlignCenter)

        self.speaker_btn = QPushButton("🔊  Hear question")
        self.speaker_btn.setCursor(Qt.PointingHandCursor)
        self.speaker_btn.setMinimumHeight(62)
        self.speaker_btn.setMinimumWidth(220)
        self.speaker_btn.clicked.connect(self._speak_current_question)
        self.speaker_btn.setStyleSheet("""
            QPushButton {
                background-color: #7A4A2A;
                color: white;
                border: none;
                border-radius: 18px;
                font-size: 19px;
                font-weight: 900;
                padding: 12px 20px;
            }
            QPushButton:hover {
                background-color: #663D22;
            }
        """)

        self.mic_btn = QPushButton("🎙️  Answer by voice")
        self.mic_btn.setCursor(Qt.PointingHandCursor)
        self.mic_btn.setMinimumHeight(62)
        self.mic_btn.setMinimumWidth(240)
        self.mic_btn.clicked.connect(self._start_voice_answer)
        self._set_mic_state("ready")

        self.voice_status_label = QLabel("")
        self.voice_status_label.setAlignment(Qt.AlignCenter)
        self.voice_status_label.setWordWrap(True)
        self.voice_status_label.setStyleSheet("""
            font-size: 17px;
            font-weight: 800;
            color: #6B6B6B;
            background: transparent;
        """)

        self.voice_controls_row.addWidget(self.speaker_btn)
        self.voice_controls_row.addWidget(self.mic_btn)

        self.options_grid = QGridLayout()
        self.options_grid.setHorizontalSpacing(18)
        self.options_grid.setVerticalSpacing(18)

        question_layout.addWidget(self.question_label)
        question_layout.addLayout(self.voice_controls_row)
        question_layout.addWidget(self.voice_status_label)
        question_layout.addLayout(self.options_grid)

        root.addWidget(self.question_card, 1)

        # ---------- Pain scale card ----------
        self.scale_card = QFrame()
        self.scale_card.setMaximumHeight(490)
        self.scale_card.setMinimumHeight(450)
        self.scale_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.scale_card.setStyleSheet("""
            QFrame {
                background-color: rgba(255,255,255,0.92);
                border-radius: 28px;
                border: none;
            }
        """)

        scale_layout = QVBoxLayout(self.scale_card)
        scale_layout.setContentsMargins(44, 34, 44, 30)
        scale_layout.setSpacing(0)
        scale_layout.setAlignment(Qt.AlignTop)

        self.scale_title = QLabel("How bad is the pain? (1–10)")
        self.scale_title.setAlignment(Qt.AlignCenter)
        self.scale_title.setWordWrap(True)
        self.scale_title.setStyleSheet("""
            font-size: 38px;
            font-weight: 900;
            color: #2D1810;
            background: transparent;
        """)

        self.scale_voice_controls_row = QHBoxLayout()
        self.scale_voice_controls_row.setSpacing(18)
        self.scale_voice_controls_row.setAlignment(Qt.AlignCenter)

        self.scale_speaker_btn = QPushButton("🔊  Hear question")
        self.scale_speaker_btn.setCursor(Qt.PointingHandCursor)
        self.scale_speaker_btn.setMinimumHeight(58)
        self.scale_speaker_btn.setMinimumWidth(220)
        self.scale_speaker_btn.clicked.connect(self._speak_current_question)
        self.scale_speaker_btn.setStyleSheet("""
            QPushButton {
                background-color: #7A4A2A;
                color: white;
                border: none;
                border-radius: 18px;
                font-size: 18px;
                font-weight: 900;
                padding: 10px 18px;
            }
            QPushButton:hover {
                background-color: #663D22;
            }
        """)

        self.scale_mic_btn = QPushButton("🎙️  Say number")
        self.scale_mic_btn.setCursor(Qt.PointingHandCursor)
        self.scale_mic_btn.setMinimumHeight(58)
        self.scale_mic_btn.setMinimumWidth(210)
        self.scale_mic_btn.clicked.connect(self._start_voice_answer)
        self._set_scale_mic_state("ready")

        self.scale_voice_status_label = QLabel("")
        self.scale_voice_status_label.setAlignment(Qt.AlignCenter)
        self.scale_voice_status_label.setWordWrap(True)
        self.scale_voice_status_label.setStyleSheet("""
            font-size: 16px;
            font-weight: 800;
            color: #6B6B6B;
            background: transparent;
        """)

        self.scale_voice_controls_row.addWidget(self.scale_speaker_btn)
        self.scale_voice_controls_row.addWidget(self.scale_mic_btn)

        self.scale_buttons_row = QHBoxLayout()
        self.scale_buttons_row.setSpacing(16)

        self.scale_buttons = []
        colors = [
            "#16A34A", "#22C55E", "#84CC16", "#EAB308", "#F59E0B",
            "#EA580C", "#EF4444", "#DC2626", "#B91C1C", "#991B1B"
        ]
        faces = ["☺", "☺", "☺", "😐", "😐", "😐", "☹", "☹", "☹", "☹"]

        for i in range(1, 11):
            btn = QPushButton(f"{faces[i - 1]}\n{i}")
            btn.setCheckable(True)
            btn.setMinimumHeight(132)
            btn.setMinimumWidth(86)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.clicked.connect(lambda checked, value=i: self._set_pain(value))
            self.scale_buttons.append(btn)
            self.scale_buttons_row.addWidget(btn)
            self._style_pain_button(btn, colors[i - 1], selected=False)

        labels_row = QHBoxLayout()
        labels_row.setContentsMargins(4, 0, 4, 0)
        labels_row.setSpacing(0)

        self.no_pain_label = QLabel("No pain")
        self.no_pain_label.setAlignment(Qt.AlignLeft)
        self.no_pain_label.setStyleSheet("""
            font-size: 22px;
            font-weight: 900;
            color: #6B6B6B;
            background: transparent;
            padding-left: 8px;
        """)

        self.worst_pain_label = QLabel("Worst pain")
        self.worst_pain_label.setAlignment(Qt.AlignRight)
        self.worst_pain_label.setStyleSheet("""
            font-size: 22px;
            font-weight: 900;
            color: #6B6B6B;
            background: transparent;
            padding-right: 8px;
        """)

        labels_row.addWidget(self.no_pain_label)
        labels_row.addStretch()
        labels_row.addWidget(self.worst_pain_label)

        scale_layout.addWidget(self.scale_title)
        scale_layout.addSpacing(18)
        scale_layout.addLayout(self.scale_voice_controls_row)
        scale_layout.addWidget(self.scale_voice_status_label)
        scale_layout.addSpacing(28)
        scale_layout.addLayout(self.scale_buttons_row)
        scale_layout.addSpacing(12)
        scale_layout.addLayout(labels_row)
        scale_layout.addStretch()

        root.addWidget(self.scale_card)

        # ---------- Bottom buttons ----------
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(18)

        self.back_btn = QPushButton("←  Back")
        self.skip_btn = QPushButton("Skip")
        self.emergency_btn = QPushButton("ⓘ  Emergency")
        self.next_btn = QPushButton("Next  →")

        for btn in [self.back_btn, self.skip_btn, self.emergency_btn, self.next_btn]:
            btn.setMinimumHeight(74)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setCursor(Qt.PointingHandCursor)

        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #0052A3;
                border: 3px solid #0052A3;
                border-radius: 18px;
                font-size: 22px;
                font-weight: 900;
                padding: 16px 20px;
            }
            QPushButton:hover { background-color: #EEF4FB; }
        """)

        self.skip_btn.setStyleSheet("""
            QPushButton {
                background-color: #F2ECE4;
                color: #7B5B46;
                border: 2px solid #D7CABC;
                border-radius: 18px;
                font-size: 22px;
                font-weight: 900;
                padding: 16px 20px;
            }
            QPushButton:hover { background-color: #ECE3D8; }
        """)

        self.emergency_btn.setStyleSheet("""
            QPushButton {
                background-color: #B10000;
                color: white;
                border: none;
                border-radius: 18px;
                font-size: 22px;
                font-weight: 900;
                padding: 16px 20px;
            }
            QPushButton:hover { background-color: #970000; }
        """)

        self.next_btn.setStyleSheet("""
            QPushButton {
                background-color: #0052A3;
                color: white;
                border: none;
                border-radius: 18px;
                font-size: 22px;
                font-weight: 900;
                padding: 16px 20px;
            }
            QPushButton:hover { background-color: #00468C; }
            QPushButton:disabled {
                background-color: #89A8CC;
                color: white;
            }
        """)

        bottom_row.addWidget(self.back_btn)
        bottom_row.addWidget(self.skip_btn)
        bottom_row.addWidget(self.emergency_btn)
        bottom_row.addWidget(self.next_btn)

        root.addLayout(bottom_row)

        self.back_btn.clicked.connect(self._handle_back)
        self.skip_btn.clicked.connect(self._handle_skip)
        self.emergency_btn.clicked.connect(self.emergency_clicked.emit)
        self.next_btn.clicked.connect(self._handle_next)

        self.answers["pain_scale"] = 3
        self.scale_card.hide()
        self._set_pain(3)

    # ==========================================================
    # Public mode methods
    # ==========================================================
    def set_entry_mode(self, mode: str):
        self.entry_mode = (mode or "type").lower()
        self.auto_speak_enabled = self.entry_mode == "voice"

    def set_input_mode(self, mode: str):
        self.set_entry_mode(mode)

    def set_mode(self, mode: str):
        self.set_entry_mode(mode)

    # ==========================================================
    # Language helpers
    # ==========================================================
    def _is_kriol_mode(self) -> bool:
        return self.strings.get("back", "Back").strip().lower() == "bek"

    def _t(self, en: str, kriol: str) -> str:
        return kriol if self._is_kriol_mode() else en

    def _translate_display_text(self, text: str) -> str:
        if not self._is_kriol_mode() or not text:
            return text

        display_map = {
            "breathing problem": "brithin trabul",
            "sore throat": self.strings.get("symptom_sore_throat", "Throt pein"),
            "stomach pain": self.strings.get("symptom_stomach_pain", "Beli pein"),
            "body pain": self.strings.get("symptom_body_pain", "Bodi pein"),
            "skin problem": self.strings.get("symptom_skin_problem", "Skin trabul"),
            "chest pain": self.strings.get("symptom_chest_pain", "Jes pein"),
            "headache": self.strings.get("symptom_headache", "Hedake"),
            "fever": self.strings.get("symptom_fever", "Fiba"),
            "cough": self.strings.get("symptom_cough", "Kof"),
            "dizzy": self.strings.get("symptom_dizzy", "Dizi"),
            "tired": self.strings.get("symptom_tired", "Taid"),
            "weak": "wik",
            "vomiting": "spyu",
            "diarrhea": "ranishit",
            "rash": "rash",
            "pain": "pein",
            "head": "hed",
            "chest": "jes",
            "stomach": "beli",
            "throat": "throt",
            "whole body": "hol bodi",
            "yes": "yuwai",
            "no": "nomu",
        }

        result = text
        for eng, kriol in sorted(display_map.items(), key=lambda x: len(x[0]), reverse=True):
            result = re.sub(rf"\b{re.escape(eng)}\b", kriol, result, flags=re.IGNORECASE)
        return result

    def _translate_question_text(self, text: str) -> str:
        if not self._is_kriol_mode():
            return text

        clean = (text or "").strip().lower()

        known = {
            "where is the problem?": "Wea im pein?",
            "where is the pain?": "Wea im pein?",
            "how long has this been happening?": "Hau long yu bin garr diswan?",
            "do you have fever?": "Yu garr fiba?",
            "do you have a fever?": "Yu garr fiba?",
            "are you coughing?": "Yu kof?",
            "do you have cough?": "Yu garr kof?",
            "are you feeling dizzy?": "Yu fil dizi?",
            "are you vomiting?": "Yu spyu?",
            "is it getting worse?": "Im kam moa nogud?",
        }

        if clean in known:
            return known[clean]

        return self._translate_display_text(text)

    # ==========================================================
    # Public UI update
    # ==========================================================
    def set_strings(self, s: dict):
        self.strings = s or {}
        is_kriol = self._is_kriol_mode()

        self.scale_title.setText(
            self.strings.get(
                "how_bad",
                "Hau nogud pein? (1–10)" if is_kriol else "How bad is the pain? (1–10)"
            )
        )
        self.no_pain_label.setText(
            self.strings.get("no_pain_label", "Nomo pein" if is_kriol else "No pain")
        )
        self.worst_pain_label.setText(
            self.strings.get("worst_pain_label", "Moj nogud pein" if is_kriol else "Worst pain")
        )
        self.back_btn.setText(self.strings.get("back", "Bek" if is_kriol else "←  Back"))
        self.skip_btn.setText(self.strings.get("skip", "Skipim" if is_kriol else "Skip"))
        self.emergency_btn.setText(
            self.strings.get("emergency", "🚨 Imijensi Elp" if is_kriol else "ⓘ  Emergency")
        )
        self.next_btn.setText(self.strings.get("next", "Nekis" if is_kriol else "Next  →"))

        self.speaker_btn.setText(
            "🔊  Lisin kweshin" if is_kriol else "🔊  Hear question"
        )
        self.mic_btn.setText(
            "🎙️  Ansa langa vois" if is_kriol else "🎙️  Answer by voice"
        )
        self.scale_speaker_btn.setText(
            "🔊  Lisin kweshin" if is_kriol else "🔊  Hear question"
        )
        self.scale_mic_btn.setText(
            "🎙️  Tok namba" if is_kriol else "🎙️  Say number"
        )

    def set_questions(self, original_text: str, english_meaning: str, questions: list):
        self.answers = {"pain_scale": self.answers.get("pain_scale", 3)}
        self.questions = questions or []
        self.current_index = 0
        self._current_question_id = None

        you_said = self.strings.get("you_said_label", "You said")
        english_meaning_label = self.strings.get("english_meaning_label", "English meaning")

        display_original = self._translate_display_text(original_text)
        display_meaning = self._translate_display_text(english_meaning)

        self.summary_label.setText(
            f"{you_said}: {display_original}   |   {english_meaning_label}: {display_meaning}"
        )

        self.question_card.show()
        self.scale_card.hide()
        self._render_current_question()

    # ==========================================================
    # Rendering
    # ==========================================================
    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _render_current_question(self):
        total_steps = len(self.questions) + 1
        current_step = min(self.current_index + 1, total_steps)
        percent = int((current_step / total_steps) * 100)

        progress_template = self.strings.get("question_progress", "Question {current} of {total}")
        self.progress_label.setText(progress_template.format(current=current_step, total=total_steps))
        self.percent_label.setText(f"{percent}%")
        self.progress_bar.setValue(percent)

        speak_mode = self.entry_mode == "voice"

        self.speaker_btn.setVisible(speak_mode)
        self.mic_btn.setVisible(speak_mode)
        self.voice_status_label.setVisible(speak_mode)

        self.scale_speaker_btn.setVisible(speak_mode)
        self.scale_mic_btn.setVisible(speak_mode)
        self.scale_voice_status_label.setVisible(speak_mode)

        self.voice_status_label.setText("")
        self.scale_voice_status_label.setText("")
        self._set_mic_state("ready")
        self._set_scale_mic_state("ready")

        if self.current_index >= len(self.questions):
            self.question_card.hide()
            self.scale_card.show()
            self.skip_btn.hide()
            self.next_btn.setText(self.strings.get("see_results", "See Results  →"))

            if speak_mode:
                self._auto_speak_current_question()

            return

        self.question_card.show()
        self.scale_card.hide()
        self.skip_btn.show()
        self.next_btn.setText(self.strings.get("next", "Next  →"))

        question = self.questions[self.current_index]
        self._current_question_id = question.get("id")
        display_text = self._translate_question_text(question.get("text", ""))
        self.question_label.setText(display_text)

        self._clear_layout(self.options_grid)

        options = question.get("options", [])
        for i, option in enumerate(options):
            row = i // 2
            col = i % 2
            btn = self._make_option_button(question["id"], option)
            self.options_grid.addWidget(btn, row, col)

        if speak_mode:
            self._auto_speak_current_question()

    def _make_option_button(self, question_id: str, value: str):
        display_value = self._translate_display_text(value)

        btn = QPushButton(display_value)
        btn.setProperty("answer_value", value)
        btn.setCheckable(True)
        btn.setMinimumHeight(86)
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #2D1810;
                border: 3px solid #D9D3CA;
                border-radius: 20px;
                font-size: 23px;
                font-weight: 900;
                padding: 16px 18px;
            }
            QPushButton:hover {
                background-color: #EEF4FB;
                border: 3px solid #0052A3;
            }
            QPushButton:checked {
                background-color: #0052A3;
                color: white;
                border: 3px solid #0052A3;
            }
        """)

        if self.answers.get(question_id) == value:
            btn.setChecked(True)

        btn.clicked.connect(lambda checked, qid=question_id, val=value: self._select_answer(qid, val))
        return btn

    def _select_answer(self, question_id: str, value: str):
        self.answers[question_id] = value
        self._render_current_question()

    # ==========================================================
    # Pain scale
    # ==========================================================
    def _style_pain_button(self, btn: QPushButton, color: str, selected: bool):
        border = "#0052A3" if selected else color
        border_width = "5px" if selected else "0px"
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: {border_width} solid {border};
                border-radius: 16px;
                font-size: 28px;
                font-weight: 900;
                padding: 10px;
            }}
            QPushButton:hover {{ border: 5px solid #0052A3; }}
        """)

    def _set_pain(self, value: int):
        self.answers["pain_scale"] = value
        colors = [
            "#16A34A", "#22C55E", "#84CC16", "#EAB308", "#F59E0B",
            "#EA580C", "#EF4444", "#DC2626", "#B91C1C", "#991B1B"
        ]

        for i, btn in enumerate(self.scale_buttons, start=1):
            btn.setChecked(i == value)
            self._style_pain_button(btn, colors[i - 1], selected=(i == value))

    # ==========================================================
    # Speaker / TTS
    # ==========================================================
    def _current_question_speech_text(self) -> str:
        if self.current_index >= len(self.questions):
            return self.scale_title.text()

        question = self.questions[self.current_index]
        return self._translate_question_text(question.get("text", ""))

    def _auto_speak_current_question(self):
        if not self.auto_speak_enabled:
            return

        self._speak_current_question()

    def _speak_current_question(self):
        text = self._current_question_speech_text()
        self._speak_text(text)

    def _speak_text(self, text: str):
        text = (text or "").strip()
        if not text:
            return

        # If a speech thread is already running, do not start another one.
        # This avoids repeated speaker clicks / auto-speak overlap.
        if self._tts_thread is not None and self._tts_thread.is_alive():
            return

        def speak_job():
            try:
                import pyttsx3

                engine = pyttsx3.init()
                engine.setProperty("rate", 150)
                engine.setProperty("volume", 1.0)

                # Kriol is spoken phonetically using available system voice.
                # English uses system default English voice.
                engine.say(text)
                engine.runAndWait()
                try:
                    engine.stop()
                except Exception:
                    pass
            except Exception as e:
                print(f"TTS error: {e}")

        self._tts_thread = threading.Thread(target=speak_job, daemon=True)
        self._tts_thread.start()

    # ==========================================================
    # Mic button state
    # ==========================================================
    def _set_mic_state(self, state: str):
        styles = {
            "ready": ("#0052A3", "🎙️  Answer by voice"),
            "listening": ("#E87912", "🎙️  Listening..."),
            "processing": ("#D4A017", "⏳  Processing..."),
            "done": ("#16803C", "✓  Answer detected"),
            "error": ("#B10000", "⚠ Try again"),
        }

        color, text = styles.get(state, styles["ready"])
        if self._is_kriol_mode():
            text_map = {
                "ready": "🎙️  Ansa langa vois",
                "listening": "🎙️  Lisin...",
                "processing": "⏳  Wokabat...",
                "done": "✓  Ansa bin faindim",
                "error": "⚠ Trai agen",
            }
            text = text_map.get(state, text)

        self.mic_btn.setText(text)
        self.mic_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 18px;
                font-size: 19px;
                font-weight: 900;
                padding: 12px 20px;
            }}
            QPushButton:hover {{
                background-color: {color};
            }}
        """)

    def _set_scale_mic_state(self, state: str):
        styles = {
            "ready": ("#0052A3", "🎙️  Say number"),
            "listening": ("#E87912", "🎙️  Listening..."),
            "processing": ("#D4A017", "⏳  Processing..."),
            "done": ("#16803C", "✓  Number detected"),
            "error": ("#B10000", "⚠ Try again"),
        }

        color, text = styles.get(state, styles["ready"])
        if self._is_kriol_mode():
            text_map = {
                "ready": "🎙️  Tok namba",
                "listening": "🎙️  Lisin...",
                "processing": "⏳  Wokabat...",
                "done": "✓  Namba bin faindim",
                "error": "⚠ Trai agen",
            }
            text = text_map.get(state, text)

        self.scale_mic_btn.setText(text)
        self.scale_mic_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 18px;
                font-size: 18px;
                font-weight: 900;
                padding: 10px 18px;
            }}
            QPushButton:hover {{
                background-color: {color};
            }}
        """)

    # ==========================================================
    # Voice answer processing
    # ==========================================================
    def _start_voice_answer(self):
        if self.entry_mode != "voice":
            return

        if self._voice_worker is not None and self._voice_worker.isRunning():
            return

        self._set_mic_state("listening")
        self._set_scale_mic_state("listening")

        if self.current_index >= len(self.questions):
            self.scale_voice_status_label.setText(
                self._t("Say a number from one to ten.", "Tok namba wan to ten.")
            )
        else:
            self.voice_status_label.setText(
                self._t("Speak your answer now.", "Tok yu ansa nau.")
            )

        self._voice_worker = QuestionVoiceWorker(duration_seconds=4, whisper_model_name="small")
        self._voice_worker.status_changed.connect(self._on_voice_status)
        self._voice_worker.transcription_ready.connect(self._on_voice_transcription)
        self._voice_worker.error.connect(self._on_voice_error)
        self._voice_worker.finished.connect(self._on_voice_finished)
        self._voice_worker.start()

    def _on_voice_status(self, status: str):
        if status == "listening":
            self._set_mic_state("listening")
            self._set_scale_mic_state("listening")
        elif status == "processing":
            self._set_mic_state("processing")
            self._set_scale_mic_state("processing")
            if self.current_index >= len(self.questions):
                self.scale_voice_status_label.setText(
                    self._t("Processing your voice...", "Wokabat langa yu vois...")
                )
            else:
                self.voice_status_label.setText(
                    self._t("Processing your voice...", "Wokabat langa yu vois...")
                )

    def _on_voice_transcription(self, text: str):
        text = (text or "").strip()

        if self.current_index >= len(self.questions):
            matched = self._match_pain_number(text)
            if matched is None:
                self._set_scale_mic_state("error")
                self.scale_voice_status_label.setText(
                    self._t(
                        f'I heard: "{text}". Please say a number from 1 to 10.',
                        f'I bin lisen: "{text}". Plis tok namba 1 to 10.'
                    )
                )
                return

            self._set_pain(matched)
            self._set_scale_mic_state("done")
            self.scale_voice_status_label.setText(
                self._t(
                    f'I heard: "{text}" → selected {matched}.',
                    f'I bin lisen: "{text}" → jusim {matched}.'
                )
            )
            return

        question = self.questions[self.current_index]
        question_id = question.get("id")
        options = question.get("options", [])

        matched_option = self._match_option_from_speech(text, options)

        if matched_option is None:
            self._set_mic_state("error")
            self.voice_status_label.setText(
                self._t(
                    f'I heard: "{text}". Please try again or tap an option.',
                    f'I bin lisen: "{text}". Trai agen o tap wan opshan.'
                )
            )
            return

        self.answers[question_id] = matched_option
        self._set_mic_state("done")
        self.voice_status_label.setText(
            self._t(
                f'I heard: "{text}" → selected "{self._translate_display_text(matched_option)}".',
                f'I bin lisen: "{text}" → jusim "{self._translate_display_text(matched_option)}".'
            )
        )
        self._render_current_question()

    def _on_voice_error(self, message: str):
        self._set_mic_state("error")
        self._set_scale_mic_state("error")

        if self.current_index >= len(self.questions):
            self.scale_voice_status_label.setText(message)
        else:
            self.voice_status_label.setText(message)

    def _on_voice_finished(self):
        self._voice_worker = None

    def _match_pain_number(self, text: str):
        clean = self._normalise_text(text)

        word_to_number = {
            "one": 1, "wan": 1,
            "two": 2, "too": 2, "tu": 2,
            "three": 3, "tree": 3,
            "four": 4, "for": 4,
            "five": 5,
            "six": 6,
            "seven": 7,
            "eight": 8, "ate": 8,
            "nine": 9,
            "ten": 10,
        }

        for i in range(1, 11):
            if re.search(rf"\b{i}\b", clean):
                return i

        for word, number in word_to_number.items():
            if re.search(rf"\b{word}\b", clean):
                return number

        return None

    def _match_option_from_speech(self, speech_text: str, options: list):
        speech_clean = self._normalise_text(speech_text)

        yes_words = {"yes", "yeah", "yep", "yup", "ha", "yuwai", "correct"}
        no_words = {"no", "nah", "nope", "nomu", "not"}

        if any(word in speech_clean.split() for word in yes_words):
            for option in options:
                if self._normalise_text(option) in {"yes", "yuwai"}:
                    return option
                if "yes" in self._normalise_text(option):
                    return option

        if any(word in speech_clean.split() for word in no_words):
            for option in options:
                if self._normalise_text(option) in {"no", "nomu"}:
                    return option
                if "no" in self._normalise_text(option):
                    return option

        best_option = None
        best_score = 0.0

        for option in options:
            option_clean = self._normalise_text(option)
            option_display_clean = self._normalise_text(self._translate_display_text(option))

            if option_clean and option_clean in speech_clean:
                return option

            if option_display_clean and option_display_clean in speech_clean:
                return option

            score_1 = SequenceMatcher(None, speech_clean, option_clean).ratio()
            score_2 = SequenceMatcher(None, speech_clean, option_display_clean).ratio()
            score = max(score_1, score_2)

            if score > best_score:
                best_score = score
                best_option = option

        if best_score >= 0.55:
            return best_option

        return None

    def _normalise_text(self, text: str) -> str:
        text = (text or "").lower().strip()
        text = text.replace("’", "'")
        text = re.sub(r"[^a-zA-Z0-9\s']", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    # ==========================================================
    # Navigation
    # ==========================================================
    def _handle_back(self):
        if self.current_index == 0:
            self.back_clicked.emit()
            return

        self.current_index -= 1
        self._render_current_question()

    def _handle_skip(self):
        if self.current_index < len(self.questions):
            self.current_index += 1
            self._render_current_question()

    def _handle_next(self):
        if self.current_index < len(self.questions):
            question = self.questions[self.current_index]
            if question["id"] not in self.answers:
                return

            self.current_index += 1
            self._render_current_question()
            return

        self.next_clicked.emit(self.answers)