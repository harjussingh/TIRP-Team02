package com.example.saca.util

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import com.example.saca.model.Language
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

class SpeechRecognitionManager(private val context: Context) {

    private var speechRecognizer: SpeechRecognizer? = null
    
    private val _transcript = MutableStateFlow("")
    val transcript: StateFlow<String> = _transcript.asStateFlow()
    
    private val _isListening = MutableStateFlow(false)
    val isListening: StateFlow<Boolean> = _isListening.asStateFlow()
    
    private val _audioLevel = MutableStateFlow(0f)
    val audioLevel: StateFlow<Float> = _audioLevel.asStateFlow()
    
    private val _error = MutableStateFlow<String?>(null)
    val error: StateFlow<String?> = _error.asStateFlow()
    
    private val _isReady = MutableStateFlow(true)
    val isReady: StateFlow<Boolean> = _isReady.asStateFlow()

    init {
        initializeSpeechRecognizer()
    }

    private fun initializeSpeechRecognizer() {
        if (SpeechRecognizer.isRecognitionAvailable(context)) {
            speechRecognizer = SpeechRecognizer.createSpeechRecognizer(context)
            setupRecognitionListener()
        } else {
            _error.value = "Speech recognition not available on this device"
        }
    }

    private fun setupRecognitionListener() {
        speechRecognizer?.setRecognitionListener(object : RecognitionListener {
            
            override fun onReadyForSpeech(params: Bundle?) {
                _isReady.value = true
                _error.value = null
            }

            override fun onBeginningOfSpeech() {
                _isListening.value = true
                _transcript.value = ""
                _audioLevel.value = 0f
            }

            override fun onRmsChanged(rmsdB: Float) {
                // rmsdB ranges from 0 to ~90, normalize to 0-1
                _audioLevel.value = (rmsdB / 90f).coerceIn(0f, 1f)
            }

            override fun onBufferReceived(buffer: ByteArray?) {
                // Raw audio buffer — can be used for waveform visualization later
            }

            override fun onEndOfSpeech() {
                // User has stopped speaking
            }

            override fun onError(error: Int) {
                _isListening.value = false
                _isReady.value = true
                
                val errorMessage = when (error) {
                    SpeechRecognizer.ERROR_AUDIO -> "Audio recording error"
                    SpeechRecognizer.ERROR_CLIENT -> "Client side error"
                    SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> "Microphone permission denied"
                    SpeechRecognizer.ERROR_NETWORK -> "Network error"
                    SpeechRecognizer.ERROR_NO_MATCH -> "No speech detected. Try again."
                    SpeechRecognizer.ERROR_SERVER -> "Server error"
                    SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "No speech input. Tap the mic and speak clearly."
                    else -> "Recognition error: $error"
                }
                _error.value = errorMessage
            }

            override fun onResults(results: Bundle?) {
                _isListening.value = false
                _isReady.value = true
                _audioLevel.value = 0f
                
                val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                val bestMatch = matches?.firstOrNull() ?: ""
                
                if (bestMatch.isNotEmpty()) {
                    _transcript.value = bestMatch
                    _error.value = null
                } else {
                    _error.value = "No speech detected. Please try again."
                }
            }

            override fun onPartialResults(partialResults: Bundle?) {
                // Show live partial transcript as user speaks
                val partial = partialResults
                    ?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                    ?.firstOrNull() ?: ""
                
                if (partial.isNotEmpty()) {
                    _transcript.value = partial
                }
            }

            override fun onEvent(eventType: Int, params: Bundle?) {
                // Reserved for future use
            }
        })
    }

    fun startListening(language: Language = Language.ENGLISH) {
        if (!_isReady.value) return
        
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
            )
            
            // Enable partial results for live transcript display
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            
            // Set language based on user selection
            putExtra(
                RecognizerIntent.EXTRA_LANGUAGE,
                when (language) {
                    Language.ENGLISH -> "en-AU" // Australian English
                    Language.KRIOL -> "en-AU"   // Kriol uses English recognizer (no separate Kriol model)
                }
            )
            
            // Optimize for speech input (less likely to recognize background noise as speech)
            putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_COMPLETE_SILENCE_LENGTH_MILLIS, 5000)
        }
        
        _isReady.value = false
        speechRecognizer?.startListening(intent)
    }

    fun stopListening() {
        speechRecognizer?.stopListening()
    }

    fun cancel() {
        speechRecognizer?.cancel()
        _isListening.value = false
        _transcript.value = ""
        _audioLevel.value = 0f
    }

    fun clearTranscript() {
        _transcript.value = ""
        _error.value = null
    }

    fun clearError() {
        _error.value = null
    }

    fun release() {
        speechRecognizer?.destroy()
        speechRecognizer = null
    }
}
