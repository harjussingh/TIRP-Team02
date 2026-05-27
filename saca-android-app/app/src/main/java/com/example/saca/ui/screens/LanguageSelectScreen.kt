package com.example.saca.ui.screens

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.saca.R
import com.example.saca.model.Language
import com.example.saca.ui.theme.OchreAccent
import com.example.saca.ui.theme.PrimaryBlue
import com.example.saca.ui.theme.TextSecondary
import com.example.saca.viewmodel.TriageViewModel

@Composable
fun LanguageSelectScreen(
    viewModel: TriageViewModel,
    onLanguageSelected: () -> Unit
) {
    val language by viewModel.language.collectAsState()

    Box(modifier = Modifier.fillMaxSize()) {

        // --- Background PNG ---
        Image(
            painter = painterResource(id = R.drawable.saca_background),
            contentDescription = null,
            modifier = Modifier.fillMaxSize(),
            contentScale = ContentScale.Crop
        )

        // --- Semi-transparent overlay so text stays readable over the pattern ---
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color(0xCCF5F0EB))  // WarmClay at ~80% opacity
        )

        // --- Screen content ---
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 28.dp),
            verticalArrangement = Arrangement.SpaceBetween
        ) {

            // ── Top section ──────────────────────────────────
            Column {
                Spacer(modifier = Modifier.height(52.dp))

                // S logo — black rounded square
                Surface(
                    shape = RoundedCornerShape(16.dp),
                    color = Color.Black,
                    modifier = Modifier.size(64.dp)
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Text(
                            text = "S",
                            color = Color.White,
                            fontSize = 32.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }

                Spacer(modifier = Modifier.height(20.dp))

                // "SACA · TRIAGE" eyebrow label
                Text(
                    text = "SACA · TRIAGE",
                    style = MaterialTheme.typography.labelMedium,
                    color = OchreAccent,
                    letterSpacing = 2.sp
                )

                Spacer(modifier = Modifier.height(8.dp))

                // Welkom headline
                Text(
                    text = "Welkom",
                    style = MaterialTheme.typography.headlineLarge,
                    color = Color(0xFF1A1A1A)
                )

                Spacer(modifier = Modifier.height(8.dp))

                // Bilingual subtitle — English first, Kriol below
                Text(
                    text = "Choose your language",
                    style = MaterialTheme.typography.bodyLarge,
                    color = TextSecondary
                )
                Text(
                    text = "Jus yu langgus",
                    style = MaterialTheme.typography.bodyLarge,
                    color = TextSecondary
                )

                Spacer(modifier = Modifier.height(40.dp))

                // ── Language cards ───────────────────────────
                LanguageCard(
                    code = "EN",
                    title = "English",
                    subtitle = "Speak in English",
                    codeColor = PrimaryBlue,
                    onClick = {
                        viewModel.setLanguage(Language.ENGLISH)
                        onLanguageSelected()
                    }
                )

                Spacer(modifier = Modifier.height(16.dp))

                LanguageCard(
                    code = "KR",
                    title = "Kriol",
                    subtitle = "Tok langa Kriol",
                    codeColor = OchreAccent,
                    onClick = {
                        viewModel.setLanguage(Language.KRIOL)
                        onLanguageSelected()
                    }
                )
            }

            // ── Bottom — offline + privacy notice ────────────
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier
                    .padding(bottom = 32.dp)
                    .fillMaxWidth()
            ) {
                Icon(
                    painter = painterResource(id = android.R.drawable.ic_dialog_info),
                    contentDescription = null,
                    tint = TextSecondary,
                    modifier = Modifier.size(16.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = "Works offline · Your info stays private",
                    style = MaterialTheme.typography.labelMedium,
                    color = TextSecondary
                )
            }
        }
    }
}

// ── Language card ─────────────────────────────────────────────────────────────
@Composable
fun LanguageCard(
    code: String,
    title: String,
    subtitle: String,
    codeColor: Color,
    onClick: () -> Unit
) {
    Surface(
        onClick = onClick,
        shape = RoundedCornerShape(14.dp),
        color = Color(0xFFFFF8F0),          // LightSand — slightly warmer than white
        shadowElevation = 2.dp,
        modifier = Modifier
            .fillMaxWidth()
            .heightIn(min = 80.dp)          // 80dp > 48dp accessibility floor
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 20.dp, vertical = 16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Code badge — EN / KR
            Text(
                text = code,
                style = MaterialTheme.typography.headlineSmall,
                color = codeColor,
                fontWeight = FontWeight.Bold,
                modifier = Modifier.width(52.dp)
            )

            Spacer(modifier = Modifier.width(12.dp))

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