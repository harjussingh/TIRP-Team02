from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QStackedWidget

from src.ui.pages.home_page import HomePage
from src.ui.pages.input_page import InputPage
from src.ui.pages.questions_page import QuestionsPage
from src.ui.pages.results_page import ResultsPage
from src.ui.pages.emergency_page import EmergencyPage
from src.ui.pages.symptom_selection_page import SymptomSelectionPage
from src.ui.widgets.background_widget import PatternBackgroundWidget
from src.services.triage_orchestrator import run_initial_assessment, run_final_assessment
from src.utils.lang import load_strings
from src.utils.paths import asset_path


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SACA - Adaptive Clinical Assistant")
        self.setMinimumSize(1280, 860)
        self.setObjectName("mainWindow")

        self.language_code = "en"
        self.strings = load_strings(self.language_code)
        self.current_mode = "type"
        self.current_nlp_output = None
        self.current_entry_page = "input"

        self.home_page = HomePage()
        self.input_page = InputPage()
        self.symptom_selection_page = SymptomSelectionPage()
        self.questions_page = QuestionsPage()
        self.results_page = ResultsPage()
        self.emergency_page = EmergencyPage()

        self._prepare_page_backgrounds()

        self.stack = QStackedWidget()
        self.stack.setObjectName("appStack")
        self.stack.setAttribute(Qt.WA_TranslucentBackground, True)
        self.stack.setStyleSheet("QStackedWidget#appStack { background: transparent; border: none; }")

        self.stack.addWidget(self.home_page)               # 0
        self.stack.addWidget(self.input_page)              # 1
        self.stack.addWidget(self.symptom_selection_page)  # 2
        self.stack.addWidget(self.questions_page)          # 3
        self.stack.addWidget(self.results_page)            # 4
        self.stack.addWidget(self.emergency_page)          # 5

        self.background = PatternBackgroundWidget(asset_path("backgrounds", "saca_pattern_bg.jpg"))
        layout = QVBoxLayout(self.background)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.stack)
        self.setCentralWidget(self.background)

        self._connect()
        self._apply_language()
        self.go_home()

    def _prepare_page_backgrounds(self):
        """Let the pattern image show through normal pages; keep emergency plain."""
        pattern_pages = [
            self.home_page,
            self.input_page,
            self.symptom_selection_page,
            self.questions_page,
            self.results_page,
        ]

        for page in pattern_pages:
            page.setObjectName("transparentPage")
            page.setAutoFillBackground(False)
            page.setAttribute(Qt.WA_TranslucentBackground, True)

        self.emergency_page.setObjectName("emergencyPlainPage")
        self.emergency_page.setAutoFillBackground(True)
        self.emergency_page.setAttribute(Qt.WA_StyledBackground, True)

    def _connect(self):
        self.home_page.speak_clicked.connect(self._go_voice)
        self.home_page.type_clicked.connect(self._go_type)
        self.home_page.pictures_clicked.connect(self._go_pictures)
        self.home_page.emergency_clicked.connect(self.go_emergency)
        self.home_page.language_changed.connect(self._change_language)

        self.input_page.back_clicked.connect(self.go_home)
        self.input_page.emergency_clicked.connect(self.go_emergency)
        self.input_page.submit_clicked.connect(self._handle_initial_input)

        self.symptom_selection_page.back_clicked.connect(self.go_home)
        self.symptom_selection_page.emergency_clicked.connect(self.go_emergency)
        self.symptom_selection_page.continue_clicked.connect(self._handle_picture_input)

        self.questions_page.back_clicked.connect(self._handle_questions_back)
        self.questions_page.emergency_clicked.connect(self.go_emergency)
        self.questions_page.next_clicked.connect(self._handle_answers)

        self.results_page.back_clicked.connect(lambda: self.stack.setCurrentIndex(3))
        self.results_page.emergency_clicked.connect(self.go_emergency)
        self.results_page.home_clicked.connect(self.go_home)

        self.emergency_page.back_clicked.connect(self.go_home)

    def _apply_language(self):
        self.strings = load_strings(self.language_code)
        self.home_page.set_strings(self.strings)
        self.input_page.set_strings(self.strings)
        self.symptom_selection_page.set_strings(self.strings)
        self.questions_page.set_strings(self.strings)
        self.results_page.set_strings(self.strings)
        self.emergency_page.set_strings(self.strings)

    def _change_language(self, code: str):
        self.language_code = code
        self._apply_language()

    def _show_page(self, index: int, emergency: bool = False):
        self.background.set_emergency_mode(emergency)
        self.stack.setCurrentIndex(index)

    def go_home(self):
        self._show_page(0, emergency=False)

    def go_emergency(self):
        self._show_page(5, emergency=True)

    def _go_voice(self):
        self.current_mode = "voice"
        self.current_entry_page = "input"
        self.input_page.set_mode("voice", self.strings)
        self._show_page(1, emergency=False)

    def _go_type(self):
        self.current_mode = "type"
        self.current_entry_page = "input"
        self.input_page.set_mode("type", self.strings)
        self._show_page(1, emergency=False)

    def _go_pictures(self):
        self.current_entry_page = "pictures"
        self._show_page(2, emergency=False)

    def _handle_picture_input(self, text: str):
        self._start_assessment(text)

    def _handle_initial_input(self, text: str):
        self._start_assessment(text)

    def _start_assessment(self, text: str):
        self.current_nlp_output = run_initial_assessment(text, self.language_code)
        self.questions_page.set_questions(
            original_text=self.current_nlp_output["original_text"],
            english_meaning=self.current_nlp_output["translated_text_en"],
            questions=self.current_nlp_output["followup_questions"],
        )
        self._show_page(3, emergency=False)

    def _handle_questions_back(self):
        if self.current_entry_page == "pictures":
            self._show_page(2, emergency=False)
        else:
            self._show_page(1, emergency=False)

    def _handle_answers(self, answers: dict):
        result_data = run_final_assessment(self.current_nlp_output, answers, ui_language=self.language_code)
        self.results_page.set_result(result_data)
        self._show_page(4, emergency=False)
