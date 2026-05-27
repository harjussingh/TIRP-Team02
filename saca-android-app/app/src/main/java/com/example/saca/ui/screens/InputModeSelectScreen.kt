package com.example.saca.ui.screens

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.saca.R
import com.example.saca.model.InputMode
import com.example.saca.model.Language
import com.example.saca.ui.components.SacaTopBar
import com.example.saca.ui.theme.PrimaryBlue
import com.example.saca.ui.theme.TextSecondary
import com.example.saca.viewmodel.TriageViewModel

@Composable
fun InputModeSelectScreen(
    viewModel: TriageViewModel,
    onModeSelected: () -> Unit,
    onBack: () -> Unit
) {
    val language by viewModel.language.collectAsState()
    val selectedMode by viewModel.inputMode.collectAsState()

    // Bilingual strings — all copy driven by language state
    val headline = when (language) {
        Language.ENGLISH -> "How do you want to tell us?"
        Language.KRIOL   -> "Wanem weh yu wande tok?"
    }
    val tapToHear = when (language) {
        Language.ENGLISH -> "Tap to hear"
        Language.KRIOL   -> "Tajim fo irrim"
    }

    Box(modifier = Modifier.fillMaxSize()) {

        // --- Background PNG (same asset, lighter overlay) ---
        Image(
            painter = painterResource(id = R.drawable.saca_background),
            contentDescription = null,
            modifier = Modifier.fillMaxSize(),
            contentScale = ContentScale.Crop
        )

        // Slightly stronger overlay on this screen — cards need contrast
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color(0xE6F5F0EB))  // WarmClay ~90% opacity
        )

        // --- Screen content ---
        Column(modifier = Modifier.fillMaxSize()) {

            // ── Persistent top bar ────────────────────────────
            SacaTopBar(
                currentLanguage = language,
                onLanguageToggle = { viewModel.setLanguage(it) },
                onBack = onBack
            )

            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(horizontal = 28.dp),
                verticalArrangement = Arrangement.spacedBy(0.dp)
            ) {

                Spacer(modifier = Modifier.height(8.dp))

                // ── Headline ─────────────────────────────────
                Text(
                    text = headline,
                    style = MaterialTheme.typography.headlineMedium,
                    color = Color(0xFF1A1A1A)
                )

                Spacer(modifier = Modifier.height(16.dp))

                // ── Read-aloud pill ───────────────────────────
                OutlinedButton(
                    onClick = { /* TTS — wired in later phase */ },
                    shape = RoundedCornerShape(50),
                    contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp),
                    colors = ButtonDefaults.outlinedButtonColors(
                        contentColor = Color(0xFF1A1A1A)
                    )
                ) {
                    Text(
                        text = "▶  $tapToHear",
                        style = MaterialTheme.typography.labelLarge
                    )
                }

                Spacer(modifier = Modifier.height(28.dp))

                // ── Three input mode cards ────────────────────
                InputModeCard(
                    mode = InputMode.SPEAK,
                    language = language,
                    isSelected = selectedMode == InputMode.SPEAK,
                    onClick = {
                        viewModel.setInputMode(InputMode.SPEAK)
                        onModeSelected()
                    }
                )

                Spacer(modifier = Modifier.height(14.dp))

                InputModeCard(
                    mode = InputMode.PICTURES,
                    language = language,
                    isSelected = selectedMode == InputMode.PICTURES,
                    onClick = {
                        viewModel.setInputMode(InputMode.PICTURES)
                        onModeSelected()
                    }
                )

                Spacer(modifier = Modifier.height(14.dp))

                InputModeCard(
                    mode = InputMode.TYPE,
                    language = language,
                    isSelected = selectedMode == InputMode.TYPE,
                    onClick = {
                        viewModel.setInputMode(InputMode.TYPE)
                        onModeSelected()
                    }
                )
            }
        }
    }
}

// ── Input mode card ───────────────────────────────────────────────────────────
@Composable
fun InputModeCard(
    mode: InputMode,
    language: Language,
    isSelected: Boolean,
    onClick: () -> Unit
) {
    // All copy and icons defined here — single source of truth per mode
    data class ModeStrings(
        val icon: String,
        val titleEN: String, val subtitleEN: String,
        val titleKR: String, val subtitleKR: String
    )

    val content = when (mode) {
        InputMode.SPEAK    -> ModeStrings("🎤", "Speak",    "Talk to the app",  "Tok",       "Tok langa eb")
        InputMode.PICTURES -> ModeStrings("⊞",  "Pictures", "Tap a picture",    "Piksa",     "Tajim piksa")
        InputMode.TYPE     -> ModeStrings("⌨",  "Type",     "Use the keyboard", "Raitimbat", "Yusim kiibod")
    }

    val title    = if (language == Language.ENGLISH) content.titleEN    else content.titleKR
    val subtitle = if (language == Language.ENGLISH) content.subtitleEN else content.subtitleKR

    Surface(
        onClick = onClick,
        shape = RoundedCornerShape(14.dp),
        color = Color(0xFFFFF8F0),
        shadowElevation = if (isSelected) 0.dp else 2.dp,
        modifier = Modifier
            .fillMaxWidth()
            .heightIn(min = 80.dp)
            // Blue border on selected card — matches design exactly
            .then(
                if (isSelected)
                    Modifier.border(2.dp, PrimaryBlue, RoundedCornerShape(14.dp))
                else
                    Modifier
            )
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 20.dp, vertical = 16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {

            // Icon container — sand-coloured rounded box
            Surface(
                shape = RoundedCornerShape(10.dp),
                color = Color(0xFFEDE8E2),
                modifier = Modifier.size(52.dp)
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Text(
                        text = content.icon,
                        fontSize = 22.sp
                    )
                }
            }

            Spacer(modifier = Modifier.width(18.dp))

            // Title + subtitle
            Column {
                Text(
                    text = title,
                    style = MaterialTheme.typography.bodyLarge,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFF1A1A1A)
                )
                Text(
                    text = subtitle,
                    style = MaterialTheme.typography.bodyLarge,
                    color = TextSecondary
                )
            }
        }
    }
}