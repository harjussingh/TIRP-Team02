package com.example.saca.util

import android.content.Context
import android.media.MediaPlayer
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import com.example.saca.model.Language
import java.util.Locale

// NarrationManager — single audio engine for all screens
// English: Android TTS
// Kriol: recorded audio files (res/raw/) — wired in later phase
class NarrationManager(private val context: Context) {

    private var tts: TextToSpeech? = null
    private var ttsReady = false
    private var mediaPlayer: MediaPlayer? = null

    // Current playback state — screens observe this to update play button UI
    var isPlaying: Boolean = false
        private set

    var onPlaybackStarted: (() -> Unit)? = null
    var onPlaybackStopped: (() -> Unit)? = null

    init {
        initialiseTts()
    }

    private fun initialiseTts() {
        tts = TextToSpeech(context) { status ->
            if (status == TextToSpeech.SUCCESS) {
                tts?.language = Locale("en", "AU")  // Australian English
                ttsReady = true
            }
        }
    }

    // ── Main entry point — called by all screens ──────────────────────────
    // text     : the headline or instruction to narrate
    // language : EN uses TTS, KRIOL uses recorded audio (TODO)
    // screenKey: unique id per screen — used as raw resource name for Kriol
    //            e.g. "language_select", "input_mode", "symptom_input"
    //            Kriol audio files will be named: kriol_language_select.mp3 etc.
    fun narrate(text: String, language: Language, screenKey: String = "") {
        stop() // stop any current playback before starting new

        when (language) {
            Language.ENGLISH -> narrateWithTts(text)
            Language.KRIOL   -> narrateKriol(screenKey)
        }
    }

    private fun narrateWithTts(text: String) {
        if (!ttsReady || tts == null) return

        tts?.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
            override fun onStart(utteranceId: String?) {
                isPlaying = true
                onPlaybackStarted?.invoke()
            }
            override fun onDone(utteranceId: String?) {
                isPlaying = false
                onPlaybackStopped?.invoke()
            }
            override fun onError(utteranceId: String?) {
                isPlaying = false
                onPlaybackStopped?.invoke()
            }
        })

        tts?.speak(
            text,
            TextToSpeech.QUEUE_FLUSH,
            null,
            "SACA_NARRATION"
        )
    }

    private fun narrateKriol(screenKey: String) {
        // ── TODO: Kriol recorded audio ────────────────────────────────────
        // When Kriol audio files are ready:
        // 1. Add .mp3 files to res/raw/ named: kriol_{screenKey}.mp3
        //    e.g. kriol_language_select.mp3, kriol_input_mode.mp3
        // 2. Uncomment and use the block below:
        //
        // val resId = context.resources.getIdentifier(
        //     "kriol_$screenKey", "raw", context.packageName
        // )
        // if (resId == 0) return  // file not found — silent fail
        //
        // mediaPlayer = MediaPlayer.create(context, resId).also { player ->
        //     player.setOnPreparedListener {
        //         isPlaying = true
        //         onPlaybackStarted?.invoke()
        //         player.start()
        //     }
        //     player.setOnCompletionListener {
        //         isPlaying = false
        //         onPlaybackStopped?.invoke()
        //         player.release()
        //         mediaPlayer = null
        //     }
        // }
        // ─────────────────────────────────────────────────────────────────
        android.util.Log.d("Narration", "Kriol audio not yet recorded for: $screenKey")
    }

    fun stop() {
        tts?.stop()
        mediaPlayer?.stop()
        mediaPlayer?.release()
        mediaPlayer = null
        isPlaying = false
        onPlaybackStopped?.invoke()
    }

    fun release() {
        stop()
        tts?.shutdown()
        tts = null
        ttsReady = false
    }
}