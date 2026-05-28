import os
import tempfile
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QThread, QTimer, QPropertyAnimation, QEasingCurve, QRect, Property, QUrl
from PySide6.QtGui import (
    QTextCursor, QPainter, QPen, QColor, QFont,
    QLinearGradient, QPainterPath, QPixmap,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QFrame, QSizePolicy,
    QStackedWidget, QScrollArea, QGraphicsOpacityEffect,
    QAbstractButton,
)
from src.ui.widgets.help_popup import HelpButton
from src.utils.audio import play as _play, play_sequence as _play_sequence, stop_all as _stop_all

# Kriol transcription corrector (applied to raw Whisper output in Kriol mode)
try:
    from nlp.kriol_translator import correct_kriol_transcription, load_kriol_dictionary as _load_kriol_dict
    import os as _os
    _KRIOL_DICT_PATH = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "data", "kriol_dictionary.json")
    _KRIOL_DICT = _load_kriol_dict(_os.path.normpath(_KRIOL_DICT_PATH))
except Exception:
    correct_kriol_transcription = None
    _KRIOL_DICT = {}


def _audio_path(filename: str) -> str:
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(
        os.path.join(base, "..", "..", "..", "assets", "audio", filename)
    )


def _play(filename: str):
    """Fire-and-forget audio playback."""
    path = _audio_path(filename)
    if not os.path.exists(path):
        return
    player = QMediaPlayer()
    audio_out = QAudioOutput()
    audio_out.setVolume(1.0)
    player.setAudioOutput(audio_out)
    player.setSource(QUrl.fromLocalFile(path))
    player.play()
    player._audio_out = audio_out
    _play._active.append(player)
    player.playbackStateChanged.connect(
        lambda state, p=player: _play._active.remove(p)
        if p in _play._active and state == QMediaPlayer.StoppedState else None
    )

_play._active = []


def _play_sequence(filenames: list, on_complete=None):
    """Play a list of audio files one after another, then call on_complete."""
    if not filenames:
        if on_complete:
            on_complete()
        return
    first, *rest = filenames
    path = _audio_path(first)
    if not os.path.exists(path):
        _play_sequence(rest, on_complete)
        return
    player = QMediaPlayer()
    audio_out = QAudioOutput()
    audio_out.setVolume(1.0)
    player.setAudioOutput(audio_out)
    player.setSource(QUrl.fromLocalFile(path))
    player._audio_out = audio_out
    _play._active.append(player)
    def _on_status(status, p=player):
        if status == QMediaPlayer.EndOfMedia:
            if p in _play._active:
                _play._active.remove(p)
            _play_sequence(rest, on_complete)
    player.mediaStatusChanged.connect(_on_status)
    player.play()



# ──────────────────────────────────────────────────────────────────
#  Shared hero panel (same gradient as home page)
# ──────────────────────────────────────────────────────────────────
class _HeroPanel(QWidget):
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0.0, QColor("#8B3A2E"))
        grad.setColorAt(1.0, QColor("#5A1F16"))
        p.fillRect(self.rect(), grad)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 18))
        p.drawEllipse(self.width() - 120, -80, 260, 260)
        p.setBrush(QColor(255, 255, 255, 12))
        p.drawEllipse(-80, self.height() - 150, 280, 280)
        p.setBrush(QColor("#D4A017"))
        p.drawRect(0, self.height() - 6, self.width(), 6)


# ──────────────────────────────────────────────────────────────────
#  Fade-in label helper
# ──────────────────────────────────────────────────────────────────
class _FadeInLabel(QLabel):
    """QLabel that fades in from transparent to opaque when play() is called."""
    def __init__(self, text="", duration=600, parent=None):
        super().__init__(text, parent)
        self._duration = duration
        self._fx = QGraphicsOpacityEffect(self)
        self._fx.setOpacity(0.0)
        self.setGraphicsEffect(self._fx)
        self._anim = QPropertyAnimation(self._fx, b"opacity", self)
        self._anim.setDuration(self._duration)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

    def play(self, delay=0):
        self._fx.setOpacity(0.0)
        if delay > 0:
            QTimer.singleShot(delay, self._anim.start)
        else:
            self._anim.start()


