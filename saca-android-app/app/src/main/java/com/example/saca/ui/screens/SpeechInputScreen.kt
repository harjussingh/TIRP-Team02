package com.example.saca.ui.screens

import android.Manifest
import android.content.Intent
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.core.*
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.saca.R
import com.example.saca.model.Language
import com.example.saca.ui.components.SacaTopBar
import com.example.saca.ui.theme.PrimaryBlue
import com.example.saca.ui.theme.SeverityHigh
import com.example.saca.ui.theme.TextSecondary
import com.example.saca.util.SpeechRecognitionManager
import com.example.saca.viewmodel.TriageViewModel

@Composable
fun SpeechInputScreen(
    viewModel: TriageViewModel,
    onNext: () -> Unit,
    onBack: () -> Unit
) {
    val context = LocalContext.current
    val language by viewModel.language.collectAsState()
    val typedInput by viewModel.typedInput.collectAsState()

    // Use the new SpeechRecognitionManager for voice capturing
    val speechManager = remember { SpeechRecognitionManager(context) }
    val transcript by speechManager.transcript.collectAsState()
    val isListening by speechManager.isListening.collectAsState()
    val audioLevel by speechManager.audioLevel.collectAsState()
    val error by speechManager.error.collectAsState()
    val isReady by speechManager.isReady.collectAsState()

    var hasPermission by remember { mutableStateOf(false) }

    // Bilingual copy
    val headline = if (language == Language.ENGLISH) "What's wrong?" else "Wanem ron?"
    val subtitle = if (language == Language.ENGLISH) "Tap and speak" else "Tajim en tok"
    val tapMicLabel = if (language == Language.ENGLISH) "Tap the mic" else "Tajim mik"
    val placeholder =
        if (language == Language.ENGLISH) "Your words will show here..." else "Yu wods baimbai shomap yia..."
    val nextLabel = if (language == Language.ENGLISH) "Next" else "Nekst"
    val tryAgainLabel = if (language == Language.ENGLISH) "Try again" else "Traem agen"

    // Narrate screen header when screen loads
    LaunchedEffect(Unit) {
        viewModel.narrationManager.narrate(
            text = headline,
            language = language,
            screenKey = "speech_input"
        )
    }

    // Update ViewModel transcript when speechManager transcript changes
    LaunchedEffect(transcript) {
        if (transcript.isNotEmpty()) {
            viewModel.setSpeechTranscript(transcript)
        }
    }

    fun startListening() {
        speechManager.clearError()
        speechManager.startListening(language)
    }

    fun stopListening() {
        speechManager.stopListening()
    }

    // Microphone permission launcher
    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        hasPermission = granted
        if (granted) {
            startListening()
        }
    }

    // Cleanup speech manager when screen is disposed
    DisposableEffect(Unit) {
        onDispose { speechManager.release() }
    }

    // Pulse animation on mic when listening
    val pulseScale by rememberInfiniteTransition(label = "pulse").animateFloat(
        initialValue = 1f,
        targetValue = 1.12f,
        animationSpec = infiniteRepeatable(
            animation = tween(700, easing = EaseInOut),
            repeatMode = RepeatMode.Reverse
        ),
        label = "micPulse"
    )

    Box(modifier = Modifier.fillMaxSize()) {

        Image(
            painter = painterResource(id = R.drawable.saca_background),
            contentDescription = null,
            modifier = Modifier.fillMaxSize(),
            contentScale = ContentScale.Crop
        )
        Box(modifier = Modifier
            .fillMaxSize()
            .background(Color(0xE6F5F0EB)))

        Column(modifier = Modifier.fillMaxSize()) {

            SacaTopBar(
                currentLanguage = language,
                onLanguageToggle = { viewModel.setLanguage(it) },
                onBack = onBack
            )

            Column(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth()
                    .padding(horizontal = 28.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {

                Spacer(modifier = Modifier.height(8.dp))

                // Headline left-aligned
                Column(modifier = Modifier.fillMaxWidth()) {
                    Text(
                        text = headline,
                        style = MaterialTheme.typography.headlineMedium,
                        color = Color(0xFF1A1A1A)
                    )
                    Text(
                        text = subtitle,
                        style = MaterialTheme.typography.bodyLarge,
                        color = TextSecondary
                    )
                }

                Spacer(modifier = Modifier.height(48.dp))

                // Large pulsing mic button — 120dp with audio level visualization
                Box(
                    modifier = Modifier.size(140.dp),
                    contentAlignment = Alignment.Center
                ) {
                    // Audio level circle (animated background)
                    if (isListening) {
                        Surface(
                            shape = CircleShape,
                            color = SeverityHigh.copy(alpha = audioLevel * 0.3f),
                            modifier = Modifier
                                .size((120 + audioLevel * 20).dp)
                        ) {}
                    }

                    Surface(
                        onClick = {
                            if (isListening) {
                                stopListening()
                            } else {
                                if (!hasPermission) {
                                    permissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
                                } else {
                                    startListening()
                                }
                            }
                        },
                        shape = CircleShape,
                        color = PrimaryBlue,
                        modifier = Modifier
                            .size(120.dp)
                            .scale(if (isListening) pulseScale else 1f)
                    ) {
                        Box(contentAlignment = Alignment.Center) {
                            Text("🎤", fontSize = 40.sp)
                        }
                    }
                }

                Spacer(modifier = Modifier.height(20.dp))

                Text(
                    text = if (isListening) "Listening..." else tapMicLabel,
                    style = MaterialTheme.typography.bodyLarge,
                    fontWeight = FontWeight.Bold,
                    color = if (isListening) SeverityHigh else Color(0xFF1A1A1A)
                )

                Spacer(modifier = Modifier.height(28.dp))

                // Error display (if any)
                if (error != null) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .background(
                                color = SeverityHigh.copy(alpha = 0.15f),
                                shape = RoundedCornerShape(12.dp)
                            )
                            .padding(12.dp)
                    ) {
                        Column {
                            Text(
                                text = "⚠ ${error ?: ""}",
                                style = MaterialTheme.typography.bodyMedium,
                                color = SeverityHigh,
                                fontWeight = FontWeight.Bold
                            )
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                text = tryAgainLabel,
                                style = MaterialTheme.typography.labelMedium,
                                color = SeverityHigh.copy(alpha = 0.7f)
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(16.dp))
                }

                // Live transcript area — dashed border
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(min = 120.dp)
                        .border(
                            width = 1.5.dp,
                            color = Color(0xFFCCC5BB),
                            shape = RoundedCornerShape(14.dp)
                        )
                        .background(Color(0xFFFFF8F0), RoundedCornerShape(14.dp))
                        .padding(16.dp)
                ) {
                    Text(
                        text = transcript.ifEmpty { placeholder },
                        style = MaterialTheme.typography.bodyLarge,
                        color = if (transcript.isEmpty()) TextSecondary else Color(0xFF1A1A1A)
                    )
                }
            }

            // Next — disabled until transcript has content and ready state
            Box(modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)) {
                Button(
                    onClick = {
                        speechManager.stopListening()
                        onNext()
                    },
                    enabled = transcript.isNotBlank() && isReady,
                    shape = RoundedCornerShape(14.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = PrimaryBlue,
                        disabledContainerColor = Color(0xFFD6CFC8)
                    ),
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(60.dp)
                ) {
                    Text(
                        text = "→  $nextLabel",
                        style = MaterialTheme.typography.bodyLarge,
                        fontWeight = FontWeight.Bold,
                        color = Color.White
                    )
                }
            }
        }
    }
}
