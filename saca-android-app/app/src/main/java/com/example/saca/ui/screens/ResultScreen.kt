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
import com.example.saca.model.Severity
import com.example.saca.ui.theme.OchreAccent
import com.example.saca.ui.theme.PrimaryBlue
import com.example.saca.ui.theme.TextSecondary
import com.example.saca.viewmodel.TriageViewModel

@Composable
fun ResultScreen(
    viewModel: TriageViewModel,
    onBack: () -> Unit
) {
    val inferenceResult by viewModel.inferenceResult.collectAsState()

    Box(modifier = Modifier.fillMaxSize()) {
        // --- Background PNG ---
        Image(
            painter = painterResource(id = R.drawable.saca_background),
            contentDescription = null,
            modifier = Modifier.fillMaxSize(),
            contentScale = ContentScale.Crop
        )

        // --- Semi-transparent overlay ---
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color(0xCCF5F0EB))
        )

        // --- Screen content ---
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp),
            verticalArrangement = Arrangement.SpaceEvenly,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = "Triage Result",
                fontSize = 28.sp,
                fontWeight = FontWeight.Bold,
                color = PrimaryBlue,
                modifier = Modifier.padding(bottom = 16.dp)
            )

            inferenceResult?.let { result ->
                // Severity box
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 8.dp),
                    shape = RoundedCornerShape(12.dp),
                    colors = CardDefaults.cardColors(containerColor = Color.White)
                ) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Text(
                            text = "Severity",
                            fontSize = 16.sp,
                            fontWeight = FontWeight.SemiBold,
                            color = TextSecondary
                        )
                        Text(
                            text = result.severity.displayName,
                            fontSize = 24.sp,
                            fontWeight = FontWeight.Bold,
                            color = when (result.severity) {
                                Severity.LOW -> Color.Green
                                Severity.MEDIUM -> Color(0xFFFFA500)
                                Severity.HIGH -> Color.Red
                                Severity.CRITICAL -> Color(0xFF990000)
                            },
                            modifier = Modifier.padding(top = 8.dp)
                        )
                    }
                }

                // Confidence
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 8.dp),
                    shape = RoundedCornerShape(12.dp),
                    colors = CardDefaults.cardColors(containerColor = Color.White)
                ) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Text(
                            text = "Confidence",
                            fontSize = 16.sp,
                            fontWeight = FontWeight.SemiBold,
                            color = TextSecondary
                        )
                        Text(
                            text = "%.1f%%".format(result.confidence * 100),
                            fontSize = 24.sp,
                            fontWeight = FontWeight.Bold,
                            color = PrimaryBlue,
                            modifier = Modifier.padding(top = 8.dp)
                        )
                    }
                }

                // Follow-up needed
                if (result.needsFollowUp) {
                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 8.dp),
                        shape = RoundedCornerShape(12.dp),
                        colors = CardDefaults.cardColors(containerColor = Color(0xFFFFE5E5))
                    ) {
                        Column(
                            modifier = Modifier.padding(16.dp),
                            horizontalAlignment = Alignment.CenterHorizontally
                        ) {
                            Text(
                                text = "⚠️ Follow-up Recommended",
                                fontSize = 16.sp,
                                fontWeight = FontWeight.Bold,
                                color = Color.Red
                            )
                            if (result.suggestedSymptoms.isNotEmpty()) {
                                Text(
                                    text = "Check for: ${result.suggestedSymptoms.take(3).joinToString(", ")}",
                                    fontSize = 12.sp,
                                    color = TextSecondary,
                                    modifier = Modifier.padding(top = 8.dp)
                                )
                            }
                        }
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))
            }

            // Action buttons
            Button(
                onClick = onBack,
                modifier = Modifier
                    .fillMaxWidth(0.8f)
                    .height(50.dp),
                colors = ButtonDefaults.buttonColors(containerColor = PrimaryBlue),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text("Back to Input", fontSize = 16.sp, color = Color.White)
            }
        }
    }
}