class _MicLabelProxy(QLabel):
    """Invisible QLabel whose setText() is also forwarded to MicImageButton."""
    def __init__(self, mic_btn):
        super().__init__()
        self._mic_btn = mic_btn
        self.setVisible(False)

    def setText(self, text: str):
        super().setText(text)
        self._mic_btn.set_label(text)


# ==========================================================
# Voice worker
# ==========================================================
class InitialVoiceWorker(QThread):
    status_changed = Signal(str)
    transcription_ready = Signal(str)
    error = Signal(str)

    _cached_model = None

    def __init__(self, duration_seconds=5, whisper_model_name="small", is_kriol=False):
        super().__init__()
        self.duration_seconds = duration_seconds
        self.whisper_model_name = whisper_model_name
        self.is_kriol = is_kriol
        self._cancelled = False

    def cancel(self):
        """Request cooperative cancellation. Safe to call from the main thread."""
        self._cancelled = True
        try:
            import sounddevice as sd
            sd.stop()   # unblocks sd.wait() immediately
        except Exception:
            pass

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
            sd.wait()   # cancel() calls sd.stop() to unblock this

            if self._cancelled:
                return   # exit silently — no signals emitted

            self.status_changed.emit("processing")

            temp_path = Path(tempfile.gettempdir()) / "saca_initial_voice.wav"
            write(str(temp_path), sample_rate, audio)

            if self._cancelled:
                return

            try:
                import whisper
            except Exception:
                self.error.emit("Whisper is not installed.")
                return

            if InitialVoiceWorker._cached_model is None:
                InitialVoiceWorker._cached_model = whisper.load_model(self.whisper_model_name)

            if self._cancelled:
                return

            _KRIOL_PROMPT = (
                "Mi garra fiva. Mi garra beli pen. Mi garra hedek. Mi garra kof. "
                "Mi garra soa trot. Mi garra wota nos. Mi garra ches pen. "
                "Mi no ken brij. Mi gidibat. Mi fil sik. Mi garr strongpela pen. "
                "Mi garra strongpela ches pen en mi no ken brij en mi gidibat. "
                "Yuwai. Nomu. En. Fo. Tu dei."
            )

            transcribe_kwargs = dict(fp16=False)
            if self.is_kriol:
                # Use a Kriol prompt so Whisper outputs Kriol words, not English
                transcribe_kwargs["initial_prompt"] = _KRIOL_PROMPT
            else:
                transcribe_kwargs["language"] = "en"

            result = InitialVoiceWorker._cached_model.transcribe(
                str(temp_path), **transcribe_kwargs
            )
            text = (result.get("text") or "").strip()

            if self._cancelled:
                return

            if not text:
                self.error.emit("I could not hear clearly. Please try again.")
                return

            # For Kriol, remove Whisper's sentence punctuation so the raw
            # Kriol words are shown as one continuous phrase
            if self.is_kriol:
                import re as _re
                text = _re.sub(r"[.!?,;]+", "", text)
                text = _re.sub(r"\s+", " ", text).strip()

            self.transcription_ready.emit(text)

        except Exception as e:
            if not self._cancelled:
                self.error.emit(str(e))


