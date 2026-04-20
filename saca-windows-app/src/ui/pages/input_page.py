try:
    import speech_recognition as sr
except Exception:
    sr = None

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QTextEdit, QHBoxLayout, QFrame, QMessageBox, QGridLayout
)


class InputPage(QWidget):
    back_clicked = Signal()
    emergency_clicked = Signal()
    submit_clicked = Signal(str)

    def __init__(self):
        super().__init__()
        self.mode = "type"
        self.strings = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(60, 35, 60, 35)
        root.setSpacing(20)

        self.title_label = QLabel("Type here")
        self.title_label.setObjectName("mainTitle")
        self.title_label.setAlignment(Qt.AlignCenter)

        self.subtitle_label = QLabel("Write or speak your symptoms")
        self.subtitle_label.setObjectName("mainSubtitle")
        self.subtitle_label.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setObjectName("contentCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(16)

        self.status_label = QLabel("")
        self.status_label.setObjectName("cardBody")
        self.status_label.setAlignment(Qt.AlignCenter)

        self.mic_btn = QPushButton("🎤 Start speaking")
        self.mic_btn.setObjectName("bigPrimaryButton")
        self.mic_btn.setMinimumHeight(78)
        self.mic_btn.clicked.connect(self.record_voice)

        self.input_box = QTextEdit()
        self.input_box.setMinimumHeight(220)
        self.input_box.setPlaceholderText("Type here")

        self.chips_title = QLabel("Quick symptoms")
        self.chips_title.setObjectName("fieldLabel")

        self.chips_grid = QGridLayout()
        self.chips_grid.setHorizontalSpacing(12)
        self.chips_grid.setVerticalSpacing(12)

        self.symptom_chips = []
        chip_texts = [
            "Headache", "Fever", "Cough", "Stomach pain",
            "Sore throat", "Body pain", "Tired", "Dizzy"
        ]

        for i, text in enumerate(chip_texts):
            btn = QPushButton(text)
            btn.setObjectName("optionButton")
            btn.setMinimumHeight(54)
            btn.clicked.connect(lambda checked=False, value=text: self._add_chip_text(value))
            self.symptom_chips.append(btn)
            self.chips_grid.addWidget(btn, i // 2, i % 2)

        chips_frame = QFrame()
        chips_layout = QVBoxLayout(chips_frame)
        chips_layout.setContentsMargins(0, 0, 0, 0)
        chips_layout.setSpacing(10)
        chips_layout.addWidget(self.chips_title)
        chips_layout.addLayout(self.chips_grid)

        buttons = QHBoxLayout()

        self.back_btn = QPushButton("Back")
        self.back_btn.setObjectName("secondaryButton")
        self.back_btn.setMinimumHeight(50)

        self.emergency_btn = QPushButton("Emergency Help")
        self.emergency_btn.setObjectName("secondaryButton")
        self.emergency_btn.setMinimumHeight(50)

        self.next_btn = QPushButton("Next")
        self.next_btn.setObjectName("primaryButton")
        self.next_btn.setMinimumHeight(50)

        buttons.addWidget(self.back_btn)
        buttons.addWidget(self.emergency_btn)
        buttons.addStretch()
        buttons.addWidget(self.next_btn)

        card_layout.addWidget(self.status_label)
        card_layout.addWidget(self.mic_btn)
        card_layout.addWidget(self.input_box)
        card_layout.addWidget(chips_frame)
        card_layout.addLayout(buttons)

        root.addWidget(self.title_label)
        root.addWidget(self.subtitle_label)
        root.addWidget(card)

        self.back_btn.clicked.connect(self.back_clicked.emit)
        self.emergency_btn.clicked.connect(self.emergency_clicked.emit)
        self.next_btn.clicked.connect(self._submit)

        self.chips_frame = chips_frame

    def set_strings(self, s: dict):
        self.strings = s
        self.back_btn.setText(s.get("back", "Back"))
        self.next_btn.setText(s.get("next", "Next"))
        self.emergency_btn.setText(s.get("emergency", "Emergency Help"))
        self.chips_title.setText(s.get("quick_symptoms", "Quick symptoms"))

        if self.mode == "voice":
            self.title_label.setText(s.get("speak_now", "Speak now"))
            self.subtitle_label.setText(s.get("press_microphone", "Press the microphone"))
            self.mic_btn.setText(s.get("start_speaking", "🎤 Start speaking"))
            self.input_box.setPlaceholderText(s.get("voice_placeholder", "Your voice will appear here"))
            self.status_label.setText(s.get("voice_status_ready", "Press the microphone and speak clearly"))
        else:
            self.title_label.setText(s.get("type_here", "Type here"))
            self.subtitle_label.setText(s.get("type_subtitle", "Write your symptoms"))
            self.input_box.setPlaceholderText(s.get("type_placeholder", "Type symptoms here"))
            self.status_label.setText(s.get("type_status_ready", "You can type or tap the quick symptoms"))

        chip_defaults = [
            s.get("symptom_headache", "Headache"),
            s.get("symptom_fever", "Fever"),
            s.get("symptom_cough", "Cough"),
            s.get("symptom_stomach_pain", "Stomach pain"),
            s.get("symptom_sore_throat", "Sore throat"),
            s.get("symptom_body_pain", "Body pain"),
            s.get("symptom_tired", "Tired"),
            s.get("symptom_dizzy", "Dizzy"),
        ]
        for btn, label in zip(self.symptom_chips, chip_defaults):
            btn.setText(label)

    def set_mode(self, mode: str, s: dict):
        self.mode = mode
        self.input_box.clear()

        if mode == "voice":
            self.mic_btn.show()
            self.chips_frame.hide()
        else:
            self.mic_btn.hide()
            self.chips_frame.show()

        self.set_strings(s)

    def _add_chip_text(self, value: str):
        current = self.input_box.toPlainText().strip()
        if not current:
            self.input_box.setPlainText(value)
        else:
            self.input_box.setPlainText(f"{current}, {value}")

    def record_voice(self):
        if sr is None:
            QMessageBox.warning(self, "Voice", "SpeechRecognition is not installed.")
            return

        self.status_label.setText(self.strings.get("listening", "Listening..."))

        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = recognizer.listen(source, timeout=6, phrase_time_limit=10)

            text = recognizer.recognize_google(audio)
            self.input_box.setPlainText(text)
            self.status_label.setText(self.strings.get("recording_done", "Recording complete"))

        except Exception as e:
            self.status_label.setText(self.strings.get("voice_error", "Could not understand speech"))
            QMessageBox.warning(self, "Voice", str(e))

    def _submit(self):
        text = self.input_box.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Input", "Please enter or speak symptoms.")
            return

        self.submit_clicked.emit(text)