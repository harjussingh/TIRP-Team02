import re
import tempfile
import threading
from pathlib import Path
from difflib import SequenceMatcher

from PySide6.QtCore import Signal, Qt, QThread, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QColor, QLinearGradient
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
    QScrollArea,
    QGraphicsOpacityEffect,
)
from src.ui.widgets.help_popup import HelpButton
from src.utils.audio import play_sequence as _play_sequence, stop_all as _stop_all

# Kriol transcription corrector
try:
    import os as _os
    from nlp.kriol_translator import correct_kriol_transcription as _correct_kriol, load_kriol_dictionary as _load_kriol_dict
    _KRIOL_DICT_PATH = _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "data", "kriol_dictionary.json"))
    _KRIOL_DICT = _load_kriol_dict(_KRIOL_DICT_PATH)
except Exception:
    _correct_kriol = None
    _KRIOL_DICT = {}


# ==========================================================
# Voice answer worker
# Records short audio, transcribes with local Whisper,
# then returns text to the question page.
# ==========================================================
class QuestionVoiceWorker(QThread):
    status_changed = Signal(str)
    transcription_ready = Signal(str)
    error = Signal(str)

    def __init__(self, duration_seconds=4, whisper_model_name="small", is_kriol=False):
        super().__init__()
        self.duration_seconds = duration_seconds
        self.whisper_model_name = whisper_model_name
        self.is_kriol = is_kriol

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
            _KRIOL_PROMPT = (
                "Mi garra fiva. Mi garra beli pen. Mi garra hedek. Mi garra kof. "
                "Mi garra soa trot. Mi garra wota nos. Mi garra ches pen. "
                "Mi no ken brij. Mi gidibat. Mi fil sik. Yuwai. Nomu."
            )
            transcribe_kwargs = dict(fp16=False)
            if self.is_kriol:
                transcribe_kwargs["initial_prompt"] = _KRIOL_PROMPT
            else:
                transcribe_kwargs["language"] = "en"
            result = model.transcribe(str(temp_path), **transcribe_kwargs)
            text = (result.get("text") or "").strip()

            if not text:
                self.error.emit("I could not hear clearly. Please try again.")
                return

            # Apply Kriol phonetic correction when in Kriol mode

            self.transcription_ready.emit(text)

        except Exception as e:
            self.error.emit(str(e))


# Simple alias — no broken graphics effect
_AnimatedButton = QPushButton


