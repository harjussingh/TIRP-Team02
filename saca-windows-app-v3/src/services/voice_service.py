from __future__ import annotations

import tempfile
import wave
from pathlib import Path

from PySide6.QtCore import QByteArray, QBuffer, QIODevice, QObject, QThread, QTimer, Signal


class WhisperTranscriptionWorker(QThread):
    """Runs Whisper away from the UI thread so the interface does not freeze."""

    status = Signal(str)
    transcription_ready = Signal(str)
    error = Signal(str)

    def __init__(self, audio_path: str, model_name: str = "base"):
        super().__init__()
        self.audio_path = audio_path
        self.model_name = model_name

    def run(self) -> None:  # noqa: D401 - QThread override
        try:
            self.status.emit("Converting speech to text...")

            # Prefer the uploaded NLP module's bilingual Whisper processor because
            # it includes medical vocabulary hints, Kriol vocabulary hints, language
            # detection, and Kriol-to-English post-processing support.
            try:
                from nlp.voice_processor import VoiceProcessor

                processor = VoiceProcessor(model_name=self.model_name)
                result = processor.transcribe_bilingual(self.audio_path)
                text = str(result.get("original_text") or result.get("translated_text") or "").strip()
            except ImportError:
                self.error.emit("Speech-to-text is not ready. Type below.")
                return
            except Exception:
                # Fallback to direct Whisper if the team processor is unavailable
                # but Whisper itself is installed.
                try:
                    import whisper  # type: ignore
                except Exception:
                    self.error.emit("Speech-to-text is not ready. Type below.")
                    return

                model = whisper.load_model(self.model_name)
                result = model.transcribe(
                    self.audio_path,
                    language="en",
                    fp16=False,
                    temperature=0.0,
                    initial_prompt=(
                        "Medical symptoms: fever, cough, headache, stomach pain, chest pain, "
                        "sore throat, dizzy, vomiting, breathing problem, shortness of breath. "
                        "Kriol words: mi garr hedache, mi garr hot-bodi, mi garr kof, "
                        "mi garr beli pein, sowa trot, pein, no garr, bat, en, disi."
                    ),
                )
                text = str(result.get("text", "")).strip()

            if text:
                self.transcription_ready.emit(text)
            else:
                self.error.emit("I could not hear clear words. Please type your symptoms.")

        except Exception as exc:
            self.error.emit(f"Voice transcription failed. Please type your symptoms. ({exc})")


class VoiceService(QObject):
    """Record microphone audio and optionally transcribe it with Whisper.

    This service uses PySide6 QtMultimedia for recording so it does not require
    PyAudio. If QtMultimedia or Whisper is unavailable, the UI still works and
    asks the user to type the spoken words.
    """

    status = Signal(str)
    recording_started = Signal()
    recording_stopped = Signal(str)
    transcription_ready = Signal(str)
    error = Signal(str)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self.audio_source = None
        self.buffer: QBuffer | None = None
        self.audio_bytes = QByteArray()
        self.is_recording = False
        self.worker: WhisperTranscriptionWorker | None = None
        self.output_path = Path(tempfile.gettempdir()) / "saca_voice_input.wav"

    def start_recording(self, seconds: int = 5) -> None:
        if self.is_recording:
            self.stop_recording()
            return

        try:
            from PySide6.QtMultimedia import QAudioFormat, QAudioSource, QMediaDevices
        except Exception:
            self.error.emit(
                "Microphone recording is not available in this PySide6 install. Type your symptoms."
            )
            return

        device = QMediaDevices.defaultAudioInput()
        if device.isNull():
            self.error.emit("No microphone was found. Type your symptoms instead.")
            return

        fmt = QAudioFormat()
        fmt.setSampleRate(16000)
        fmt.setChannelCount(1)
        fmt.setSampleFormat(QAudioFormat.Int16)

        if not device.isFormatSupported(fmt):
            fmt = device.preferredFormat()

        self.audio_bytes = QByteArray()
        self.buffer = QBuffer()
        self.buffer.setBuffer(self.audio_bytes)
        self.buffer.open(QIODevice.WriteOnly)

        self.audio_source = QAudioSource(device, fmt, self)
        self.audio_source.start(self.buffer)
        self.is_recording = True

        self.status.emit("Listening... speak now")
        self.recording_started.emit()
        QTimer.singleShot(seconds * 1000, self.stop_recording)

    def stop_recording(self) -> None:
        if not self.is_recording:
            return

        self.is_recording = False

        fmt = None
        if self.audio_source is not None:
            fmt = self.audio_source.format()
            self.audio_source.stop()
            self.audio_source.deleteLater()
            self.audio_source = None

        if self.buffer is not None:
            self.buffer.close()
            self.buffer = None

        raw = bytes(self.audio_bytes)
        if not raw:
            self.error.emit("No audio was recorded. Please try again or type your symptoms.")
            return

        if fmt is None:
            self.error.emit("Audio format was unavailable. Please type your symptoms.")
            return

        try:
            self._write_wav(self.output_path, raw, fmt.sampleRate(), fmt.channelCount())
        except Exception as exc:
            self.error.emit(f"Could not save microphone audio. Please type your symptoms. ({exc})")
            return

        self.status.emit("Recording finished")
        self.recording_stopped.emit(str(self.output_path))
        self._start_transcription(str(self.output_path))

    def _write_wav(self, path: Path, raw: bytes, sample_rate: int, channels: int) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(path), "wb") as wav:
            wav.setnchannels(max(channels, 1))
            wav.setsampwidth(2)  # Int16
            wav.setframerate(sample_rate or 16000)
            wav.writeframes(raw)

    def _start_transcription(self, audio_path: str) -> None:
        self.worker = WhisperTranscriptionWorker(audio_path=audio_path, model_name="small")
        self.worker.status.connect(self.status.emit)
        self.worker.transcription_ready.connect(self.transcription_ready.emit)
        self.worker.error.connect(self.error.emit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()
