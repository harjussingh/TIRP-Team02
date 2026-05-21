package com.example.saca.navigation

import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import com.example.saca.ui.screens.InputModeSelectScreen
import com.example.saca.ui.screens.LanguageSelectScreen
import com.example.saca.ui.screens.SymptomInputScreen
import com.example.saca.ui.screens.ResultScreen
import com.example.saca.viewmodel.TriageViewModel

@Composable
fun AppNavGraph(navController: NavHostController, viewModel: TriageViewModel, onEmergencyCall: () -> Unit) {

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
            DisposableEffect(Unit) {
                onDispose { viewModel.narrationManager.stop() }
            }
            InputModeSelectScreen(viewModel = viewModel, onModeSelected = {
                navController.navigate(Screen.SymptomInput.route)
            }, onBack = { navController.popBackStack() })
        }
        composable(Screen.SymptomInput.route) {
            DisposableEffect(Unit) {
                onDispose { viewModel.narrationManager.stop() }
            }
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
                viewModel              = viewModel,
                onBack                 = {
                    viewModel.resetSession()
                    navController.popBackStack()
                                         },
                onStartOver            = {
                    viewModel.resetSession()
                    navController.navigate(Screen.LanguageSelect.route) {
                        popUpTo(Screen.LanguageSelect.route) { inclusive = true }
                    }
                },
                onEmergencyCallConfirmed = onEmergencyCall
            )
        }
    }
}