class MicCircleButton(QAbstractButton):
    """
    Mic button that renders 'mic normal.png' with clear visual state feedback:
      ready      – normal image, subtle hover scale (+5%)
      listening  – red tint overlay + animated pulsing outer ring
      processing – dimmed + spinning arc overlay
      done       – green tint overlay
      error      – dark red tint overlay
    Press while listening → cancels recording.
    """

    _BASE_SIZE = 182

    # ── state colour config ──
    _STATE_TINT = {
        "ready":      None,
        "listening":  QColor(198, 50, 30, 80),    # warm red wash
        "processing": QColor(0, 0, 0, 80),         # dim
        "done":       QColor(40, 160, 80, 80),     # green wash
        "error":      QColor(177, 0, 0, 100),      # error red
    }
    _STATE_RING = {
        "ready":      None,
        "listening":  QColor(198, 50, 30, 220),    # bright red ring
        "processing": QColor(212, 160, 23, 180),   # amber ring
        "done":       QColor(40, 160, 80, 200),    # green ring
        "error":      QColor(177, 0, 0, 200),      # red ring
    }

    def __init__(self):
        super().__init__()

        self.state = "ready"
        self._label_text = ""

        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(self._BASE_SIZE, self._BASE_SIZE)
        # allow the widget to shrink/grow without clipping during hover
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Load image
        from src.utils.paths import asset_path
        img_path = str(asset_path("backgrounds", "mic normal.png"))
        self._pixmap = QPixmap(img_path)

        # ── hover scale ──
        self._scale = 1.0
        self._hover_anim = QPropertyAnimation(self, b"mic_scale", self)
        self._hover_anim.setDuration(160)
        self._hover_anim.setEasingCurve(QEasingCurve.OutCubic)

        # ── pulse ring for listening state ──
        self._pulse = 0.0          # 0.0 → 1.0 drives ring radius
        self._pulse_anim = QPropertyAnimation(self, b"pulse_val", self)
        self._pulse_anim.setDuration(900)
        self._pulse_anim.setStartValue(0.0)
        self._pulse_anim.setEndValue(1.0)
        self._pulse_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._pulse_anim.setLoopCount(-1)   # loop forever while listening

        # ── processing spin arc ──
        self._spin_angle = 0
        self._spin_timer = QTimer(self)
        self._spin_timer.setInterval(30)
        self._spin_timer.timeout.connect(self._tick_spin)

    # ── scale property ──
    def _get_scale(self): return self._scale
    def _set_scale(self, v):
        self._scale = v
        s = int(self._BASE_SIZE * v)
        self.setFixedSize(s, s)
    mic_scale = Property(float, _get_scale, _set_scale)

    # ── pulse property ──
    def _get_pulse(self): return self._pulse
    def _set_pulse(self, v):
        self._pulse = v
        self.update()
    pulse_val = Property(float, _get_pulse, _set_pulse)

    def _tick_spin(self):
        self._spin_angle = (self._spin_angle + 8) % 360
        self.update()

    # ── state management ──
    def set_state(self, state: str):
        self.state = state
        # stop all effects first
        self._pulse_anim.stop()
        self._spin_timer.stop()
        self._pulse = 0.0
        if state == "listening":
            self._pulse_anim.start()
        elif state == "processing":
            self._spin_timer.start()
        self.update()

    def set_label(self, text: str):
        self._label_text = text

    def _apply_state_style(self): pass

    # ── hover ──
    def enterEvent(self, event):
        if self.state == "ready":
            self._hover_anim.stop()
            self._hover_anim.setStartValue(self._scale)
            self._hover_anim.setEndValue(1.05)
            self._hover_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.state == "ready":
            self._hover_anim.stop()
            self._hover_anim.setStartValue(self._scale)
            self._hover_anim.setEndValue(1.0)
            self._hover_anim.start()
        super().leaveEvent(event)

    # ── paint ──
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2

        # 1. Pulsing outer ring (listening) – drawn BEHIND the image
        if self.state == "listening" and self._pulse > 0:
            ring_color = QColor(198, 50, 30, int(220 * (1.0 - self._pulse)))
            ring_pen = QPen(ring_color, 3)
            painter.setPen(ring_pen)
            painter.setBrush(Qt.NoBrush)
            expand = int(w * 0.18 * self._pulse)  # expands outward up to 18% of size
            r = min(w, h) // 2 + expand
            painter.drawEllipse(int(cx - r), int(cy - r), r * 2, r * 2)

        # 2. Mic image
        painter.drawPixmap(self.rect(), self._pixmap)

        # 3. State tint overlay
        tint = self._STATE_TINT.get(self.state)
        if tint:
            painter.setPen(Qt.NoPen)
            painter.setBrush(tint)
            r2 = min(w, h) // 2
            painter.drawEllipse(int(cx - r2), int(cy - r2), r2 * 2, r2 * 2)

        # 4. Processing spin arc
        if self.state == "processing":
            arc_pen = QPen(QColor(212, 160, 23, 230), 4)
            arc_pen.setCapStyle(Qt.RoundCap)
            painter.setPen(arc_pen)
            painter.setBrush(Qt.NoBrush)
            pad = int(w * 0.08)
            painter.drawArc(pad, pad, w - pad * 2, h - pad * 2,
                            (-self._spin_angle) * 16, 100 * 16)

        # 5. Solid ring border for non-ready states
        ring_col = self._STATE_RING.get(self.state)
        if ring_col and self.state != "listening":   # listening uses pulse
            rp = QPen(ring_col, 4)
            painter.setPen(rp)
            painter.setBrush(Qt.NoBrush)
            pad2 = 4
            painter.drawEllipse(pad2, pad2, w - pad2 * 2, h - pad2 * 2)






