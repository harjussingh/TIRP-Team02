from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QFrame, QProgressBar
)
import os
import re


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

        root = QVBoxLayout(self)
        root.setContentsMargins(60, 40, 60, 40)
        root.setSpacing(20)

        self.top_card = QFrame()
        self.top_card.setObjectName("contentCard")
        top_layout = QVBoxLayout(self.top_card)
        top_layout.setContentsMargins(24, 20, 24, 20)
        top_layout.setSpacing(10)

        self.title_label = QLabel("A few more questions")
        self.title_label.setObjectName("pageTitle")

        self.progress_label = QLabel("Question 1 of 1")
        self.progress_label.setObjectName("cardBody")

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMinimumHeight(16)

        self.summary_label = QLabel("")
        self.summary_label.setObjectName("cardBody")
        self.summary_label.setWordWrap(True)

        top_layout.addWidget(self.title_label)
        top_layout.addWidget(self.progress_label)
        top_layout.addWidget(self.progress_bar)
        top_layout.addWidget(self.summary_label)

        self.question_card = QFrame()
        self.question_card.setObjectName("contentCard")
        question_layout = QVBoxLayout(self.question_card)
        question_layout.setContentsMargins(24, 24, 24, 24)
        question_layout.setSpacing(18)

        self.question_label = QLabel("")
        self.question_label.setObjectName("mainTitle")
        self.question_label.setAlignment(Qt.AlignCenter)
        self.question_label.setWordWrap(True)

        self.options_row_1 = QHBoxLayout()
        self.options_row_1.setSpacing(14)

        self.options_row_2 = QHBoxLayout()
        self.options_row_2.setSpacing(14)

        question_layout.addWidget(self.question_label)
        question_layout.addSpacing(10)
        question_layout.addLayout(self.options_row_1)
        question_layout.addLayout(self.options_row_2)

        self.scale_card = QFrame()
        self.scale_card.setObjectName("contentCard")
        scale_layout = QVBoxLayout(self.scale_card)
        scale_layout.setContentsMargins(24, 24, 24, 24)
        scale_layout.setSpacing(16)

        self.scale_title = QLabel("How bad is your problem?")
        self.scale_title.setObjectName("mainTitle")
        self.scale_title.setAlignment(Qt.AlignCenter)

        self.scale_image = QLabel()
        self.scale_image.setObjectName("painScaleImage")
        self.scale_image.setAlignment(Qt.AlignCenter)
        self.scale_image.setMinimumHeight(220)

        img_path = os.path.join("assets", "images", "pain_scale.png")
        if os.path.exists(img_path):
            pixmap = QPixmap(img_path)
            self.scale_image.setPixmap(
                pixmap.scaledToWidth(900, Qt.SmoothTransformation)
            )
        else:
            self.scale_image.setText("Pain Scale")

        self.scale_buttons_row_1 = QHBoxLayout()
        self.scale_buttons_row_1.setSpacing(12)

        self.scale_buttons_row_2 = QHBoxLayout()
        self.scale_buttons_row_2.setSpacing(12)

        self.scale_buttons = []
        for i in range(1, 11):
            btn = QPushButton(str(i))
            btn.setObjectName("optionButton")
            btn.setCheckable(True)
            btn.setMinimumHeight(70)
            btn.clicked.connect(lambda checked, value=i: self._set_pain(value))
            self.scale_buttons.append(btn)

        for btn in self.scale_buttons[:5]:
            self.scale_buttons_row_1.addWidget(btn)
        for btn in self.scale_buttons[5:]:
            self.scale_buttons_row_2.addWidget(btn)

        self.scale_label = QLabel("Selected level: 3")
        self.scale_label.setObjectName("scaleValueLabel")
        self.scale_label.setAlignment(Qt.AlignCenter)
        self.scale_label.setMinimumHeight(44)

        scale_layout.addWidget(self.scale_title)
        scale_layout.addWidget(self.scale_image)
        scale_layout.addLayout(self.scale_buttons_row_1)
        scale_layout.addLayout(self.scale_buttons_row_2)
        scale_layout.addWidget(self.scale_label)

        buttons = QHBoxLayout()
        buttons.setSpacing(12)

        self.back_btn = QPushButton("Back")
        self.back_btn.setObjectName("secondaryButton")
        self.back_btn.setMinimumHeight(50)
        self.back_btn.setMinimumWidth(120)

        self.emergency_btn = QPushButton("Emergency Help")
        self.emergency_btn.setObjectName("secondaryButton")
        self.emergency_btn.setMinimumHeight(50)
        self.emergency_btn.setMinimumWidth(170)

        self.next_btn = QPushButton("Next")
        self.next_btn.setObjectName("primaryButton")
        self.next_btn.setMinimumHeight(50)
        self.next_btn.setMinimumWidth(170)

        buttons.addWidget(self.back_btn)
        buttons.addWidget(self.emergency_btn)
        buttons.addStretch()
        buttons.addWidget(self.next_btn)

        root.addWidget(self.top_card)
        root.addWidget(self.question_card)
        root.addWidget(self.scale_card)
        root.addLayout(buttons)

        self.back_btn.clicked.connect(self._handle_back)
        self.emergency_btn.clicked.connect(self.emergency_clicked.emit)
        self.next_btn.clicked.connect(self._handle_next)

        self.answers["pain_scale"] = 3
        self.scale_buttons[2].setChecked(True)
        self.scale_card.hide()

    def _is_kriol_mode(self) -> bool:
        return self.strings.get("back", "Back").strip().lower() == "bek"

    def _translate_display_text(self, text: str) -> str:
        if not self._is_kriol_mode() or not text:
            return text

        display_map = {
            "headache": self.strings.get("symptom_headache", "Hedake"),
            "fever": self.strings.get("symptom_fever", "Fiba"),
            "cough": self.strings.get("symptom_cough", "Kof"),
            "stomach pain": self.strings.get("symptom_stomach_pain", "Beli pein"),
            "sore throat": self.strings.get("symptom_sore_throat", "Throt pein"),
            "body pain": self.strings.get("symptom_body_pain", "Bodi pein"),
            "tired": self.strings.get("symptom_tired", "Taid"),
            "dizzy": self.strings.get("symptom_dizzy", "Dizi"),
            "chest pain": self.strings.get("symptom_chest_pain", "Jes pein"),
            "skin problem": self.strings.get("symptom_skin_problem", "Skin trabul"),
            "head": "hed",
            "chest": "jes",
            "stomach": "beli",
            "throat": "throt",
            "whole body": "hol bodi",
            "pain": "pein",
            "weak": "wik",
            "vomiting": "spyu",
            "diarrhea": "ranishit",
            "rash": "rash",
            "breathing problem": "brithin trabul"
        }

        result = text
        for eng, kriol in sorted(display_map.items(), key=lambda x: len(x[0]), reverse=True):
            result = re.sub(rf"\b{re.escape(eng)}\b", kriol, result, flags=re.IGNORECASE)

        return result

    def set_strings(self, s: dict):
        self.strings = s
        self.title_label.setText(s.get("few_questions", "A few more questions"))
        self.scale_title.setText(s.get("how_bad", "How bad is your problem?"))
        self.back_btn.setText(s.get("back", "Back"))
        self.next_btn.setText(s.get("next", "Next"))
        self.emergency_btn.setText(s.get("emergency", "Emergency Help"))
        self._update_scale_label(self.answers.get("pain_scale", 3))

    def set_questions(self, original_text: str, english_meaning: str, questions: list):
        self.answers = {"pain_scale": self.answers.get("pain_scale", 3)}
        self.questions = questions
        self.current_index = 0

        you_said = self.strings.get(
            "you_said_label",
            "Yu sed" if self._is_kriol_mode() else "You said"
        )
        english_meaning_label = self.strings.get(
            "english_meaning_label",
            "Ingris mining" if self._is_kriol_mode() else "English meaning"
        )

        display_original = self._translate_display_text(original_text)
        display_meaning = self._translate_display_text(english_meaning)

        self.summary_label.setText(
            f"{you_said}: {display_original}\n\n{english_meaning_label}: {display_meaning}"
        )

        self.question_card.show()
        self.scale_card.hide()
        self._render_current_question()

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _render_current_question(self):
        total_steps = len(self.questions) + 1
        current_step = min(self.current_index + 1, total_steps)

        progress_template = self.strings.get(
            "question_progress",
            "Kwestin {current} long {total}" if self._is_kriol_mode() else "Question {current} of {total}"
        )
        self.progress_label.setText(progress_template.format(current=current_step, total=total_steps))
        self.progress_bar.setValue(int((current_step / total_steps) * 100))

        if self.current_index >= len(self.questions):
            self.question_card.hide()
            self.scale_card.show()
            self.next_btn.setText(self.strings.get("see_results", "See Results"))
            return

        self.question_card.show()
        self.scale_card.hide()
        self.next_btn.setText(self.strings.get("next", "Next"))

        question = self.questions[self.current_index]
        self.question_label.setText(question["text"])

        self._clear_layout(self.options_row_1)
        self._clear_layout(self.options_row_2)

        options = question["options"]
        half = (len(options) + 1) // 2

        for option in options[:half]:
            btn = self._make_option_button(question["id"], option)
            self.options_row_1.addWidget(btn)

        for option in options[half:]:
            btn = self._make_option_button(question["id"], option)
            self.options_row_2.addWidget(btn)

    def _make_option_button(self, question_id: str, value: str):
        btn = QPushButton(value)
        btn.setObjectName("optionButton")
        btn.setCheckable(True)
        btn.setMinimumHeight(90)

        if self.answers.get(question_id) == value:
            btn.setChecked(True)

        btn.clicked.connect(lambda checked, qid=question_id, val=value: self._select_answer(qid, val))
        return btn

    def _select_answer(self, question_id: str, value: str):
        self.answers[question_id] = value
        self._render_current_question()

    def _update_scale_label(self, value: int):
        template = self.strings.get(
            "selected_level_label",
            "Yu jusum lebul: {value}" if self._is_kriol_mode() else "Selected level: {value}"
        )
        self.scale_label.setText(template.format(value=value))

    def _set_pain(self, value: int):
        self.answers["pain_scale"] = value
        self._update_scale_label(value)

        for i, btn in enumerate(self.scale_buttons, start=1):
            btn.setChecked(i == value)

    def _handle_back(self):
        if self.current_index == 0:
            self.back_clicked.emit()
            return

        self.current_index -= 1
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