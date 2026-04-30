package com.example.saca.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
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

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        verticalArrangement = Arrangement.SpaceBetween
    ) {

        // Top section — logo + headline
        Column {
            Spacer(modifier = Modifier.height(24.dp))

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

            Spacer(modifier = Modifier.height(16.dp))

            // "SACA · TRIAGE" label
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
            )

            Spacer(modifier = Modifier.height(8.dp))

            // Bilingual subtitle
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

            Spacer(modifier = Modifier.height(32.dp))

            // Language option cards
            LanguageCard(
                code = "EN",
                title = "English",
                subtitle = "Speak in English",
                codeColor = PrimaryBlue,
                isSelected = language == Language.ENGLISH,
                onClick = {
                    viewModel.setLanguage(Language.ENGLISH)
                    onLanguageSelected()
                }
            )

            Spacer(modifier = Modifier.height(12.dp))

            LanguageCard(
                code = "KR",
                title = "Kriol",
                subtitle = "Tok langa Kriol",
                codeColor = OchreAccent,
                isSelected = language == Language.KRIOL,
                onClick = {
                    viewModel.setLanguage(Language.KRIOL)
                    onLanguageSelected()
                }
            )
        }

        // Bottom — offline notice
        Row(
            verticalAlignment = Alignment.CenterVertically,
            modifier = Modifier.padding(bottom = 16.dp)
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

@Composable
fun LanguageCard(
    code: String,
    title: String,
    subtitle: String,
    codeColor: Color,
    isSelected: Boolean,
    onClick: () -> Unit
) {
    Surface(
        onClick = onClick,
        shape = RoundedCornerShape(12.dp),
        color = MaterialTheme.colorScheme.surface,
        modifier = Modifier
            .fillMaxWidth()
            .heightIn(min = 72.dp)   // accessibility floor from design tokens
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Code badge — EN / KR
            Text(
                text = code,
                style = MaterialTheme.typography.headlineSmall,
                color = codeColor,
                modifier = Modifier.width(48.dp)
            )
            Spacer(modifier = Modifier.width(12.dp))
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