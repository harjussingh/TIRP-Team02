package com.example.saca.ui.screens

import androidx.compose.animation.core.*
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.saca.model.FollowUpQuestion
import com.example.saca.model.Language
import com.example.saca.ui.components.SacaTopBar
import com.example.saca.ui.theme.*
import com.example.saca.viewmodel.TriageViewModel

@Composable
fun FollowUpScreen(
    viewModel   : TriageViewModel,
    questions   : List<FollowUpQuestion>,
    currentIndex: Int,
    isOffline   : Boolean = false,
    onAnswer    : (questionId: String, answer: String) -> Unit,
    onBack      : () -> Unit
) {
    val language by viewModel.language.collectAsState()
    val question  = questions.getOrNull(currentIndex) ?: return
    val total     = questions.size
    val progress  = (currentIndex + 1).toFloat() / total.toFloat()

    val questionText = if (language == Language.KRIOL) question.textKR else question.textEN

    // Progress bar animation
    val animatedProgress by animateFloatAsState(
        targetValue   = progress,
        animationSpec = tween(400),
        label         = "followup_progress"
    )

    // Step label
    val stepEN = "Step ${currentIndex + 1} of $total"
    val stepKR = "Step ${currentIndex + 1} langa $total"
    val stepLabel = if (language == Language.KRIOL) stepKR else stepEN

    Scaffold(
        topBar = {
            Column {
                SacaTopBar(
                    currentLanguage  = language,          // ← was 'language ='
                    onLanguageToggle = { viewModel.setLanguage(it) },
                    onBack           = onBack
                )
                // Step label shown below the top bar
                Text(
                    text     = stepLabel,
                    style    = MaterialTheme.typography.labelMedium,
                    color    = TextSecondary,
                    modifier = Modifier.padding(start = 16.dp, bottom = 4.dp)
                )
            }
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .background(WarmClay)
        ) {
            // Progress bar
            LinearProgressIndicator(
                progress      = { animatedProgress },
                modifier      = Modifier
                    .fillMaxWidth()
                    .height(4.dp),
                color         = OchreAccent,
                trackColor    = Color(0xFFE0DBD5)
            )

            // Offline banner
            if (isOffline) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(Color(0xFFFFF3CD))
                        .padding(horizontal = 16.dp, vertical = 8.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Text("⚡", fontSize = 14.sp)
                    Text(
                        text  = if (language == Language.KRIOL)
                            "No intenet — waking offlain"
                        else
                            "No internet — working offline",
                        style = MaterialTheme.typography.labelMedium,
                        color = Color(0xFF856404)
                    )
                }
            }

            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(horizontal = 24.dp, vertical = 16.dp),
                verticalArrangement = Arrangement.SpaceBetween
            ) {
                // Question + play button
                Row(
                    modifier          = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.Top
                ) {
                    Text(
                        text       = questionText,
                        style      = MaterialTheme.typography.headlineMedium.copy(
                            fontWeight = FontWeight.Bold,
                            fontSize   = 32.sp,
                            lineHeight = 40.sp
                        ),
                        color      = Color(0xFF1A1A1A),
                        modifier   = Modifier.weight(1f).padding(end = 16.dp)
                    )

                    // Play button
                    Surface(
                        onClick  = {
                            viewModel.narrationManager.narrate(
                                text      = questionText,
                                language  = language,
                                screenKey = "followup_${question.id}"
                            )
                        },
                        shape  = CircleShape,
                        color  = PrimaryBlue,
                        modifier = Modifier.size(56.dp)
                    ) {
                        Box(contentAlignment = Alignment.Center) {
                            Text("▶", color = Color.White, fontSize = 20.sp)
                        }
                    }
                }

                Spacer(modifier = Modifier.height(32.dp))

                // Answer options — large cards matching design
                Column(
                    verticalArrangement = Arrangement.spacedBy(16.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    question.options.forEachIndexed { index, option ->
                        val label = if (language == Language.KRIOL) option.valueKR else option.valueEN
                        val icon  = when (index) {
                            0    -> "👍"
                            1    -> "👎"
                            else -> "•"
                        }

                        Surface(
                            onClick = { onAnswer(question.id, option.valueEN) },
                            shape   = RoundedCornerShape(16.dp),
                            color   = Color.White,
                            border  = BorderStroke(1.dp, Color(0xFFE0DBD5)),
                            modifier = Modifier
                                .fillMaxWidth()
                                .defaultMinSize(minHeight = 80.dp)
                        ) {
                            Row(
                                modifier          = Modifier.padding(horizontal = 20.dp, vertical = 20.dp),
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(16.dp)
                            ) {
                                // Option number circle
                                Surface(
                                    shape = CircleShape,
                                    color = Color(0xFFF5F0EB),
                                    modifier = Modifier.size(36.dp)
                                ) {
                                    Box(contentAlignment = Alignment.Center) {
                                        Text(
                                            text     = icon,
                                            fontSize = 18.sp
                                        )
                                    }
                                }

                                Text(
                                    text       = label,
                                    style      = MaterialTheme.typography.titleLarge.copy(
                                        fontWeight = FontWeight.Bold,
                                        fontSize   = 22.sp
                                    ),
                                    color      = Color(0xFF1A1A1A)
                                )
                            }
                        }
                    }
                }

                Spacer(modifier = Modifier.weight(1f))
            }
        }
    }
}