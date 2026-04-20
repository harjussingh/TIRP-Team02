from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStackedWidget

from src.ui.pages.home_page import HomePage
from src.ui.pages.input_page import InputPage
from src.ui.pages.questions_page import QuestionsPage
from src.ui.pages.results_page import ResultsPage
from src.ui.pages.emergency_page import EmergencyPage
from src.ui.pages.symptom_selection_page import SymptomSelectionPage
from src.services.triage_orchestrator import run_initial_assessment, run_final_assessment
from src.utils.lang import load_strings


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SACA - Adaptive Clinical Assistant")
        self.setMinimumSize(1280, 860)

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

        self.stack = QStackedWidget()
        self.stack.addWidget(self.home_page)               # 0
        self.stack.addWidget(self.input_page)              # 1
        self.stack.addWidget(self.symptom_selection_page)  # 2
        self.stack.addWidget(self.questions_page)          # 3
        self.stack.addWidget(self.results_page)            # 4
        self.stack.addWidget(self.emergency_page)          # 5

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)
        self.setCentralWidget(container)

        self._connect()
        self._apply_language()
        self.go_home()

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

    def go_home(self):
        self.stack.setCurrentIndex(0)

    def go_emergency(self):
        self.stack.setCurrentIndex(5)

    def _go_voice(self):
        self.current_mode = "voice"
        self.current_entry_page = "input"
        self.input_page.set_mode("voice", self.strings)
        self.stack.setCurrentIndex(1)

    def _go_type(self):
        self.current_mode = "type"
        self.current_entry_page = "input"
        self.input_page.set_mode("type", self.strings)
        self.stack.setCurrentIndex(1)

    def _go_pictures(self):
        self.current_entry_page = "pictures"
        self.stack.setCurrentIndex(2)

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
        self.stack.setCurrentIndex(3)

    def _handle_questions_back(self):
        if self.current_entry_page == "pictures":
            self.stack.setCurrentIndex(2)
        else:
            self.stack.setCurrentIndex(1)

    def _handle_answers(self, answers: dict):
        result_data = run_final_assessment(self.current_nlp_output, answers)
        self.results_page.set_result(result_data)
        self.stack.setCurrentIndex(4)