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
import com.example.saca.ui.theme.TextSecondary
import com.example.saca.viewmodel.TriageViewModel

@Composable
fun SpeechInputScreen(
    viewModel: TriageViewModel,
    onNext: () -> Unit,
    onBack: () -> Unit
) {
    val context = LocalContext.current
    val language by viewModel.language.collectAsState()
    val transcript by viewModel.speechTranscript.collectAsState()

    var isListening by remember { mutableStateOf(false) }
    var hasPermission by remember { mutableStateOf(false) }

    // Bilingual copy
    val headline = if (language == Language.ENGLISH) "What's wrong?" else "Wanem ron?"
    val subtitle = if (language == Language.ENGLISH) "Tap and speak" else "Tajim en tok"
    val tapMicLabel = if (language == Language.ENGLISH) "Tap the mic" else "Tajim mik"
    val placeholder =
        if (language == Language.ENGLISH) "Your words will show here..." else "Yu wods baimbai shomap yia..."
    val nextLabel = if (language == Language.ENGLISH) "Next" else "Nekst"

    // Microphone permission launcher
    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted -> hasPermission = granted }

    // SpeechRecognizer — Android built-in, works offline on most devices
    val speechRecognizer = remember { SpeechRecognizer.createSpeechRecognizer(context) }

    val recognitionListener = remember {
        object : RecognitionListener {
            override fun onResults(results: Bundle?) {
                val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                val text = matches?.firstOrNull() ?: ""
                viewModel.setSpeechTranscript(text)
                isListening = false
            }

            override fun onError(error: Int) {
                isListening = false
            }

            override fun onReadyForSpeech(params: Bundle?) {}
            override fun onBeginningOfSpeech() {}
            override fun onRmsChanged(rmsdB: Float) {}
            override fun onBufferReceived(buffer: ByteArray?) {}
            override fun onEndOfSpeech() {}
            override fun onPartialResults(partialResults: Bundle?) {
                // Show live partial transcript as user speaks
                val partial = partialResults
                    ?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                    ?.firstOrNull() ?: ""
                if (partial.isNotEmpty()) viewModel.setSpeechTranscript(partial)
            }

            override fun onEvent(eventType: Int, params: Bundle?) {}
        }
    }

    DisposableEffect(Unit) {
        speechRecognizer.setRecognitionListener(recognitionListener)
        onDispose { speechRecognizer.destroy() }
    }

    fun startListening() {
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
            )
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            // Language follows user's toggle — English or Kriol (en-AU closest match)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, "en-AU")
        }
        speechRecognizer.startListening(intent)
        isListening = true
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

                // Large pulsing mic button — 120dp (exceeds 72dp design spec)
                Surface(
                    onClick = {
                        if (!hasPermission) {
                            permissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
                        } else {
                            if (isListening) {
                                speechRecognizer.stopListening()
                                isListening = false
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

                Spacer(modifier = Modifier.height(20.dp))

                Text(
                    text = tapMicLabel,
                    style = MaterialTheme.typography.bodyLarge,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFF1A1A1A)
                )

                Spacer(modifier = Modifier.height(28.dp))

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

            // Next — disabled until transcript has content
            Box(modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)) {
                Button(
                    onClick = onNext,
                    enabled = transcript.isNotBlank(),
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