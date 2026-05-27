package com.example.saca.navigation

import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import com.example.saca.ui.screens.*
import com.example.saca.viewmodel.TriageViewModel

@Composable
fun AppNavGraph(
    navController  : NavHostController,
    viewModel      : TriageViewModel,
    onEmergencyCall: () -> Unit
) {
    val language        by viewModel.language.collectAsState()
    val loadingProgress by viewModel.loadingProgress.collectAsState()
    val loadingStatus   by viewModel.loadingStatus.collectAsState()
    val usedRemote      by viewModel.usedRemoteNlp.collectAsState()

    NavHost(
        navController    = navController,
        startDestination = Screen.LanguageSelect.route
    ) {
        composable(Screen.LanguageSelect.route) {
            LanguageSelectScreen(
                viewModel          = viewModel,
                onLanguageSelected = {
                    navController.navigate(Screen.InputModeSelect.route)
                }
            )
        }

        composable(Screen.InputModeSelect.route) {
            DisposableEffect(Unit) {
                onDispose { viewModel.narrationManager.stop() }
            }
            InputModeSelectScreen(
                viewModel      = viewModel,
                onModeSelected = { navController.navigate(Screen.SymptomInput.route) },
                onBack         = { navController.popBackStack() }
            )
        }

        composable(Screen.SymptomInput.route) {
            DisposableEffect(Unit) {
                onDispose { viewModel.narrationManager.stop() }
            }
            SymptomInputScreen(
                viewModel = viewModel,
                onNext    = {
                    navController.navigate(Screen.Loading.route)
                    viewModel.runInference { needsFollowUp ->
                        if (needsFollowUp) {
                            navController.navigate(Screen.FollowUp.route) {
                                popUpTo(Screen.Loading.route) { inclusive = true }
                            }
                        } else {
                            navController.navigate(Screen.Result.route) {
                                popUpTo(Screen.Loading.route) { inclusive = true }
                            }
                        }
                    }
                },
                onBack = { navController.popBackStack() }
            )
        }

        composable(Screen.Loading.route) {
            LoadingScreen(
                language   = language,
                usedRemote = usedRemote,
                progress   = loadingProgress,
                statusText = loadingStatus
            )
        }

        composable(Screen.Result.route) {
            ResultScreen(
                viewModel                = viewModel,
                onBack                   = {
                    viewModel.resetSession()
                    navController.popBackStack()
                },
                onStartOver              = {
                    viewModel.resetSession()
                    navController.navigate(Screen.LanguageSelect.route) {
                        popUpTo(Screen.LanguageSelect.route) { inclusive = true }
                    }
                },
                onEmergencyCallConfirmed = onEmergencyCall
            )
        }
        composable(Screen.FollowUp.route) {
            val questions   by viewModel.followUpQuestions.collectAsState()
            val currentIdx  by viewModel.followUpIndex.collectAsState()

            FollowUpScreen(
                viewModel    = viewModel,
                questions    = questions,
                currentIndex = currentIdx,
                isOffline    = !usedRemote,
                onAnswer     = { questionId, answer ->
                    val done = viewModel.answerFollowUp(questionId, answer)
                    if (done) {
                        viewModel.runFinalInference()
                        navController.navigate(Screen.Result.route) {
                            popUpTo(Screen.FollowUp.route) { inclusive = true }
                        }
                    }
                },
                onBack = { navController.popBackStack() }
            )
        }
    }
}