package com.example.saca.ui.screens

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.shape.CircleShape
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
import com.example.saca.model.ALL_SYMPTOMS
import com.example.saca.model.Language
import com.example.saca.model.Symptom
import com.example.saca.ui.components.SacaTopBar
import com.example.saca.ui.theme.PrimaryBlue
import com.example.saca.ui.theme.TextSecondary
import com.example.saca.viewmodel.TriageViewModel

@Composable
fun PictogramInputScreen(
    viewModel: TriageViewModel,
    onNext: () -> Unit,
    onBack: () -> Unit
) {
    val language by viewModel.language.collectAsState()
    val selectedSymptoms by viewModel.selectedSymptoms.collectAsState()

    val headline = if (language == Language.ENGLISH) "What's wrong?" else "Wanem ron?"
    val subtitle =
        if (language == Language.ENGLISH) "Tap one or more pictures" else "Tajim wan o mo piksa"
    val nextLabel = if (language == Language.ENGLISH) "Next" else "Nekst"

    Box(modifier = Modifier.fillMaxSize()) {

        // Background
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

            // Top bar
            SacaTopBar(
                currentLanguage = language,
                onLanguageToggle = { viewModel.setLanguage(it) },
                onBack = onBack
            )

            // Read-aloud play button — top right of headline row
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 24.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Top
            ) {
                Column {
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

                // Play button circle
                Surface(
                    onClick = { /* TTS — later phase */ },
                    shape = CircleShape,
                    color = Color(0xFFE8E4DF),
                    modifier = Modifier.size(44.dp)
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Text("▶", fontSize = 16.sp, color = Color(0xFF1A1A1A))
                    }
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Symptom grid — scrollable, 2 columns
            LazyVerticalGrid(
                columns = GridCells.Fixed(2),
                modifier = Modifier
                    .weight(1f)
                    .padding(horizontal = 16.dp),
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
                contentPadding = PaddingValues(bottom = 12.dp)
            ) {
                items(ALL_SYMPTOMS) { symptom ->
                    SymptomCard(
                        symptom = symptom,
                        language = language,
                        isSelected = selectedSymptoms.contains(symptom),
                        onClick = { viewModel.toggleSymptom(symptom) }
                    )
                }
            }

            // Sticky Next button — disabled until at least 1 symptom selected
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp)
            ) {
                Button(
                    onClick = onNext,
                    enabled = selectedSymptoms.isNotEmpty(),
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
                        // Shows count: "→ Next · 2"
                        text = if (selectedSymptoms.isEmpty())
                            "→  $nextLabel"
                        else
                            "→  $nextLabel · ${selectedSymptoms.size}",
                        style = MaterialTheme.typography.bodyLarge,
                        fontWeight = FontWeight.Bold,
                        color = Color.White
                    )
                }
            }
        }
    }
}

// Individual symptom card
@Composable
fun SymptomCard(
    symptom: Symptom,
    language: Language,
    isSelected: Boolean,
    onClick: () -> Unit
) {
    val label = if (language == Language.ENGLISH) symptom.labelEN else symptom.labelKR

    Surface(
        onClick = onClick,
        shape = RoundedCornerShape(14.dp),
        color = Color(0xFFFFF8F0),
        shadowElevation = if (isSelected) 0.dp else 2.dp,
        modifier = Modifier
            .fillMaxWidth()
            .aspectRatio(1f)                     // square card
            .then(
                if (isSelected)
                    Modifier.border(2.dp, PrimaryBlue, RoundedCornerShape(14.dp))
                else Modifier
            )
    ) {
        Box(modifier = Modifier.fillMaxSize()) {

            // Icon + label centred
            Column(
                modifier = Modifier.align(Alignment.Center),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text(symptom.icon, fontSize = 36.sp)
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = label,
                    style = MaterialTheme.typography.bodyLarge,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFF1A1A1A)
                )
            }

            // Blue checkmark badge — top right when selected
            if (isSelected) {
                Surface(
                    shape = CircleShape,
                    color = PrimaryBlue,
                    modifier = Modifier
                        .align(Alignment.TopEnd)
                        .padding(10.dp)
                        .size(26.dp)
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Text(
                            "✓",
                            color = Color.White,
                            fontSize = 14.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }
        }
    }
}