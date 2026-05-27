package com.example.saca.ui.screens

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.example.saca.R
import com.example.saca.model.Language
import com.example.saca.ui.components.SacaTopBar
import com.example.saca.ui.theme.PrimaryBlue
import com.example.saca.ui.theme.TextSecondary
import com.example.saca.viewmodel.TriageViewModel

@Composable
fun TextInputScreen(
    viewModel: TriageViewModel,
    onNext: () -> Unit,
    onBack: () -> Unit
) {
    val language by viewModel.language.collectAsState()
    val typedInput by viewModel.typedInput.collectAsState()

    // Bilingual copy
    val headline = if (language == Language.ENGLISH) "What's wrong?" else "Wanem ron?"
    val textHint = if (language == Language.ENGLISH) "Type what is wrong" else "Rait wanem ron"
    val voiceButtonLabel =
        if (language == Language.ENGLISH) "Use voice instead" else "Yus vois instedi"
    val nextLabel = if (language == Language.ENGLISH) "Next" else "Nekst"

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
                    .padding(horizontal = 28.dp)
            ) {

                Spacer(modifier = Modifier.height(8.dp))

                Text(
                    text = headline,
                    style = MaterialTheme.typography.headlineMedium,
                    color = Color(0xFF1A1A1A)
                )
                Text(
                    text = textHint,
                    style = MaterialTheme.typography.bodyLarge,
                    color = TextSecondary
                )

                Spacer(modifier = Modifier.height(24.dp))

                // Large textarea — min 200dp, expands with content
                OutlinedTextField(
                    value = typedInput,
                    onValueChange = { viewModel.setTypedInput(it) },
                    placeholder = {
                        Text(
                            text = textHint,
                            style = MaterialTheme.typography.bodyLarge,
                            color = TextSecondary
                        )
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(min = 200.dp),
                    shape = RoundedCornerShape(14.dp),
                    colors = OutlinedTextFieldDefaults.colors(
                        unfocusedContainerColor = Color(0xFFFFF8F0),
                        focusedContainerColor = Color(0xFFFFF8F0),
                        focusedBorderColor = PrimaryBlue,
                        unfocusedBorderColor = Color(0xFFCCC5BB)
                    ),
                    textStyle = MaterialTheme.typography.bodyLarge.copy(
                        color = Color(0xFF1A1A1A)
                    ),
                    maxLines = 8
                )

                Spacer(modifier = Modifier.height(16.dp))

                // "Use voice instead" — switches input mode back to SPEAK
                OutlinedButton(
                    onClick = { viewModel.switchToSpeech() },
                    shape = RoundedCornerShape(50),
                    colors = ButtonDefaults.outlinedButtonColors(
                        contentColor = Color(0xFF1A1A1A)
                    ),
                    contentPadding = PaddingValues(horizontal = 20.dp, vertical = 10.dp)
                ) {
                    Text("🎤  $voiceButtonLabel", style = MaterialTheme.typography.labelLarge)
                }
            }

            // Next — disabled until something is typed
            Box(modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)) {
                Button(
                    onClick = onNext,
                    enabled = typedInput.isNotBlank(),
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