class InputPage(QWidget):
    back_clicked = Signal()
    emergency_clicked = Signal()
    submit_clicked = Signal(str)

    def __init__(self):
        super().__init__()
        self.strings = {}
        self.current_mode = "type"
        self._voice_worker = None

        # ── top-level horizontal split ──
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── LEFT hero panel ──
        self._hero = _HeroPanel()
        self._hero.setFixedWidth(300)
        self._hero.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        hero_layout = QVBoxLayout(self._hero)
        hero_layout.setContentsMargins(36, 44, 28, 36)
        hero_layout.setSpacing(0)

        self._hero_title = _FadeInLabel("Tell us\nhow you\nfeel", duration=700)
        self._hero_title.setObjectName("heroWelcome")
        self._hero_title.setWordWrap(True)

        self._hero_tag = QLabel("Every detail\nhelps.")
        self._hero_tag.setObjectName("heroTagline")
        self._hero_tag.setWordWrap(True)

        hero_layout.addStretch(1)
        hero_layout.addWidget(self._hero_title)
        hero_layout.addStretch(2)

        dot_row = QHBoxLayout()
        for c in ["#D4A017", "#C65D2E", "#F2E6D8"]:
            dot = QFrame()
            dot.setFixedSize(10, 10)
            dot.setStyleSheet(f"background:{c}; border-radius:5px;")
            dot_row.addWidget(dot)
            dot_row.addSpacing(6)
        dot_row.addStretch()
        hero_layout.addLayout(dot_row)
        hero_layout.addSpacing(24)

        # ── RIGHT content panel ──
        right = QWidget()
        right.setObjectName("homeRightPanel")
        right.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(40, 36, 40, 28)
        right_layout.setSpacing(0)

        # back button
        self.back_btn = QPushButton("← Back")
        self.back_btn.setObjectName("backLinkButton")
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
        self.back_btn.clicked.connect(_stop_all)
        self.back_btn.clicked.connect(self.back_clicked.emit)

        self._help_btn = HelpButton(
            en_title="Entering Your Symptoms",
            en_text="Tell us what symptoms you have.\n\n"
                    "• Press the microphone and speak clearly, OR\n"
                    "• Type your symptoms in the text box.\n\n"
                    "You can also tap the quick-select buttons to add common symptoms quickly.\n\n"
                    "When ready, press Next to continue.",
            kr_title="Putim Yu Simptom",
            kr_text="Telim mibala wanem simptom yu garrim.\n\n"
                    "• Pres maikrofon en tok klin, O\n"
                    "• Raidim simptom langa tekst boks.\n\n"
                    "Yu ken tapim kwik-jusum batnit blong aderim simptom kwiktaim.\n\n"
                    "Taim yu redi, pres Nekis blong gowin.",
        )
        top_row = QHBoxLayout()
        top_row.setSpacing(0)
        top_row.addWidget(self.back_btn, 0, Qt.AlignVCenter)
        top_row.addStretch()
        top_row.addWidget(self._help_btn, 0, Qt.AlignVCenter)
        right_layout.addLayout(top_row)
        right_layout.addSpacing(12)

        # heading
        self._page_heading = _FadeInLabel("What's wrong?", duration=700)
        self._page_heading.setObjectName("rightHeading")

        self._page_sub = QLabel("Describe your symptoms below")
        self._page_sub.setObjectName("rightSubheading")

        divider = QFrame()
        divider.setFixedHeight(3)
        divider.setObjectName("rightDivider")

        # mode stack (voice / type)
        self.mode_stack = QStackedWidget()
        self.mode_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.voice_page = self._build_voice_page()
        self.type_page  = self._build_type_page()

        self.mode_stack.addWidget(self.voice_page)
        self.mode_stack.addWidget(self.type_page)

        # bottom action bar
        btn_row = QHBoxLayout()
        btn_row.setSpacing(14)

        self.emergency_btn = QPushButton("⚠   Emergency")
        self.emergency_btn.setObjectName("homeEmergencyOutlineButton")
        self.emergency_btn.setCursor(Qt.PointingHandCursor)
        self.emergency_btn.setFixedHeight(52)
        self.emergency_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.emergency_btn.clicked.connect(_stop_all)
        self.emergency_btn.clicked.connect(self.emergency_clicked.emit)

        self.next_btn = QPushButton("Next  →")
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.setFixedHeight(52)
        self.next_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.submit_btn = self.next_btn
        btn_row.addWidget(self.emergency_btn)
        btn_row.addWidget(self.next_btn)

        _top = QHBoxLayout()
        _top.setSpacing(0)
        _top.addWidget(self.back_btn, 0, Qt.AlignVCenter)
        _top.addStretch()
        _top.addWidget(self._help_btn, 0, Qt.AlignVCenter)
        right_layout.addLayout(_top)
        right_layout.addSpacing(12)
        right_layout.addWidget(self._page_heading)
        right_layout.addSpacing(4)
        right_layout.addWidget(self._page_sub)
        right_layout.addSpacing(16)
        right_layout.addWidget(divider)
        right_layout.addSpacing(16)
        right_layout.addWidget(self.mode_stack, 1)
        right_layout.addSpacing(16)
        right_layout.addLayout(btn_row)

        root.addWidget(self._hero)
        root.addWidget(right, 1)

        self.next_btn.clicked.connect(_stop_all)
        self.next_btn.clicked.connect(self._submit)
        self._update_mode_ui()
        self._update_next_button()

    def play_entry_animations(self):
        """Called by MainWindow after the page becomes visible (post curtain-reveal)."""
        QTimer.singleShot(60,  lambda: self._hero_title.play())
        QTimer.singleShot(180, lambda: self._page_heading.play())
        if self.current_mode == "voice":
            audio = "Kriol-Speak.mp3" if self._is_kriol() else "English-Speak.mp3"
            QTimer.singleShot(400, lambda: _play_sequence([audio], on_complete=self._animate_mic_btn))
        elif self.current_mode == "type":
            audio = "Kriol-typing.mp3" if self._is_kriol() else "English-typing.mp3"
            QTimer.singleShot(400, lambda: _play_sequence([audio], on_complete=self._animate_type_box))

    def _animate_type_box(self):
        """Nudge the text input box down then spring back."""
        box = self.input_box
        orig = box.geometry()
        nudged = orig.translated(0, 10)
        a1 = QPropertyAnimation(box, b"geometry", box)
        a1.setDuration(120)
        a1.setStartValue(orig)
        a1.setEndValue(nudged)
        a1.setEasingCurve(QEasingCurve.OutQuad)
        a2 = QPropertyAnimation(box, b"geometry", box)
        a2.setDuration(240)
        a2.setStartValue(nudged)
        a2.setEndValue(orig)
        a2.setEasingCurve(QEasingCurve.OutBack)
        a1.finished.connect(a2.start)
        a1.start()
        box._nudge_a1 = a1
        box._nudge_a2 = a2

    def _animate_mic_btn(self):
        """Nudge the mic button down then spring back — same pattern as mode cards."""
        btn = self.mic_btn
        orig = btn.geometry()
        nudged = orig.translated(0, 12)
        a1 = QPropertyAnimation(btn, b"geometry", btn)
        a1.setDuration(130)
        a1.setStartValue(orig)
        a1.setEndValue(nudged)
        a1.setEasingCurve(QEasingCurve.OutQuad)
        a2 = QPropertyAnimation(btn, b"geometry", btn)
        a2.setDuration(260)
        a2.setStartValue(nudged)
        a2.setEndValue(orig)
        a2.setEasingCurve(QEasingCurve.OutBack)
        a1.finished.connect(a2.start)
        a1.start()
        self._mic_nudge_a1 = a1
        self._mic_nudge_a2 = a2

    # --------------------------------------------------
    # Type page
    # --------------------------------------------------
    def _build_type_page(self):
        page = QWidget()
        page.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.setAlignment(Qt.AlignTop)

        self.section_label = QLabel("How do you feel?")
        self.section_label.setStyleSheet(
            "color:#2D1810; font-size:17px; font-weight:900; background:transparent;"
        )
        layout.addWidget(self.section_label)

        self.input_box = QTextEdit()
        self.input_box.setPlaceholderText("Type your symptoms here...")
        self.input_box.setFixedHeight(150)
        self.input_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.input_box.setStyleSheet("""
            QTextEdit {
                background-color: #FFFFFF;
                border: 2px solid #E1D4C6;
                border-radius: 16px;
                padding: 14px 18px;
                color: #2D1810;
                font-size: 17px;
                font-weight: 700;
            }
            QTextEdit:focus { border: 2px solid #8B3A2E; }
        """)
        self.input_box.textChanged.connect(self._update_next_button)
        layout.addWidget(self.input_box)

        self.type_box  = self.input_box
        self.text_input = self.input_box

        self.quick_label = QLabel("Quick select:")
        self.quick_label.setStyleSheet(
            "color:#2D1810; font-size:16px; font-weight:900; background:transparent;"
        )
        layout.addWidget(self.quick_label)

        self.quick_area  = QVBoxLayout()
        self.quick_area.setSpacing(10)
        self.quick_row_1 = QHBoxLayout(); self.quick_row_1.setSpacing(10)
        self.quick_row_2 = QHBoxLayout(); self.quick_row_2.setSpacing(10)
        self.quick_area.addLayout(self.quick_row_1)
        self.quick_area.addLayout(self.quick_row_2)
        layout.addLayout(self.quick_area)

        self.quick_buttons = []
        row_1 = [("Headache",130),("Fever",90),("Cough",100),("Stomach pain",155),("Sore throat",140)]
        row_2 = [("Body ache",135),("Tired",90),("Dizzy",90)]
        for text, width in row_1:
            btn = self._make_quick_button(text, width)
            self.quick_row_1.addWidget(btn); self.quick_buttons.append(btn)
        self.quick_row_1.addStretch()
        for text, width in row_2:
            btn = self._make_quick_button(text, width)
            self.quick_row_2.addWidget(btn); self.quick_buttons.append(btn)
        self.quick_row_2.addStretch()

        return page

    # --------------------------------------------------
    # Speak / voice page
    # --------------------------------------------------
    def _build_voice_page(self):
        page = QWidget()
        page.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignTop)

        # Mic button — centred (created first so proxy can reference it)
        self.mic_btn = MicCircleButton()
        self.mic_btn.clicked.connect(self._handle_mic_click)

        # Proxy label: invisible widget; all setText() calls forward into the button
        self.voice_status_label = _MicLabelProxy(self.mic_btn)

        layout.addStretch(1)
        mic_row = QHBoxLayout()
        mic_row.addStretch()
        mic_row.addWidget(self.mic_btn)
        mic_row.addStretch()
        layout.addLayout(mic_row)
        layout.addSpacing(12)

        # Primary status label (big, bold — changes with state)
        self.tap_hint_label = QLabel("Tap the mic to speak")
        self.tap_hint_label.setAlignment(Qt.AlignCenter)
        self.tap_hint_label.setStyleSheet(
            "color:#8B3A2E; font-size:16px; font-weight:900;"
            " letter-spacing:0.3px; background:transparent;"
        )
        tap_row = QHBoxLayout()
        tap_row.addStretch()
        tap_row.addWidget(self.tap_hint_label)
        tap_row.addStretch()
        layout.addLayout(tap_row)
        layout.addSpacing(6)

        # Secondary helper hint (smaller — extra context / cancel hint)
        self.voice_helper_label = QLabel("")
        self.voice_helper_label.setAlignment(Qt.AlignCenter)
        self.voice_helper_label.setWordWrap(True)
        self.voice_helper_label.setFixedHeight(36)
        self.voice_helper_label.setStyleSheet(
            "color:#5A1F16; font-size:13px; font-weight:600; background:transparent;"
        )
        layout.addWidget(self.voice_helper_label)
        layout.addSpacing(22)

        # Thin accent divider
        voice_divider = QFrame()
        voice_divider.setFixedHeight(2)
        voice_divider.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            " stop:0 transparent, stop:0.3 #8B3A2E, stop:0.7 #8B3A2E, stop:1 transparent);"
            " border:none;"
        )
        layout.addWidget(voice_divider)
        layout.addSpacing(16)

        # Transcript label
        self._transcript_label = QLabel("Your words:")
        self._transcript_label.setStyleSheet(
            "color:#6B4E3D; font-size:13px; font-weight:800; background:transparent;"
        )
        layout.addWidget(self._transcript_label)
        layout.addSpacing(6)

        # Transcript text box
        self.voice_text_box = QTextEdit()
        self.voice_text_box.setPlaceholderText("Your words will appear here after speaking...")
        self.voice_text_box.setFixedHeight(100)
        self.voice_text_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.voice_text_box.setStyleSheet("""
            QTextEdit {
                background-color: #FFFFFF;
                border: 2px solid #E1D4C6;
                border-radius: 14px;
                padding: 12px 16px;
                color: #2D1810;
                font-size: 16px;
                font-weight: 700;
            }
            QTextEdit:focus { border: 2px solid #8B3A2E; }
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
        btn.setFixedHeight(42)
        btn.setMinimumWidth(width)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #FDF3EE;
                color: #8B3A2E;
                border: 2px solid #E1C4B8;
                border-radius: 18px;
                font-size: 14px;
                font-weight: 900;
                padding: 0px 14px;
            }
            QPushButton:hover {
                background-color: #8B3A2E;
                color: #FFFFFF;
                border: 2px solid #8B3A2E;
            }
            QPushButton:pressed { background-color: #6B2A1E; }
        """)
        btn.clicked.connect(lambda checked=False, s=text: self._add_symptom(s))
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
        # If already recording → cancel
        if self._voice_worker is not None and self._voice_worker.isRunning():
            self._stop_worker()
            self.mic_btn.set_state("ready")
            self.voice_status_label.setText("")
            self.tap_hint_label.setText("Tap the mic to speak")
            self.voice_helper_label.setText(
                "Rekoding stotem." if self._is_kriol() else "Recording cancelled."
            )
            self.mic_btn.setEnabled(True)
            return

        # keep button enabled so user can cancel
        self.mic_btn.set_state("listening")

        self.tap_hint_label.setText(
            "🎙  Listening…" if not self._is_kriol() else "🎙  Lisin…"
        )
        self.voice_status_label.setText(
            "Lisin..." if self._is_kriol() else "Listening..."
        )
        self.voice_helper_label.setText(
            "Tap the mic again to cancel" if not self._is_kriol()
            else "Tapm maik gen blong stotem."
        )

        self.voice_text_box.setPlaceholderText(
            "Lisin nau..." if self._is_kriol() else "Listening now..."
        )

        self._voice_worker = InitialVoiceWorker(duration_seconds=8 if self._is_kriol() else 5, whisper_model_name="small", is_kriol=self._is_kriol())
        self._voice_worker.status_changed.connect(self._on_voice_status)
        self._voice_worker.transcription_ready.connect(self._on_voice_text)
        self._voice_worker.error.connect(self._on_voice_error)
        self._voice_worker.finished.connect(self._on_voice_finished)
        self._voice_worker.start()

    def _stop_worker(self):
        """Cooperatively cancel the voice worker without killing the thread."""
        w = self._voice_worker
        self._voice_worker = None   # clear reference FIRST
        if w is None:
            return
        try:
            w.status_changed.disconnect()
            w.transcription_ready.disconnect()
            w.error.disconnect()
            w.finished.disconnect()
        except RuntimeError:
            pass
        w.cancel()          # sets flag + calls sd.stop() — safe, no segfault
        # do NOT call w.wait() on the main thread; let it finish in background

    def _on_voice_status(self, status: str):
        if status == "listening":
            self.mic_btn.set_state("listening")
            self.voice_status_label.setText(
                "Lisin..." if self._is_kriol() else "Listening..."
            )

        elif status == "processing":
            self.mic_btn.set_state("processing")
            self.tap_hint_label.setText(
                "⏳  Processing…" if not self._is_kriol() else "⏳  Wokabat…"
            )
            self.voice_status_label.setText(
                "Wokabat..." if self._is_kriol() else "Processing..."
            )
            self.voice_helper_label.setText(
                "Wet liklik. Mi tanim yu vois." if self._is_kriol()
                else "Please wait — converting your voice."
            )

    def _on_voice_text(self, text: str):
        self.mic_btn.set_state("done")
        self.tap_hint_label.setText(
            "✓  Got it!" if not self._is_kriol() else "✓  Ansa faindim!"
        )
        self.voice_status_label.setText(
            "Ansa bin faindim" if self._is_kriol() else "Voice detected"
        )
        self.voice_helper_label.setText(
            "Yu ken nekis, o tap maik gen." if self._is_kriol()
            else "Tap mic again to re-record, or press Next."
        )

        self.voice_text_box.setPlainText(text)

        cursor = self.voice_text_box.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.voice_text_box.setTextCursor(cursor)

        self._update_next_button()

    def _on_voice_error(self, message: str):
        self.mic_btn.set_state("error")
        self.tap_hint_label.setText(
            "⚠  Something went wrong" if not self._is_kriol() else "⚠  Samting rong"
        )
        self.voice_status_label.setText(
            "Trai agen" if self._is_kriol() else "Try again"
        )
        self.voice_helper_label.setText(message)

    def _on_voice_finished(self):
        # Guard: if worker was already nulled (cancelled), do nothing
        if self._voice_worker is None:
            return
        self._voice_worker = None

        self.mic_btn.setEnabled(True)
        self.mic_btn.setCursor(Qt.PointingHandCursor)

        if self.mic_btn.state != "done" and self.mic_btn.state != "error":
            self.tap_hint_label.setText("Tap the mic to speak")
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
        self._help_btn.set_kriol(self._is_kriol())
        self._update_mode_ui()

    def _is_kriol(self) -> bool:
        return self.strings.get("back", "Back").strip().lower() == "bek"

    def _update_mode_ui(self):
        is_kriol = self._is_kriol()

        if self.current_mode == "voice":
            self.mode_stack.setCurrentWidget(self.voice_page)
            self._page_heading.setText("Wanem rong?" if is_kriol else "What's wrong?")
            self._page_sub.setText(
                "Tapim maik en tok klia" if is_kriol else "Tap the mic and speak clearly"
            )
            self._hero_title.setText("Tok nao\nen wi\nbai lisin" if is_kriol else "Speak up\nand we\nwill listen")
            self._hero_tag.setText("Yu vois\nimpoten." if is_kriol else "Your voice\nmatters.")
            self.voice_status_label.setText("Tapim maik" if is_kriol else "Tap the mic")
            self.voice_helper_label.setText("")
            self._transcript_label.setText("Yu wod:" if is_kriol else "Your words:")
            self.voice_text_box.setPlaceholderText(
                "Yu tok bai so iya..." if is_kriol else "Your words will show here..."
            )
            self.mic_btn.set_state("ready")
        else:
            self.mode_stack.setCurrentWidget(self.type_page)
            self._page_heading.setText("Raitim simptom" if is_kriol else "Type your symptoms")
            self._page_sub.setText(
                "Raidim wei yu fil" if is_kriol else "Write what you feel below"
            )
            self._hero_title.setText("Raidim\nwei yu\nfil" if is_kriol else "Tell us\nhow you\nfeel")
            self._hero_tag.setText("Evri deteil\nhelpim." if is_kriol else "Every detail\nhelps.")
            self.input_box.setPlaceholderText(
                "Raitim yu simptom iya..." if is_kriol else "Type your symptoms here..."
            )

        self.section_label.setText("Wanim yu fil?" if is_kriol else "How do you feel?")
        self.quick_label.setText("Kwik simptom:" if is_kriol else "Quick select:")
        self.back_btn.setText("← Bek" if is_kriol else "← Back")
        self.emergency_btn.setText("⚠   Imijensi" if is_kriol else "⚠   Emergency")
        self.next_btn.setText("Nekis  →" if is_kriol else "Next  →")

        quick_labels = [
            ("Hedake" if is_kriol else "Headache"),
            ("Fiba"   if is_kriol else "Fever"),
            ("Kof"    if is_kriol else "Cough"),
            ("Beli pein"  if is_kriol else "Stomach pain"),
            ("Throt pein" if is_kriol else "Sore throat"),
            ("Bodi pein"  if is_kriol else "Body ache"),
            ("Taid"  if is_kriol else "Tired"),
            ("Dizi"  if is_kriol else "Dizzy"),
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
                    background-color: #8B3A2E;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 14px;
                    font-size: 17px;
                    font-weight: 900;
                    padding: 12px 18px;
                }
                QPushButton:hover { background-color: #6B2A1E; }
            """)
        else:
            self.next_btn.setStyleSheet("""
                QPushButton {
                    background-color: #D4B8B0;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 14px;
                    font-size: 17px;
                    font-weight: 900;
                    padding: 12px 18px;
                }
            """)

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