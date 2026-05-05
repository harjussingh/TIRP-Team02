package com.example.saca.ui.screens

import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import com.example.saca.model.InputMode
import com.example.saca.viewmodel.TriageViewModel

@Composable
fun SymptomInputScreen(
    viewModel: TriageViewModel,
    onNext: () -> Unit,
    onBack: () -> Unit
) {
    val inputMode by viewModel.inputMode.collectAsState()

    // Route to correct modality based on what user chose on Screen 02
    when (inputMode) {
        InputMode.PICTURES -> PictogramInputScreen(viewModel, onNext, onBack)
        InputMode.SPEAK -> SpeechInputScreen(viewModel, onNext, onBack)
        InputMode.TYPE -> TextInputScreen(viewModel, onNext, onBack)
        null -> PictogramInputScreen(viewModel, onNext, onBack) // safe default
    }
}