from __future__ import annotations

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QStackedWidget, QGraphicsOpacityEffect, QWidget

from src.ui.pages.home_page import HomePage
from src.ui.pages.input_page import InputPage
from src.ui.pages.questions_page import QuestionsPage
from src.ui.pages.results_page import ResultsPage
from src.ui.pages.emergency_page import EmergencyPage
from src.ui.pages.symptom_selection_page import SymptomSelectionPage
from src.ui.pages.loading_page import LoadingPage
from src.ui.widgets.background_widget import PatternBackgroundWidget
from src.utils.lang import load_strings
from src.utils.paths import asset_path
from src.utils.audio import stop_all as _stop_all


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SACA - Adaptive Clinical Assistant")
        self.setFixedSize(1024, 720)
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
        self.loading_page = LoadingPage()

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
        self.stack.addWidget(self.loading_page)            # 6

        self.background = PatternBackgroundWidget(asset_path("backgrounds", "saca_pattern_bg.jpg"))
        layout = QVBoxLayout(self.background)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.stack)
        self.setCentralWidget(self.background)

        self._connect()
        self._apply_language()

        # ── page-transition curtain ──
        # A solid-coloured overlay that sits on top of everything.
        # Fade IN (0→1) hides current content, we swap page, then fade OUT (1→0).
        # This prevents the background image or other page text from showing through.
        self._curtain = QWidget(self.background)
        self._curtain.setFixedSize(1024, 720)
        self._curtain.setStyleSheet("background-color: #F0E6D8;")   # warm cream
        self._curtain.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._curtain.raise_()

        self._curtain_fx = QGraphicsOpacityEffect(self._curtain)
        self._curtain_fx.setOpacity(0.0)
        self._curtain.setGraphicsEffect(self._curtain_fx)

        self._curtain_anim = QPropertyAnimation(self._curtain_fx, b"opacity", self)
        self._curtain_anim.setDuration(200)
        self._curtain_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self._curtain_anim.finished.connect(self._on_curtain_step)

        self._pending_index    = None
        self._pending_emergency = False
        self._curtain_phase    = "idle"   # "cover" | "reveal" | "idle"

        self.go_home(animated=False)

    def closeEvent(self, event):
        """Stop all audio when the application window is closed."""
        _stop_all()
        super().closeEvent(event)

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

        # Loading page uses its own solid red background — must be opaque
        self.loading_page.setObjectName("loadingPage")
        self.loading_page.setAutoFillBackground(True)
        self.loading_page.setAttribute(Qt.WA_StyledBackground, True)

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

        self.results_page.emergency_clicked.connect(self.go_emergency)
        self.results_page.home_clicked.connect(self.go_home)

        self.loading_page.analysis_complete.connect(self._on_analysis_complete)
        self.loading_page.initial_complete.connect(self._on_initial_complete)

        self.emergency_page.back_clicked.connect(self.go_home)

    def _apply_language(self):
        self.strings = load_strings(self.language_code)
        self.home_page.set_strings(self.strings)
        self.input_page.set_strings(self.strings)
        self.symptom_selection_page.set_language(self.language_code)
        self.symptom_selection_page.set_strings(self.strings)
        self.questions_page.set_strings(self.strings)
        self.results_page.set_strings(self.strings)
        self.emergency_page.set_strings(self.strings)

    def _change_language(self, code: str):
        self.language_code = code
        self._apply_language()

    def _show_page(self, index: int, emergency: bool = False):
        """Transition to a page using a solid curtain: cover → swap → reveal."""
        if self._curtain_phase != "idle":
            # Queue latest target; current animation will pick it up
            self._pending_index = index
            self._pending_emergency = emergency
            return
        self._pending_index = index
        self._pending_emergency = emergency
        self._curtain_phase = "cover"
        self._curtain_anim.setStartValue(0.0)
        self._curtain_anim.setEndValue(1.0)
        self._curtain_anim.start()

    def _on_curtain_step(self):
        if self._curtain_phase == "cover":
            # Curtain fully opaque — safe to swap page
            self.background.set_emergency_mode(self._pending_emergency)
            self.stack.setCurrentIndex(self._pending_index)
            # Notify the incoming page so it can replay entry animations
            incoming = self.stack.currentWidget()
            if hasattr(incoming, "play_entry_animations"):
                incoming.play_entry_animations()
            self._pending_index = None
            # Now reveal
            self._curtain_phase = "reveal"
            self._curtain_anim.setStartValue(1.0)
            self._curtain_anim.setEndValue(0.0)
            self._curtain_anim.start()
        else:
            # Reveal finished
            self._curtain_phase = "idle"
            # If a new navigation was queued while we were revealing, honour it now
            if self._pending_index is not None:
                self._show_page(self._pending_index, self._pending_emergency)

    def go_home(self, animated: bool = True):
        _stop_all()
        # Clear all inputs so the next session starts fresh
        self.input_page.clear_input()
        self.symptom_selection_page.clear_selection()
        if animated:
            self._show_page(0, emergency=False)
        else:
            self.background.set_emergency_mode(False)
            self.stack.setCurrentIndex(0)

    def go_emergency(self):
        self.emergency_page.show_popup(parent=self)

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
        self.current_mode = "pictures"
        self.current_entry_page = "pictures"
        self._show_page(2, emergency=False)

    def _handle_picture_input(self, text: str):
        self._start_assessment(text)

    def _handle_initial_input(self, text: str):
        self._start_assessment(text)

    def _start_assessment(self, text: str):
        self._show_page(6, emergency=False)
        self.loading_page.start_initial_analysis(text, self.language_code)

    def _on_initial_complete(self, nlp_output: dict):
        self.current_nlp_output = nlp_output
        self.questions_page.set_input_mode(self.current_mode)
        self.questions_page.set_questions(
            original_text=nlp_output["original_text"],
            english_meaning=nlp_output["translated_text_en"],
            questions=nlp_output["followup_questions"],
        )
        self._show_page(3, emergency=False)

    def _handle_questions_back(self):
        _stop_all()
        if self.current_entry_page == "pictures":
            self._show_page(2, emergency=False)
        else:
            self._show_page(1, emergency=False)

    def _on_analysis_complete(self, result_data: dict):
        self.results_page.set_result(result_data)
        self._show_page(4, emergency=False)

    def _handle_answers(self, answers: dict):
        self._show_page(6, emergency=False)
        self.loading_page.start_analysis(
            self.current_nlp_output, answers, self.language_code
        )
