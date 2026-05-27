package com.example.saca.navigation

// Sealed class - exhaustive, compiler checked routes
sealed class Screen(val route: String) {
    object LanguageSelect : Screen("language_select")
    object InputModeSelect : Screen("input_mode_select")
    object SymptomInput : Screen("symptom_input")
    object FollowUp : Screen("follow_up")
    object Result : Screen("result")
}