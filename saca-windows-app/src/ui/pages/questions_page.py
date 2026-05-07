import re

from PySide6.QtCore import Signal, Qt
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

        # ---------- Small summary ----------
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
        question_layout.setContentsMargins(44, 42, 44, 42)
        question_layout.setSpacing(28)

        self.question_label = QLabel("")
        self.question_label.setAlignment(Qt.AlignCenter)
        self.question_label.setWordWrap(True)
        self.question_label.setStyleSheet("""
            font-size: 38px;
            font-weight: 900;
            color: #2D1810;
            background: transparent;
        """)

        self.options_grid = QGridLayout()
        self.options_grid.setHorizontalSpacing(18)
        self.options_grid.setVerticalSpacing(18)

        question_layout.addWidget(self.question_label)
        question_layout.addLayout(self.options_grid)

        root.addWidget(self.question_card, 1)

        # ---------- Pain scale card ----------
        self.scale_card = QFrame()
        self.scale_card.setMaximumHeight(470)
        self.scale_card.setMinimumHeight(430)
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
        scale_layout.addSpacing(42)
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

    # ------------------------------------------------------------------
    # Language helpers
    # ------------------------------------------------------------------
    def _is_kriol_mode(self) -> bool:
        return self.strings.get("back", "Back").strip().lower() == "bek"

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
        }

        result = text
        for eng, kriol in sorted(display_map.items(), key=lambda x: len(x[0]), reverse=True):
            result = re.sub(rf"\b{re.escape(eng)}\b", kriol, result, flags=re.IGNORECASE)
        return result

    def set_strings(self, s: dict):
        self.strings = s or {}
        is_kriol = self._is_kriol_mode()

        self.scale_title.setText(
            self.strings.get("how_bad", "Hau nogud pein? (1–10)" if is_kriol else "How bad is the pain? (1–10)")
        )
        self.no_pain_label.setText(self.strings.get("no_pain_label", "Nomo pein" if is_kriol else "No pain"))
        self.worst_pain_label.setText(self.strings.get("worst_pain_label", "Moj nogud pein" if is_kriol else "Worst pain"))
        self.back_btn.setText(self.strings.get("back", "Bek" if is_kriol else "←  Back"))
        self.skip_btn.setText(self.strings.get("skip", "Skipim" if is_kriol else "Skip"))
        self.emergency_btn.setText(self.strings.get("emergency", "🚨 Imijensi Elp" if is_kriol else "ⓘ  Emergency"))
        self.next_btn.setText(self.strings.get("next", "Nekis" if is_kriol else "Next  →"))

    def set_questions(self, original_text: str, english_meaning: str, questions: list):
        self.answers = {"pain_scale": self.answers.get("pain_scale", 3)}
        self.questions = questions or []
        self.current_index = 0

        you_said = self.strings.get("you_said_label", "You said")
        english_meaning_label = self.strings.get("english_meaning_label", "English meaning")

        display_original = self._translate_display_text(original_text)
        display_meaning = self._translate_display_text(english_meaning)
        self.summary_label.setText(f"{you_said}: {display_original}   |   {english_meaning_label}: {display_meaning}")

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
        percent = int((current_step / total_steps) * 100)

        progress_template = self.strings.get("question_progress", "Question {current} of {total}")
        self.progress_label.setText(progress_template.format(current=current_step, total=total_steps))
        self.percent_label.setText(f"{percent}%")
        self.progress_bar.setValue(percent)

        if self.current_index >= len(self.questions):
            self.question_card.hide()
            self.scale_card.show()
            self.skip_btn.hide()
            self.next_btn.setText(self.strings.get("see_results", "See Results  →"))
            return

        self.question_card.show()
        self.scale_card.hide()
        self.skip_btn.show()
        self.next_btn.setText(self.strings.get("next", "Next  →"))

        question = self.questions[self.current_index]
        self.question_label.setText(question["text"])
        self._clear_layout(self.options_grid)

        options = question.get("options", [])
        for i, option in enumerate(options):
            row = i // 2
            col = i % 2
            btn = self._make_option_button(question["id"], option)
            self.options_grid.addWidget(btn, row, col)

    def _make_option_button(self, question_id: str, value: str):
        btn = QPushButton(value)
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
