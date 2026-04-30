package com.example.saca.viewmodel

import androidx.lifecycle.ViewModel
import com.example.saca.model.InputMode
import com.example.saca.model.Language
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

class TriageViewModel : ViewModel() {

    // StateFlow — Compose observes this and recomposes when value changes
    private val _language = MutableStateFlow(Language.ENGLISH)
    val language: StateFlow<Language> = _language.asStateFlow()

    private val _inputMode = MutableStateFlow<InputMode?>(null)
    val inputMode: StateFlow<InputMode?> = _inputMode.asStateFlow()

    fun setLanguage(lang: Language) {
        _language.value = lang
    }

    fun setInputMode(mode: InputMode) {
        _inputMode.value = mode
    }
}