class _HeroPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(260)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, QColor("#8B3A2E"))
        grad.setColorAt(1.0, QColor("#5A1F16"))
        p.fillRect(0, 0, w, h, grad)
        for cx, cy, r, alpha in [(230, 70, 80, 18), (30, 380, 110, 12), (160, 560, 55, 10)]:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(255, 255, 255, alpha))
            p.drawEllipse(int(cx - r), int(cy - r), int(r * 2), int(r * 2))
        p.setBrush(QColor("#D4A017"))
        p.drawRect(0, h - 6, w, 6)


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
        self._is_first_question_shown = True  # reset each time set_questions is called

        # ── Outer split: hero (left) + content (right) ────────────────────
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Hero panel ────────────────────────────────────────────────────
        self._hero = _HeroPanel()
        hero_layout = QVBoxLayout(self._hero)
        hero_layout.setContentsMargins(30, 44, 22, 36)
        hero_layout.setSpacing(0)
        hero_layout.setAlignment(Qt.AlignTop)

        self._hero_title = QLabel("Follow-up\nquestions")
        self._hero_title.setWordWrap(True)
        self._hero_title.setStyleSheet(
            "font-size:30px; font-weight:900; color:#FFFFFF; background:transparent;"
        )
        self._hero_tag = QLabel("Help us understand\nyour symptoms better")
        self._hero_tag.setWordWrap(True)
        self._hero_tag.setStyleSheet(
            "font-size:15px; font-weight:700; color:rgba(255,255,255,0.80);"
            " background:transparent;"
        )

        # Progress indicators in hero
        self.progress_label = QLabel("Question 1 of 1")
        self.progress_label.setWordWrap(True)
        self.progress_label.setStyleSheet(
            "font-size:13px; font-weight:800; color:rgba(255,255,255,0.70);"
            " background:transparent;"
        )
        self.percent_label = QLabel("0%")
        self.percent_label.setStyleSheet(
            "font-size:28px; font-weight:900; color:#FFFFFF; background:transparent;"
        )
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet("""
            QProgressBar { background:rgba(255,255,255,0.25); border:none; border-radius:3px; }
            QProgressBar::chunk { background:#D4A017; border-radius:3px; }
        """)

        # Summary (what user said)
        self.summary_label = QLabel("")
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet(
            "font-size:12px; font-weight:700; color:rgba(255,255,255,0.65);"
            " background:transparent;"
        )

        hero_layout.addStretch(1)
        hero_layout.addWidget(self._hero_title)
        hero_layout.addSpacing(10)
        hero_layout.addWidget(self._hero_tag)
        hero_layout.addSpacing(24)
        hero_layout.addWidget(self.percent_label)
        hero_layout.addSpacing(6)
        hero_layout.addWidget(self.progress_bar)
        hero_layout.addSpacing(4)
        hero_layout.addWidget(self.progress_label)
        hero_layout.addSpacing(20)
        hero_layout.addWidget(self.summary_label)
        hero_layout.addStretch(2)
        dot_row = QHBoxLayout()
        for c in ["#D4A017", "#C65D2E", "#F2E6D8"]:
            dot = QFrame(); dot.setFixedSize(10, 10)
            dot.setStyleSheet(f"background:{c}; border-radius:5px;")
            dot_row.addWidget(dot)
        dot_row.addStretch()
        hero_layout.addLayout(dot_row)
        outer.addWidget(self._hero)

        # ── Right content panel ───────────────────────────────────────────
        right = QWidget()
        right.setObjectName("qPageRight")
        right.setStyleSheet("QWidget#qPageRight { background:#FDF6F0; }")
        right.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        root = QVBoxLayout(right)
        root.setContentsMargins(48, 32, 48, 28)
        root.setSpacing(20)

        outer.addWidget(right)

        # ---------- Normal question card ----------
        self.question_card = QFrame()
        self.question_card.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
            }
        """)

        question_layout = QVBoxLayout(self.question_card)
        question_layout.setContentsMargins(32, 28, 32, 28)
        question_layout.setSpacing(18)

        self.question_label = QLabel("")
        self.question_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.question_label.setWordWrap(True)
        self.question_label.setStyleSheet("""
            font-size: 52px;
            font-weight: 900;
            color: #3D1F14;
            background: transparent;
            padding-bottom: 4px;
        """)

        # Speak-mode controls: speaker + mic
        self.voice_controls_row = QHBoxLayout()
        self.voice_controls_row.setSpacing(18)
        self.voice_controls_row.setAlignment(Qt.AlignCenter)

        self.speaker_btn = QPushButton("🔊  Hear question again")
        self.speaker_btn.setCursor(Qt.PointingHandCursor)
        self.speaker_btn.setMinimumHeight(62)
        self.speaker_btn.setMinimumWidth(220)
        self.speaker_btn.clicked.connect(self._speak_current_question)
        self.speaker_btn.setStyleSheet("""
            QPushButton {
                background-color: #8B3A2E;
                color: white;
                border: none;
                border-radius: 14px;
                font-size: 16px;
                font-weight: 900;
                padding: 10px 18px;
            }
            QPushButton:hover {
                background-color: #6B2A1E;
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

        # Speak-mode buttons stay under the question
        question_layout.addLayout(self.voice_controls_row)
        question_layout.addWidget(self.voice_status_label)

        #Thin red accent divider stays above Yes/No options
        _divider = QFrame()
        _divider.setFixedHeight(3)
        _divider.setStyleSheet(
        "background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #8B3A2E, stop:1 transparent); "
        "border:none; border-radius:2px;"
        )
        question_layout.addWidget(_divider)
    
        question_layout.addLayout(self.options_grid)
        # ---------- Top bar: pill back button ----------
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 8)
        self.back_btn = QPushButton("← Back")
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.setFixedHeight(40)
        self.back_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(139,58,46,0.10);
                color: #8B3A2E;
                border: 2px solid #8B3A2E;
                border-radius: 20px;
                font-size: 14px;
                font-weight: 800;
                padding: 6px 22px;
            }
            QPushButton:hover { background-color: rgba(139,58,46,0.20); }
        """)
        self._help_btn = HelpButton(
            en_title="Follow-up Questions",
            en_text="We have a few questions to better understand your symptoms.\n\n"
                    "• Read each question carefully and choose the best answer.\n"
                    "• Use the pain scale (1–10) to rate how bad the pain is.\n"
                    "• In voice mode, press the speaker button to hear the question.\n\n"
                    "Press Next after each answer. You can press Back to go to the previous question.",
            kr_title="Moa Kwestin",
            kr_text="Mibala garrim sampela kwestin blong andastandim beta yu simptom.\n\n"
                    "• Ridum ich kwestin klin en jusum bes ansa.\n"
                    "• Yusum pein skeil (1–10) blong shoim hau nogud pein.\n"
                    "• Langa vois mod, pres spika batn blong hia kwestin.\n\n"
                    "Pres Nekis afta ich ansa. Yu ken pres Bek blong go bek long bifoa kwestin.",
        )
        top_bar.addWidget(self.back_btn)
        top_bar.addStretch()
        top_bar.addWidget(self._help_btn)
        root.insertLayout(0, top_bar)

        root.addWidget(self.question_card, 1)

        # ---------- Pain scale card ----------
        self.scale_card = QFrame()
        self.scale_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scale_card.setStyleSheet("QFrame { background-color: transparent; border: none; }")

        scale_layout = QVBoxLayout(self.scale_card)
        scale_layout.setContentsMargins(32, 16, 32, 16)
        scale_layout.setSpacing(0)
        scale_layout.setAlignment(Qt.AlignTop)

        self.scale_title = QLabel("How bad is the pain?")
        self.scale_title.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.scale_title.setWordWrap(True)
        self.scale_title.setMinimumHeight(165)
        self.scale_title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.scale_title.setStyleSheet("""
            font-size: 52px;
            font-weight: 900;
            color: #3D1F14;
            background: transparent;
        """)
        scale_layout.addWidget(self.scale_title)
        scale_layout.addSpacing(8)

        # Voice controls (speak-mode only)
        self.scale_voice_controls_row = QHBoxLayout()
        self.scale_voice_controls_row.setSpacing(18)
        self.scale_voice_controls_row.setAlignment(Qt.AlignLeft)

        self.scale_speaker_btn = QPushButton("🔊  Hear question again")
        self.scale_speaker_btn.setCursor(Qt.PointingHandCursor)
        self.scale_speaker_btn.setMinimumHeight(48)
        self.scale_speaker_btn.setMinimumWidth(200)
        self.scale_speaker_btn.clicked.connect(self._speak_current_question)
        self.scale_speaker_btn.setStyleSheet("""
            QPushButton {
                background-color: #8B3A2E;
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 900;
                padding: 8px 16px;
            }
            QPushButton:hover { background-color: #6B2A1E; }
        """)

        self.scale_mic_btn = QPushButton("🎙️  Say number")
        self.scale_mic_btn.setCursor(Qt.PointingHandCursor)
        self.scale_mic_btn.setMinimumHeight(48)
        self.scale_mic_btn.setMinimumWidth(190)
        self.scale_mic_btn.clicked.connect(self._start_voice_answer)
        self._set_scale_mic_state("ready")

        self.scale_voice_status_label = QLabel("")
        self.scale_voice_status_label.setAlignment(Qt.AlignCenter)
        self.scale_voice_status_label.setWordWrap(True)
        self.scale_voice_status_label.setStyleSheet("""
            font-size: 14px; font-weight: 800;
            color: #6B6B6B; background: transparent;
        """)

        self.scale_voice_controls_row.addWidget(self.scale_speaker_btn)
        self.scale_voice_controls_row.addWidget(self.scale_mic_btn)
        scale_layout.addLayout(self.scale_voice_controls_row)
        scale_layout.addWidget(self.scale_voice_status_label)
        scale_layout.addSpacing(16)

        # ---- Pain scale data ----
        self._pain_colors = [
            "#16A34A", "#22C55E", "#84CC16", "#EAB308", "#F59E0B",
            "#F97316", "#EF4444", "#DC2626", "#B91C1C", "#7F1D1D"
        ]
        self._pain_labels = [
            "😊", "🙂", "😐", "😕", "😟",
            "😣", "😖", "😫", "😩", "😭"
        ]
        self._pain_explanations = [
            "You feel no pain at all.",
            "Very slight, barely noticeable.",
            "Noticeable but you can still function.",
            "Distracting but manageable.",
            "Affects concentration and daily tasks.",
            "Cannot be ignored; hard to concentrate.",
            "Severe pain dominating your senses.",
            "Intense pain limiting all activity.",
            "Excruciating; unable to speak fully.",
            "Unbearable; completely debilitating.",
        ]

        # --- Row 1: cards 1–5 ---
        self.scale_buttons = []
        self.scale_buttons_row = QHBoxLayout()   # stub kept for compatibility

        for row_cards in [(1, 6), (6, 11)]:
            row_widget = QWidget()
            row_widget.setStyleSheet("background: transparent;")
            row_widget.setFixedHeight(82)
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(14)
            for i in range(row_cards[0], row_cards[1]):
                color = self._pain_colors[i - 1]
                lbl   = self._pain_labels[i - 1]
                btn = QPushButton()
                btn.setCheckable(True)
                btn.setCursor(Qt.PointingHandCursor)
                btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                btn.setFixedHeight(78)
                btn.setText(f"{self._pain_labels[i - 1]}\n{i}")
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {color};
                        color: white;
                        border: none;
                        border-radius: 12px;
                        font-size: 22px;
                        font-weight: 800;
                        padding: 4px 4px;
                    }}
                    QPushButton:hover {{
                        border: 3px solid rgba(0,0,0,0.35);
                    }}
                    QPushButton:checked {{
                        border: 4px solid #1A0A05;
                    }}
                """)
                btn.clicked.connect(lambda checked, v=i: self._set_pain(v))
                self.scale_buttons.append(btn)
                row_layout.addWidget(btn)
            scale_layout.addWidget(row_widget)
            scale_layout.addSpacing(18)

        scale_layout.addSpacing(32)

        # --- Elevated selection info card ---
        self.pain_info_card = QFrame()
        self.pain_info_card.setObjectName("painInfoCard")
        self.pain_info_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.pain_info_card.setMinimumHeight(72)
        pain_info_h = QHBoxLayout(self.pain_info_card)
        pain_info_h.setContentsMargins(20, 14, 20, 14)
        pain_info_h.setSpacing(12)

        pain_text_col = QVBoxLayout()
        pain_text_col.setContentsMargins(0, 0, 0, 0)
        pain_text_col.setSpacing(2)

        self._pain_selected_header = QLabel("You selected:")
        self._pain_selected_header.setStyleSheet(
            "font-size: 12px; font-weight: 700; color: #888; background: transparent;"
        )
        self._pain_level_label = QLabel("Level 3 — Mild")
        self._pain_level_label.setStyleSheet(
            "font-size: 18px; font-weight: 900; color: #3D1F14; background: transparent;"
        )
        pain_text_col.addWidget(self._pain_selected_header)
        pain_text_col.addWidget(self._pain_level_label)
        pain_info_h.addLayout(pain_text_col)
        pain_info_h.addStretch()

        self._pain_emoji_label = QLabel("😐")
        self._pain_emoji_label.setAlignment(Qt.AlignCenter)
        self._pain_emoji_label.setStyleSheet(
            "font-size: 36px; background: transparent;"
        )
        pain_info_h.addWidget(self._pain_emoji_label)

        # hidden stubs no longer needed
        self._pain_badge = QLabel(); self._pain_badge.hide()
        self._pain_desc_label = QLabel(); self._pain_desc_label.hide()

        self.pain_info_card.setStyleSheet("""
            QFrame#painInfoCard {
                background: white;
                border: 2px solid #CBD5E1;
                border-radius: 14px;
            }
        """)
        scale_layout.addWidget(self.pain_info_card)
        scale_layout.addSpacing(20)

        # Hidden stubs for set_strings compatibility
        self.no_pain_label = QLabel("No pain"); self.no_pain_label.hide()
        self.worst_pain_label = QLabel("Worst pain"); self.worst_pain_label.hide()
        self.pain_display_label = QLabel(""); self.pain_display_label.hide()

        self.see_results_btn = QPushButton("See Results  →")
        self.see_results_btn.setCursor(Qt.PointingHandCursor)
        self.see_results_btn.setFixedHeight(54)
        self.see_results_btn.setStyleSheet("""
            QPushButton {
                background-color: #8B3A2E;
                color: white;
                border: none;
                border-radius: 14px;
                font-size: 17px;
                font-weight: 900;
                padding: 10px 24px;
            }
            QPushButton:hover { background-color: #6B2A1E; }
        """)
        self.see_results_btn.clicked.connect(self._handle_next)
        scale_layout.addWidget(self.see_results_btn)
        scale_layout.addStretch()

        root.addWidget(self.scale_card)

        # ---------- Bottom bar: emergency only ----------
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(12)

        self.emergency_btn = QPushButton("🚨  Emergency")
        self.emergency_btn.setMinimumHeight(46)
        self.emergency_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.emergency_btn.setCursor(Qt.PointingHandCursor)
        self.emergency_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #8B3A2E;
                border: none;
                border-radius: 14px;
                font-size: 14px;
                font-weight: 800;
                padding: 8px 16px;
                text-decoration: underline;
            }
            QPushButton:hover { color: #5A1F16; }
        """)
        bottom_row.addWidget(self.emergency_btn)
        root.addLayout(bottom_row)

        self.back_btn.clicked.connect(self._handle_back)
        self.emergency_btn.clicked.connect(self.emergency_clicked.emit)

        self.answers["pain_scale"] = 3
        self.scale_card.hide()
        self._set_pain(3)

    # ==========================================================
    # Public mode methods
    # ==========================================================
    def set_entry_mode(self, mode: str):
        mode = (mode or "type").lower().strip()

        # Normalise all possible names used by the app for Speak mode.
        # This keeps the voice buttons hidden in Type/Picture mode and visible only in Speak mode.
        if mode in {"speak", "speech", "mic", "microphone"}:
            mode = "voice"

        self.entry_mode = mode
        self.auto_speak_enabled = self._is_speak_mode()

    def set_input_mode(self, mode: str):
        self.set_entry_mode(mode)

    def set_mode(self, mode: str):
        self.set_entry_mode(mode)

    def _is_speak_mode(self) -> bool:
        return self.entry_mode in {"voice", "speak", "speech", "mic", "microphone"}

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
        self._help_btn.set_kriol(is_kriol)

        self._hero_title.setText(
            "Moa\nkwestin" if is_kriol else "Follow-up\nquestions"
        )
        self._hero_tag.setText(
            "Helpim mibala\nandastandim\nyu simptom" if is_kriol
            else "Help us understand\nyour symptoms better"
        )

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
        self.back_btn.setText("← " + self.strings.get("back", "Bek" if is_kriol else "Back"))
        self.emergency_btn.setText(
            self.strings.get("emergency", "🚨 Imijensi Elp" if is_kriol else "🚨  Emergency")
        )
        self.see_results_btn.setText(
            self.strings.get("see_results", "Luk Rizalts  →" if is_kriol else "See Results  →")
        )

        self.speaker_btn.setText(
            "🔊  Lisin kweshin agen" if is_kriol else "🔊  Hear question again"
        )
        self.mic_btn.setText(
            "🎙️  Ansa langa vois" if is_kriol else "🎙️  Answer by voice"
        )
        self.scale_speaker_btn.setText(
            "🔊  Lisin kweshin agen" if is_kriol else "🔊  Hear question again"
        )
        self.scale_mic_btn.setText(
            "🎙️  Tok namba" if is_kriol else "🎙️  Say number"
        )
        self._pain_selected_header.setText(
            "Yu jusum:" if is_kriol else "You selected:"
        )
        # Refresh progress label so it shows in the right language immediately
        progress_template = self.strings.get(
            "question_progress",
            "Kwestin {current} long {total}" if is_kriol else "Question {current} of {total}"
        )
        total_steps = max(len(self.questions) + 1, 1)
        current_step = min(self.current_index + 1, total_steps)
        self.progress_label.setText(progress_template.format(current=current_step, total=total_steps))

    def set_questions(self, original_text: str, english_meaning: str, questions: list):
        self.answers = {"pain_scale": self.answers.get("pain_scale", 3)}
        self.questions = questions or []
        self.current_index = 0
        self._current_question_id = None
        self._is_first_question_shown = True

        you_said = self.strings.get("you_said_label", "You said")
        display_original = self._translate_display_text(original_text)
        self.summary_label.setText(f"{you_said}:\n\"{display_original}\"")

        self.question_card.show()
        self.question_card.setGraphicsEffect(None)
        self.scale_card.hide()
        self._render_current_question()



    
    def _apply_scale_title_layout(self, speak_mode: bool):
        """
        Only fixes pain-scale title layout in Speak/Voice mode.
        This prevents 'How bad is your problem?' from hiding behind
        the Hear question / Say number buttons.
        """
        if speak_mode:
            self.scale_title.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            self.scale_title.setWordWrap(True)
            self.scale_title.setFixedHeight(170)
            self.scale_title.setStyleSheet("""
            font-size: 48px;
            font-weight: 900;
            color: #3D1F14;
            background: transparent;
            """)
        else:
            # Fix only Type/Picture mode title spacing
            # This gives enough height for "How bad is your problem?" when it wraps to 2 lines.
            self.scale_title.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            self.scale_title.setWordWrap(True)
            self.scale_title.setFixedHeight(155)
            self.scale_title.setStyleSheet("""
            font-size: 52px;
            font-weight: 900;
            color: #3D1F14;
            background: transparent;
            """)
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

        _default_progress = "Kwestin {current} long {total}" if self._is_kriol_mode() else "Question {current} of {total}"
        progress_template = self.strings.get("question_progress", _default_progress)
        self.progress_label.setText(progress_template.format(current=current_step, total=total_steps))
        self.percent_label.setText(f"{percent}%")
        self.progress_bar.setValue(percent)

        speak_mode = self._is_speak_mode()  # show voice controls only in Speak mode
        self._apply_scale_title_layout(speak_mode)

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
            self._crossfade(self.question_card, self.scale_card)
            if speak_mode:
                QTimer.singleShot(520, self._speak_rating_page)
            return

        question = self.questions[self.current_index]
        self._current_question_id = question.get("id")
        display_text = self._translate_question_text(question.get("text", ""))

        def _update():
            self.question_label.setText(display_text)
            self._clear_layout(self.options_grid)
            options = question.get("options", [])
            for i, option in enumerate(options):
                row = i // 2
                col = i % 2
                btn = self._make_option_button(question["id"], option)
                self.options_grid.addWidget(btn, row, col)

        if self.scale_card.isVisible():
            self._crossfade(self.scale_card, self.question_card, between_fn=_update)
        else:
            self._fade_widget(self.question_card, out=True, done=lambda: (
                _update(),
                self._fade_widget(self.question_card, out=False)
            ))

        if speak_mode:
            QTimer.singleShot(520, self._auto_speak_current_question)

    # ------------------------------------------------------------------
    # Fade helpers
    # ------------------------------------------------------------------
    _FADE_STEPS    = 10
    _FADE_INTERVAL = 18   # ms

    def _fade_widget(self, widget: QWidget, out: bool, done=None, _step: int = 0, _fx=None):
        """Fade a single widget in (out=False) or out (out=True).
        _fx is created on first call and passed through every recursive step
        so there is no shared state between concurrent animations."""
        steps = self._FADE_STEPS

        # First call: create a fresh effect and attach it
        if _step == 0:
            _fx = QGraphicsOpacityEffect(widget)
            _fx.setOpacity(1.0 if out else 0.0)
            widget.setGraphicsEffect(_fx)
            widget.show()

        op = (1.0 - _step / steps) if out else (_step / steps)
        _fx.setOpacity(max(0.0, min(1.0, op)))

        if _step >= steps:
            if out:
                widget.hide()
            widget.setGraphicsEffect(None)
            if done:
                done()
            return

        QTimer.singleShot(
            self._FADE_INTERVAL,
            lambda: self._fade_widget(widget, out, done, _step + 1, _fx)
        )

    def _crossfade(self, out_widget: QWidget, in_widget: QWidget, between_fn=None):
        """Fade out out_widget then fade in in_widget."""
        def _after_out():
            if between_fn:
                between_fn()
            self._fade_widget(in_widget, out=False)
        self._fade_widget(out_widget, out=True, done=_after_out)

    # legacy shims
    def _fade_in(self, widget: QWidget, duration: int = 220):
        self._fade_widget(widget, out=False)

    def _fade_out_then(self, out_widget, between_fn, then_fade_in=None, duration: int = 200):
        self._crossfade(out_widget, then_fade_in, between_fn=between_fn)

    def _fade_transition(self, hide_widget, show_widget, between_callback=None):
        self._crossfade(hide_widget, show_widget, between_fn=between_callback)

    def _timer_fade_out(self, *a, **kw): pass
    def _timer_fade_in(self, *a, **kw): pass
    def _timer_fade_in_opacity(self, *a, **kw): pass

    def _make_option_button(self, question_id: str, value: str):
        display_value = self._translate_display_text(value)

        val_lower = value.strip().lower()
        is_yes = val_lower in {"yes", "yuwai"}
        is_no = val_lower in {"no", "nomu"}

        if is_yes:
            label = "✓  " + display_value
            bg_default, text_default = "#22C55E", "#FFFFFF"
            border_default, bg_hover, bg_checked = "#16A34A", "#16A34A", "#15803D"
        elif is_no:
            label = "✗  " + display_value
            bg_default, text_default = "#EF4444", "#FFFFFF"
            border_default, bg_hover, bg_checked = "#DC2626", "#DC2626", "#B91C1C"
        else:
            label = display_value
            bg_default, text_default = "#FDFAF6", "#3D1F14"
            border_default, bg_hover, bg_checked = "#D7CABC", "#F2E8E3", "#8B3A2E"

        btn = _AnimatedButton(label)
        btn.setProperty("answer_value", value)
        btn.setCheckable(True)
        btn.setFixedHeight(72)
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_default};
                color: {text_default};
                border: 2px solid {border_default};
                border-radius: 14px;
                font-size: 18px;
                font-weight: 900;
                padding: 14px 20px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {bg_hover};
                border: 2px solid {bg_hover};
                padding: 18px 24px;
            }}
            QPushButton:checked {{
                background-color: {bg_checked};
                color: #FFFFFF;
                border: 2px solid {bg_checked};
            }}
        """)

        if self.answers.get(question_id) == value:
            btn.setChecked(True)

        btn.clicked.connect(lambda checked, qid=question_id, val=value: self._select_answer(qid, val))
        return btn

    def _select_answer(self, question_id: str, value: str):
        self.answers[question_id] = value
        QTimer.singleShot(350, self._auto_advance)

    def _auto_advance(self):
        if self.current_index < len(self.questions):
            question = self.questions[self.current_index]
            if question["id"] in self.answers:
                self.current_index += 1
                self._render_current_question()

    # ==========================================================
    # Pain scale
    # ==========================================================
    def _style_pain_button(self, btn: QPushButton, color: str, selected: bool):
        # Style is handled inline via :checked CSS pseudo-state; this is a no-op stub.
        pass

    def _set_pain(self, value: int):
        self.answers["pain_scale"] = value
        color = self._pain_colors[value - 1]
        emoji = self._pain_labels[value - 1]
        if self._is_kriol_mode():
            names = ["Nomo", "Smol smol", "Mild", "Midel", "No komftabel",
                     "Nogud", "Strongpela", "Intens", "Togeta nogud", "Anbearabol"]
            lbl = names[value - 1]
            self._pain_level_label.setText(f"Lebul {value}  —  {lbl}")
        else:
            names = ["None", "Minimal", "Mild", "Moderate", "Uncomfortable",
                     "Distressing", "Severe", "Intense", "Very Severe", "Unbearable"]
            lbl = names[value - 1]
            self._pain_level_label.setText(f"Level {value}  —  {lbl}")
        self._pain_level_label.setStyleSheet(f"""
            font-size: 18px; font-weight: 900; color: {color}; background: transparent;
        """)
        self._pain_emoji_label.setText(emoji)
        self.pain_info_card.setStyleSheet(f"""
            QFrame#painInfoCard {{
                background: white;
                border: 2px solid {color};
                border-radius: 14px;
            }}
        """)
        # Update button checked states
        for i, btn in enumerate(self.scale_buttons, start=1):
            btn.setChecked(i == value)

    # ==========================================================
    # Speaker / TTS
    # ==========================================================
    def _current_question_speech_text(self) -> str:
        if self.current_index >= len(self.questions):
            return self.scale_title.text()

        question = self.questions[self.current_index]
        return self._translate_question_text(question.get("text", ""))

    def _auto_speak_current_question(self):
        self._speak_current_question()

    def _speak_rating_page(self):
        """Play rating audio then animate the 10 pain scale buttons sequentially."""
        is_kriol = self.strings.get("back", "Back").strip().lower() == "bek"
        audio = "Kriol-rating.mp3" if is_kriol else "English-rating.mp3"
        _stop_all()
        _play_sequence([audio], on_complete=self._animate_scale_buttons)

    def _animate_scale_buttons(self):
        """Nudge each of the 10 pain scale buttons one after another."""
        for i, btn in enumerate(self.scale_buttons):
            delay = i * 120
            def _nudge(b=btn):
                orig = b.geometry()
                nudged = orig.translated(0, 10)
                a1 = QPropertyAnimation(b, b"geometry", b)
                a1.setDuration(110)
                a1.setStartValue(orig)
                a1.setEndValue(nudged)
                a1.setEasingCurve(QEasingCurve.OutQuad)
                a2 = QPropertyAnimation(b, b"geometry", b)
                a2.setDuration(220)
                a2.setStartValue(nudged)
                a2.setEndValue(orig)
                a2.setEasingCurve(QEasingCurve.OutBack)
                a1.finished.connect(a2.start)
                a1.start()
                b._nudge_a1 = a1
                b._nudge_a2 = a2
            QTimer.singleShot(delay, _nudge)

    def _speak_current_question(self):
        """Orchestrate audio for each question.
        First question: play intro mp3 → prefix mp3 → TTS symptom word → animate buttons.
        Later questions: play prefix mp3 → TTS symptom word → animate buttons.
        """
        is_kriol = self.strings.get("back", "Back").strip().lower() == "bek"

        # Extract just the symptom word from "Do you also have {symptom}?"
        if self.current_index < len(self.questions):
            raw_text = self.questions[self.current_index].get("text", "")
            import re as _re
            m = _re.search(r"(?:do you also have|yu garr)\s+(.+?)\??$", raw_text.strip(), _re.IGNORECASE)
            symptom_word = m.group(1).strip() if m else raw_text.strip()
        else:
            symptom_word = self.scale_title.text()

        def _tts_then_animate():
            self._speak_text(symptom_word)
            QTimer.singleShot(400, self._animate_option_buttons)

        prefix_file = "Kriol-followup2.mp3" if is_kriol else "English-followup2.mp3"

        if self._is_first_question_shown:
            self._is_first_question_shown = False
            intro_file = "Kriol-followup1.mp3" if is_kriol else "English-followup1.mp3"
            _stop_all()
            _play_sequence([intro_file, prefix_file], on_complete=_tts_then_animate)
        else:
            _stop_all()
            _play_sequence([prefix_file], on_complete=_tts_then_animate)

    def _animate_option_buttons(self):
        """Nudge all current option buttons with a staggered bounce."""
        buttons = []
        for i in range(self.options_grid.count()):
            item = self.options_grid.itemAt(i)
            if item and item.widget():
                buttons.append(item.widget())
        for i, btn in enumerate(buttons):
            delay = i * 150
            def _nudge(b=btn):
                orig = b.geometry()
                nudged = orig.translated(0, 10)
                a1 = QPropertyAnimation(b, b"geometry", b)
                a1.setDuration(120)
                a1.setStartValue(orig)
                a1.setEndValue(nudged)
                a1.setEasingCurve(QEasingCurve.OutQuad)
                a2 = QPropertyAnimation(b, b"geometry", b)
                a2.setDuration(240)
                a2.setStartValue(nudged)
                a2.setEndValue(orig)
                a2.setEasingCurve(QEasingCurve.OutBack)
                a1.finished.connect(a2.start)
                a1.start()
                b._nudge_a1 = a1
                b._nudge_a2 = a2
            QTimer.singleShot(delay, _nudge)

    def _speak_text(self, text: str):
        """Speak text using macOS built-in 'say' command (no pyttsx3 needed)."""
        import subprocess, sys
        text = (text or "").strip()
        if not text:
            return
        if self._tts_thread is not None and self._tts_thread.is_alive():
            return

        def speak_job():
            try:
                if sys.platform == "darwin":
                    subprocess.run(["say", text], check=False)
                else:
                    import pyttsx3
                    engine = pyttsx3.init()
                    engine.setProperty("rate", 150)
                    engine.setProperty("volume", 1.0)
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
            "ready": ("#8B3A2E", "🎙️  Answer by voice"),
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
                border-radius: 14px;
                font-size: 15px;
                font-weight: 900;
                padding: 10px 18px;
            }}
            QPushButton:hover {{
                background-color: {color};
            }}
        """)

    def _set_scale_mic_state(self, state: str):
        styles = {
            "ready": ("#8B3A2E", "🎙️  Say number"),
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
                border-radius: 14px;
                font-size: 15px;
                font-weight: 900;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {color};
            }}
        """)

    # ==========================================================
    # Voice answer processing
    # ==========================================================
    def _start_voice_answer(self):
        if not self._is_speak_mode():
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

        self._voice_worker = QuestionVoiceWorker(duration_seconds=4, whisper_model_name="small", is_kriol=self._is_kriol_mode())
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

        # Voice answer should behave like tapping Yes/No:
        # after the answer is detected, move to the next question automatically.
        QTimer.singleShot(650, self._auto_advance)

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

    def _handle_next(self):
        # Only called from "See Results" button on pain scale card
        self.next_clicked.emit(self.answers)