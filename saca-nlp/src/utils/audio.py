"""
Shared audio playback utilities for SACA.
All pages import _play / _play_sequence / stop_all from here so there is
a single active-player list and stop_all() can silence everything at once.
"""
from __future__ import annotations

import os

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput


def _audio_path(filename: str) -> str:
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(
        os.path.join(base, "..", "..", "assets", "audio", filename)
    )


# Shared list of every in-flight QMediaPlayer instance
_active: list[QMediaPlayer] = []

# Track any running TTS subprocess (macOS 'say' / pyttsx3)
_tts_proc = None

# Set to True by stop_all(); cleared on next play so callbacks don't fire
_stopped: bool = False


def stop_all() -> None:
    """Stop and discard every currently playing audio player and kill TTS."""
    global _tts_proc, _stopped
    _stopped = True
    for p in list(_active):
        try:
            p.stop()
        except Exception:
            pass
    _active.clear()
    if _tts_proc is not None:
        try:
            _tts_proc.kill()
        except Exception:
            pass
        _tts_proc = None


def play(filename: str) -> None:
    """Fire-and-forget single-file playback."""
    global _stopped
    _stopped = False
    path = _audio_path(filename)
    if not os.path.exists(path):
        return
    player = QMediaPlayer()
    audio_out = QAudioOutput()
    audio_out.setVolume(1.0)
    player.setAudioOutput(audio_out)
    player.setSource(QUrl.fromLocalFile(path))
    player._audio_out = audio_out
    _active.append(player)

    def _on_status(status: QMediaPlayer.MediaStatus, p=player):
        if status == QMediaPlayer.EndOfMedia:
            if p in _active:
                _active.remove(p)

    player.mediaStatusChanged.connect(_on_status)
    player.play()


def play_sequence(filenames: list[str], on_complete=None, _continuation: bool = False) -> None:
    """Play files one after another; call on_complete when the last one ends."""
    global _stopped
    # Reset the stopped flag only when starting a brand-new sequence (not
    # when called recursively for the next file in the chain).
    if not _continuation:
        _stopped = False
    if _stopped:
        return
    if not filenames:
        if on_complete:
            on_complete()
        return
    first, *rest = filenames
    path = _audio_path(first)
    if not os.path.exists(path):
        play_sequence(rest, on_complete, _continuation=True)   # skip missing, keep going
        return
    player = QMediaPlayer()
    audio_out = QAudioOutput()
    audio_out.setVolume(1.0)
    player.setAudioOutput(audio_out)
    player.setSource(QUrl.fromLocalFile(path))
    player._audio_out = audio_out
    _active.append(player)

    def _on_status(status: QMediaPlayer.MediaStatus, p=player):
        if status == QMediaPlayer.EndOfMedia:
            if p in _active:
                _active.remove(p)
            if not _stopped:
                play_sequence(rest, on_complete, _continuation=True)

    player.mediaStatusChanged.connect(_on_status)
    player.play()
