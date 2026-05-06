package com.example.saca.navigation

import androidx.compose.runtime.Composable
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import com.example.saca.ui.screens.InputModeSelectScreen
import com.example.saca.ui.screens.LanguageSelectScreen
import com.example.saca.ui.screens.SymptomInputScreen
import com.example.saca.ui.screens.ResultScreen
import com.example.saca.viewmodel.TriageViewModel

@Composable
fun AppNavGraph(navController: NavHostController) {

    // Single shared ViewModel across all screens
    val viewModel: TriageViewModel = viewModel()

    NavHost(
        navController = navController, startDestination = Screen.LanguageSelect.route
    ) {
        composable(Screen.LanguageSelect.route) {
            LanguageSelectScreen(
                viewModel = viewModel, onLanguageSelected = {
                    navController.navigate(Screen.InputModeSelect.route)
                })
        }
        composable(Screen.InputModeSelect.route) {
            InputModeSelectScreen(viewModel = viewModel, onModeSelected = {
                navController.navigate(Screen.SymptomInput.route)
            }, onBack = { navController.popBackStack() })
        }
        composable(Screen.SymptomInput.route) {
            SymptomInputScreen(
                viewModel = viewModel,
                onNext = {
                    viewModel.runInference()   // ← run the model before navigating
                    navController.navigate(Screen.Result.route)
                },
                onBack = { navController.popBackStack() })
        }
        composable(Screen.Result.route) {
            ResultScreen(
                viewModel = viewModel,
                onBack = { navController.popBackStack() }
            )
        }
    }
}