package com.example.saca.ui.screens

import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
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

    // All UI strings driven by language — this is the bilingual pattern
    // used on every screen going forward
    val headline = if (language == Language.ENGLISH)
        "How do you want to tell us?"
    else
        "Wanem weh yu wande tok?"

    val tapToHearLabel = if (language == Language.ENGLISH)
        "Tap to hear"
    else
        "Tajim fo irrim"

    Column(modifier = Modifier.fillMaxSize()) {

        SacaTopBar(
            currentLanguage = language,
            onLanguageToggle = { viewModel.setLanguage(it) },
            onBack = onBack
        )

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {

            Text(
                text = headline,
                style = MaterialTheme.typography.headlineMedium,
            )

            // Read-aloud pill button
            OutlinedButton(
                onClick = { /* TTS wired in later phase */ },
                shape = RoundedCornerShape(50),
                contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp)
            ) {
                Text("▶ $tapToHearLabel")
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Three input mode cards
            InputModeCard(
                mode = InputMode.SPEAK,
                language = language,
                isSelected = selectedMode == InputMode.SPEAK,
                onClick = {
                    viewModel.setInputMode(InputMode.SPEAK)
                    onModeSelected()
                }
            )
            InputModeCard(
                mode = InputMode.PICTURES,
                language = language,
                isSelected = selectedMode == InputMode.PICTURES,
                onClick = {
                    viewModel.setInputMode(InputMode.PICTURES)
                    onModeSelected()
                }
            )
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

@Composable
fun InputModeCard(
    mode: InputMode,
    language: Language,
    isSelected: Boolean,
    onClick: () -> Unit
) {
    // Each mode has EN + Kriol copy and an icon symbol
    val (icon, titleEN, subtitleEN, titleKR, subtitleKR) = when (mode) {
        InputMode.SPEAK -> ModeContent("🎤", "Speak", "Talk to the app", "Tok", "Tok langa eb")
        InputMode.PICTURES -> ModeContent("⊞", "Pictures", "Tap a picture", "Piksa", "Tajim piksa")
        InputMode.TYPE -> ModeContent("⌨", "Type", "Use the keyboard", "Raitimbat", "Yusim kiibod")
    }

    val title = if (language == Language.ENGLISH) titleEN else titleKR
    val subtitle = if (language == Language.ENGLISH) subtitleEN else subtitleKR

    Surface(
        onClick = onClick,
        shape = RoundedCornerShape(12.dp),
        color = MaterialTheme.colorScheme.surface,
        modifier = Modifier
            .fillMaxWidth()
            .heightIn(min = 72.dp)
            .then(
                // Blue border when selected — matches design
                if (isSelected) Modifier.border(2.dp, PrimaryBlue, RoundedCornerShape(12.dp))
                else Modifier
            )
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Icon in sand-coloured box
            Surface(
                shape = RoundedCornerShape(8.dp),
                color = Color(0xFFEDE8E2),
                modifier = Modifier.size(48.dp)
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Text(text = icon, style = MaterialTheme.typography.headlineSmall)
                }
            }

            Spacer(modifier = Modifier.width(16.dp))

            Column {
                Text(
                    text = title,
                    style = MaterialTheme.typography.bodyLarge,
                    fontWeight = FontWeight.Bold
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

// Simple data holder to keep the when() block readable
data class ModeContent(
    val icon: String,
    val titleEN: String,
    val subtitleEN: String,
    val titleKR: String,
    val subtitleKR: String
)