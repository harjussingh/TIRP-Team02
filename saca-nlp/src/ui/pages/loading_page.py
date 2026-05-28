"""Loading / analysis animation page shown while run_final_assessment runs."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, QThread, Signal, QObject, QSize
from PySide6.QtGui import QColor, QPainter, QLinearGradient
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QProgressBar,
)
from PySide6.QtGui import QMovie
from src.utils.paths import asset_path
from src.utils.audio import play as _play, stop_all as _stop_all


# ---------------------------------------------------------------------------
# Background worker
# ---------------------------------------------------------------------------
class _AssessmentWorker(QObject):
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, nlp_output: dict, answers: dict, language: str):
        super().__init__()
        self._nlp_output = nlp_output
        self._answers = answers
        self._language = language

    def run(self):
        try:
            from src.services.triage_orchestrator import run_final_assessment
            result = run_final_assessment(
                self._nlp_output, self._answers, ui_language=self._language
            )
            self.finished.emit(result)
        except Exception as exc:
            self.error.emit(str(exc))


# ---------------------------------------------------------------------------
# Initial assessment worker
# ---------------------------------------------------------------------------
class _InitialAssessmentWorker(QObject):
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, text: str, language: str):
        super().__init__()
        self._text = text
        self._language = language

    def run(self):
        try:
            from src.services.triage_orchestrator import run_initial_assessment
            result = run_initial_assessment(self._text, self._language)
            self.finished.emit(result)
        except Exception as exc:
            self.error.emit(str(exc))


# ---------------------------------------------------------------------------
# Main loading page
# ---------------------------------------------------------------------------
class LoadingPage(QWidget):
    """Shown while run_initial_assessment or run_final_assessment runs on a background thread."""

    analysis_complete = Signal(dict)   # final assessment done
    initial_complete = Signal(dict)    # initial assessment done

    _STATUS_INITIAL = [
        "Processing your input…",
        "Detecting symptoms…",
        "Translating to clinical terms…",
        "Generating follow-up questions…",
        "Almost ready…",
    ]
    _STATUS_FINAL = [
        "Reviewing your symptom history…",
        "Running the clinical model…",
        "Cross-referencing diagnoses…",
        "Calculating triage priority…",
        "Preparing your results…",
    ]
    _STATUS_MESSAGES = _STATUS_FINAL  # default; overridden at runtime

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread: QThread | None = None
        self._worker = None
        self._progress_value = 0
        self._result_ready = False
        self._pending_result: dict | None = None
        self._mode = "final"  # "initial" or "final"

        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self):
        # Red accent background for the whole page
        self.setStyleSheet("background:#8B3A2E;")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setAlignment(Qt.AlignCenter)

        container = QWidget()
        container.setFixedWidth(460)
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)
        layout.setAlignment(Qt.AlignCenter)

        # Animated GIF
        self._gif_label = QLabel()
        self._gif_label.setAlignment(Qt.AlignCenter)
        self._gif_label.setStyleSheet("background: transparent;")
        self._movie = QMovie(str(asset_path("anim", "loading.gif")))
        self._movie.setScaledSize(QSize(150, 150))
        self._gif_label.setMovie(self._movie)
        self._movie.start()
        layout.addWidget(self._gif_label)

        # Title
        self._title_label = QLabel("Analysing Your Symptoms")
        self._title_label.setAlignment(Qt.AlignCenter)
        self._title_label.setWordWrap(True)
        self._title_label.setStyleSheet(
            "color:#FFFFFF; font-size:30px; font-weight:700;"
            "letter-spacing:0.5px; background:transparent;"
        )
        layout.addWidget(self._title_label)

        # Progress bar
        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(16)
        self._bar.setStyleSheet(
            """
            QProgressBar {
                background: rgba(255,255,255,0.25);
                border-radius: 8px;
                border: none;
            }
            QProgressBar::chunk {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FF8C00, stop:1 #FFA500
                );
                border-radius: 8px;
            }
            """
        )
        layout.addWidget(self._bar)

        # Percentage label
        self._pct_label = QLabel("0%")
        self._pct_label.setAlignment(Qt.AlignCenter)
        self._pct_label.setStyleSheet(
            "color:#FFFFFF; font-size:18px; font-weight:600;"
            "background:transparent;"
        )
        layout.addWidget(self._pct_label)

        root.addWidget(container, alignment=Qt.AlignCenter)

        # Timers
        self._progress_timer = QTimer(self)
        self._progress_timer.timeout.connect(self._advance_progress)

    # ------------------------------------------------------------------
    def _reset_state(self):
        self._progress_value = 0
        self._result_ready = False
        self._pending_result = None
        self._bar.setValue(0)
        self._pct_label.setText("0%")

    def start_analysis(self, nlp_output: dict, answers: dict, language: str):  # no audio — severity plays on results page
        """Called by MainWindow to begin final analysis."""
        self._mode = "final"
        self._title_label.setText(
            "Lukum Yu Simptom" if language == "kriol" else "Analysing Your Symptoms"
        )
        self._reset_state()
        _stop_all()
        _play("Kriol-loading.mp3" if language == "kriol" else "English-loading.mp3")

        # Start fake progress (0 → 80 % slowly; held until worker done)
        self._progress_timer.start(60)

        # Worker thread
        self._thread = QThread()
        self._worker = _AssessmentWorker(nlp_output, answers, language)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_worker_done)
        self._worker.error.connect(self._on_worker_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def start_initial_analysis(self, text: str, language: str):
        """Called when user submits voice/text/picture input."""
        self._mode = "initial"
        self._title_label.setText(
            "Prosesim Yu Tok" if language == "kriol" else "Processing Your Input"
        )
        self._reset_state()
        _stop_all()
        _play("Kriol-loading.mp3" if language == "kriol" else "English-loading.mp3")
        self._progress_timer.start(60)

        self._thread = QThread()
        self._worker = _InitialAssessmentWorker(text, language)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_worker_done)
        self._worker.error.connect(self._on_worker_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    # ------------------------------------------------------------------
    def _advance_progress(self):
        """Increment bar up to 82%; hold there until worker signals done."""
        if self._progress_value < 82:
            # Non-linear: fast early, slow near 82
            step = max(1, int((82 - self._progress_value) / 12))
            self._progress_value = min(82, self._progress_value + step)
            self._bar.setValue(self._progress_value)
            self._pct_label.setText(f"{self._progress_value}%")
        elif self._result_ready:
            # Worker is done — rush to 100
            self._progress_value = min(100, self._progress_value + 4)
            self._bar.setValue(self._progress_value)
            self._pct_label.setText(f"{self._progress_value}%")
            if self._progress_value >= 100:
                self._finish()

    def _on_worker_done(self, result: dict):
        self._pending_result = result
        self._result_ready = True
        if self._progress_value < 82:
            self._progress_value = 82

    def _on_worker_error(self, msg: str):
        """Fallback: emit empty result so app doesn't freeze."""
        self._pending_result = {}
        self._result_ready = True

    def _finish(self):
        self._progress_timer.stop()
        if self._pending_result is not None:
            if self._mode == "initial":
                self.initial_complete.emit(self._pending_result)
            else:
                self.analysis_complete.emit(self._pending_result)
