package com.example.saca.viewmodel

import androidx.lifecycle.ViewModel
import com.example.saca.model.InputMode
import com.example.saca.model.Language
import com.example.saca.model.Symptom
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

class TriageViewModel : ViewModel() {

    // StateFlow — Compose observes this and recomposes when value changes
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

    fun setLanguage(lang: Language) {
        _language.value = lang
    }

    fun setInputMode(mode: InputMode) {
        _inputMode.value = mode
    }

    fun toggleSymptom(symptom: Symptom) {
        _selectedSymptoms.value = _selectedSymptoms.value.toMutableSet().apply {
            if (contains(symptom)) remove(symptom) else add(symptom)
        }
    }

    fun setSpeechTranscript(text: String) {
        _speechTranscript.value = text
    }

    fun setTypedInput(text: String) {
        _typedInput.value = text
    }

    // Switch from text → speech mode mid-screen
    fun switchToSpeech() {
        _inputMode.value = InputMode.SPEAK
    }
}