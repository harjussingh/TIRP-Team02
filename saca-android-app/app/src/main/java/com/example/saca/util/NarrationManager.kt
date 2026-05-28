package com.example.saca.util

import android.content.Context
import android.media.MediaPlayer
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import com.example.saca.model.Language
import java.util.Locale

// NarrationManager — single audio engine for all screens
// English: Android TTS
// Kriol: recorded audio files (res/raw/)
class NarrationManager(private val context: Context) {

    private var tts: TextToSpeech? = null
    private var ttsReady = false

    // ── MediaPlayer (Kriol MP3 only) ──────────────────────────────────────
    private var mediaPlayer: MediaPlayer? = null

    // ── Playback state ────────────────────────────────────────────────────
    var isPlaying: Boolean = false
        private set

    var onPlaybackStarted: (() -> Unit)? = null
    var onPlaybackStopped: (() -> Unit)? = null

    // ── screenKey → res/raw resource name ─────────────────────────────────
    // Only the files that actually exist in res/raw/ are mapped here.
    // Any key NOT in this map → silent skip (file not recorded yet).
    private val screenKeyToRawName: Map<String, String> = mapOf(
        // ── Available now ─────────────────────────────────────────────────
        "speak"             to "kriol_speak",
        "speech_input"      to "kriol_speak",        // legacy alias
        "typing"            to "kriol_typing",
        "text_input"        to "kriol_typing",        // legacy alias
        "body_map"          to "kriol_body_map",
        "symptom_input"     to "kriol_body_map",     // alias → body map audio
        "pictogram_input"   to "kriol_body_map",     // alias → body map audio
        "result_mild"       to "kriol_result_mild",
        "result_moderate"   to "kriol_result_moderate",
        "result_critical"   to "kriol_result_critical",
        "result"            to "kriol_result_mild",  // generic result → mild
        "language_select"   to "kriol_language_select",
    )

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

    // ── Main entry point — called by every screen ─────────────────────────
    fun narrate(text: String, language: Language, screenKey: String = "") {
        stop()
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
        // Resolve raw name — map lookup first, then convention fallback
        val rawName = screenKeyToRawName[screenKey]
            ?: run {
                android.util.Log.d(
                    "NarrationManager",
                    "No Kriol audio mapped for screenKey='$screenKey' — skipping"
                )
                return
            }

        val resId = context.resources.getIdentifier(rawName, "raw", context.packageName)

        android.util.Log.d(
            "NarrationManager",
            "Kriol: screenKey='$screenKey' → rawName='$rawName' → resId=$resId"
        )

        if (resId == 0) {
            android.util.Log.w(
                "NarrationManager",
                "File not found in res/raw/: $rawName.mp3"
            )
            return
        }

        try {
            mediaPlayer = MediaPlayer.create(context, resId)?.also { player ->
                player.setOnPreparedListener {
                    isPlaying = true
                    onPlaybackStarted?.invoke()
                    player.start()
                    android.util.Log.d("NarrationManager", "Playing: $rawName")
                }
                player.setOnCompletionListener {
                    isPlaying = false
                    onPlaybackStopped?.invoke()
                    player.release()
                    mediaPlayer = null
                    android.util.Log.d("NarrationManager", "Done: $rawName")
                }
                player.setOnErrorListener { _, what, extra ->
                    android.util.Log.e(
                        "NarrationManager",
                        "MediaPlayer error $rawName: what=$what extra=$extra"
                    )
                    isPlaying = false
                    onPlaybackStopped?.invoke()
                    mediaPlayer = null
                    true
                }
            }

            if (mediaPlayer == null) {
                android.util.Log.e(
                    "NarrationManager",
                    "MediaPlayer.create() returned null for $rawName — " +
                    "check file format (must be valid MP3/AAC)"
                )
            }

        } catch (e: Exception) {
            android.util.Log.e("NarrationManager", "Exception playing $rawName: ${e.message}")
            isPlaying = false
        }
    }

    // ── Sequence: play multiple Kriol keys in order ───────────────────────
    /**
     * Plays a chain of Kriol audio files in order, then calls [onComplete].
     * Missing files are silently skipped — the chain continues.
     *
     * Example (follow-up screen, first question):
     *   narrationManager.narrateKriolSequence(
     *       listOf("followup_intro", "followup_prefix"),
     *       onComplete = { animateButtons() }
     *   )
     */
    fun narrateKriolSequence(screenKeys: List<String>, onComplete: (() -> Unit)? = null) {
        stop()
        playNext(screenKeys, 0, onComplete)
    }

    private fun playNext(keys: List<String>, index: Int, onComplete: (() -> Unit)?) {
        if (index >= keys.size) {
            onComplete?.invoke()
            return
        }

        val rawName = screenKeyToRawName[keys[index]]
        if (rawName == null) {
            android.util.Log.d("NarrationManager", "Sequence: skipping unmapped key '${keys[index]}'")
            playNext(keys, index + 1, onComplete)
            return
        }

        val resId = context.resources.getIdentifier(rawName, "raw", context.packageName)
        if (resId == 0) {
            android.util.Log.d("NarrationManager", "Sequence: skipping missing file $rawName")
            playNext(keys, index + 1, onComplete)
            return
        }

        try {
            mediaPlayer = MediaPlayer.create(context, resId)?.also { player ->
                player.setOnPreparedListener {
                    isPlaying = true
                    onPlaybackStarted?.invoke()
                    player.start()
                }
                player.setOnCompletionListener {
                    isPlaying = false
                    player.release()
                    mediaPlayer = null
                    playNext(keys, index + 1, onComplete)
                }
                player.setOnErrorListener { _, what, extra ->
                    android.util.Log.e("NarrationManager", "Sequence error $rawName: what=$what extra=$extra")
                    isPlaying = false
                    mediaPlayer = null
                    playNext(keys, index + 1, onComplete)
                    true
                }
            }
        } catch (e: Exception) {
            android.util.Log.e("NarrationManager", "Sequence play failed $rawName: ${e.message}")
            playNext(keys, index + 1, onComplete)
        }
    }

    // ── Stop all playback ─────────────────────────────────────────────────
    fun stop() {
        tts?.stop()
        try {
            mediaPlayer?.stop()
            mediaPlayer?.release()
        } catch (_: Exception) {}
        mediaPlayer = null
        isPlaying = false
        onPlaybackStopped?.invoke()
    }

    // ── Lifecycle ─────────────────────────────────────────────────────────
    fun release() {
        stop()
        tts?.shutdown()
        tts = null
        ttsReady = false
    }
}