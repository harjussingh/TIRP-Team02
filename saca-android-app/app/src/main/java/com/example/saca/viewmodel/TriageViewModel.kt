package com.example.saca.viewmodel

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import com.example.saca.ml.TFLiteInferenceEngine
import com.example.saca.model.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

// AndroidViewModel gives us Application context for TFLite asset loading
class TriageViewModel(application: Application) : AndroidViewModel(application) {

    private val inferenceEngine = TFLiteInferenceEngine(application)

    init {
        // Load model + vocab once when ViewModel is created
        inferenceEngine.initialise()
    }

    private val _language = MutableStateFlow(Language.ENGLISH)
    val language: StateFlow<Language> = _language.asStateFlow()

    private val _inputMode = MutableStateFlow<InputMode?>(null)
    val inputMode: StateFlow<InputMode?> = _inputMode.asStateFlow()

    // Pictogram mode — tracks which symptoms are selected
    private val _selectedSymptoms = MutableStateFlow<Set<Symptom>>(emptySet())
    val selectedSymptoms: StateFlow<Set<Symptom>> = _selectedSymptoms.asStateFlow()

    // Speech mode — transcript from SpeechRecognizer
    private val _speechTranscript = MutableStateFlow("")
    val speechTranscript: StateFlow<String> = _speechTranscript.asStateFlow()

    // Text mode — typed input
    private val _typedInput = MutableStateFlow("")
    val typedInput: StateFlow<String> = _typedInput.asStateFlow()

    // Inference result — null until model has run
    private val _inferenceResult = MutableStateFlow<ModelInferenceResult?>(null)
    val inferenceResult: StateFlow<ModelInferenceResult?> = _inferenceResult.asStateFlow()

    fun setLanguage(lang: Language) { _language.value = lang }
    fun setInputMode(mode: InputMode) { _inputMode.value = mode }
    fun setSpeechTranscript(text: String) { _speechTranscript.value = text }
    fun setTypedInput(text: String) { _typedInput.value = text }
    fun switchToSpeech() { _inputMode.value = InputMode.SPEAK }

    fun toggleSymptom(symptom: Symptom) {
        _selectedSymptoms.value = _selectedSymptoms.value.toMutableSet().apply {
            if (contains(symptom)) remove(symptom) else add(symptom)
        }
    }

    // Called when user taps Next on any input screen
    // Runs inference and stores result for the result screen
    fun runInference() {
        val symptoms: List<String> = when (_inputMode.value) {
            InputMode.TYPE     -> _typedInput.value
                .split(" ", ",", ".", "\n")
                .map { it.trim().lowercase() }
                .filter { it.isNotEmpty() }
            InputMode.SPEAK    -> _speechTranscript.value
                .split(" ", ",", ".", "\n")
                .map { it.trim().lowercase() }
                .filter { it.isNotEmpty() }
            InputMode.PICTURES -> _selectedSymptoms.value
                .map { it.labelEN.lowercase() }
            null -> return
        }

    val result = inferenceEngine.runInference(symptoms)

    // ── DEBUG: override severity here to test result screens ──────────────
    // Change to: Severity.LOW / Severity.MEDIUM / Severity.HIGH / Severity.CRITICAL
    // Set to null to use real ML output
    val debugSeverity: Severity? = Severity.CRITICAL
    // ─────────────────────────────────────────────────────────────────────

    _inferenceResult.value = if (debugSeverity != null) {
        result.copy(severity = debugSeverity)
    } else {
        result
    }
}

    // Clears all triage session state — called when starting over or leaving result screen
    fun resetSession() {
        _inferenceResult.value    = null
        _selectedSymptoms.value   = emptySet()
        _speechTranscript.value   = ""
        _typedInput.value         = ""
        _inputMode.value          = null
    }

    override fun onCleared() {
        super.onCleared()
        inferenceEngine.close()
    }
}