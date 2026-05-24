package com.example.saca.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.wrapContentWidth
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Call
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.saca.model.Language
import com.example.saca.model.Severity
import com.example.saca.ui.components.EmergencyCallDialog
import com.example.saca.ui.components.SacaTopBar
import com.example.saca.ui.theme.PrimaryBlue
import com.example.saca.ui.theme.SeverityCritical
import com.example.saca.ui.theme.SeverityHigh
import com.example.saca.ui.theme.SeverityLow
import com.example.saca.ui.theme.SeverityMedium
import com.example.saca.ui.theme.TextSecondary
import com.example.saca.ui.theme.WarmClay
import com.example.saca.viewmodel.TriageViewModel
import android.content.Context
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.platform.LocalContext

@Composable
fun ResultScreen(
    viewModel: TriageViewModel,
    onBack: () -> Unit,
    onStartOver: () -> Unit,
    onEmergencyCallConfirmed: () -> Unit
) {
    val inferenceResult  by viewModel.inferenceResult.collectAsState()
    val language         by viewModel.language.collectAsState()
    val selectedSymptoms by viewModel.selectedSymptoms.collectAsState()
    val speechTranscript by viewModel.speechTranscript.collectAsState()
    val typedInput       by viewModel.typedInput.collectAsState()

    val severity = inferenceResult?.severity ?: Severity.LOW

    // ── Severity meta ─────────────────────────────────────────────────────
    val severityColor = when (severity) {
        Severity.LOW      -> SeverityLow
        Severity.MEDIUM   -> SeverityMedium
        Severity.HIGH     -> SeverityHigh
        Severity.CRITICAL -> SeverityCritical
    }

    val severityBadge = when (severity) {
        Severity.LOW      -> "LOW · LILBIT"
        Severity.MEDIUM   -> "MEDIUM · LILBIT"
        Severity.HIGH     -> "HIGH · HEVI"
        Severity.CRITICAL -> "CRITICAL · BIGWAN HEVI"
    }

    val severityIcon = when (severity) {
        Severity.LOW      -> "✓"
        Severity.MEDIUM   -> "ℹ"
        Severity.HIGH     -> "⚠"
        Severity.CRITICAL -> "⚠"
    }

    val headline = when (severity) {
        Severity.LOW      -> if (language == Language.ENGLISH) "Rest and check again"  else "Rest na jek agen"
        Severity.MEDIUM   -> if (language == Language.ENGLISH) "See health worker"     else "Go luk helt woka"
        Severity.HIGH     -> if (language == Language.ENGLISH) "See clinic today"      else "Go klinik tudei"
        Severity.CRITICAL -> if (language == Language.ENGLISH) "Need help now"         else "Nid help nau"
    }

    val bodyText = when (severity) {
        Severity.LOW      -> if (language == Language.ENGLISH)
            "Rest. Drink water. Check again tomorrow." else "Rest. Drink wata. Jek agen tumora."
        Severity.MEDIUM   -> if (language == Language.ENGLISH)
            "Talk to a health worker today." else "Tok langa helt woka tudei."
        Severity.HIGH     -> if (language == Language.ENGLISH)
            "Go to the clinic today. Do not wait." else "Go langa klinik tudei. No wet."
        Severity.CRITICAL -> if (language == Language.ENGLISH)
            "This is serious." else "Dis wan hevi."
    }

    val primaryCtaLabel = when (severity) {
        Severity.LOW      -> if (language == Language.ENGLISH) "Rest — check again tomorrow" else "Rest — jek agen tumora"
        Severity.MEDIUM   -> if (language == Language.ENGLISH) "See health worker today"     else "Go luk helt woka tudei"
        Severity.HIGH     -> if (language == Language.ENGLISH) "Go to clinic today"          else "Go klinik tudei"
        Severity.CRITICAL -> if (language == Language.ENGLISH) "Call 000 now"                else "Kaal 000 nau"
    }

    val startOverLabel  = if (language == Language.ENGLISH) "Start over"        else "Stat oba"
    val whatYouToldUs   = if (language == Language.ENGLISH) "WHAT YOU TOLD US"  else "WANEM YU TOLEM AS"
    val howSeriousLabel = if (language == Language.ENGLISH) "HOW SERIOUS"       else "AO HEVI"

    // ── Symptom chips ─────────────────────────────────────────────────────
    val symptomChips: List<Pair<String, String>> = when {
        selectedSymptoms.isNotEmpty() -> selectedSymptoms.map {
            it.icon to if (language == Language.ENGLISH) it.labelEN else it.labelKR
        }
        speechTranscript.isNotBlank() -> listOf("🎤" to speechTranscript)
        typedInput.isNotBlank()       -> listOf("⌨" to typedInput)
        else                          -> emptyList()
    }

    val suggestedChips = inferenceResult?.suggestedSymptoms ?: emptyList()

    // Emergency dialog state
    var showEmergencyDialog by remember { mutableStateOf(false) }
    
    // Narrate result headline when screen loads
    LaunchedEffect(severity) {
        viewModel.narrationManager.narrate(
            text = headline,
            language = language,
            screenKey = "result"
        )
    }
    
    if (showEmergencyDialog) {
        EmergencyCallDialog(
            language  = language,
            onConfirm = {
                showEmergencyDialog = false
                onEmergencyCallConfirmed()
            },
            onDismiss = { showEmergencyDialog = false }
        )
    }

    // ── CRITICAL — full screen red takeover ───────────────────────────────
    if (severity == Severity.CRITICAL) {
        CriticalResultScreen(
            language        = language,
            severityBadge   = severityBadge,
            headline        = headline,
            bodyText        = bodyText,
            suggestedChips  = suggestedChips,
            ctaLabel        = primaryCtaLabel,
            startOverLabel  = startOverLabel,
            onBack          = onBack,
            onCallEmergency = { showEmergencyDialog = true },
            onStartOver     = onStartOver,
            viewModel       = viewModel
        )
        return
    }

    // ── LOW / MEDIUM / HIGH ───────────────────────────────────────────────
    // No verticalScroll — we use weight(1f) to push buttons to bottom
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(WarmClay)
    ) {

        // Top bar
        SacaTopBar(
            currentLanguage  = language,
            onLanguageToggle = { viewModel.setLanguage(it) },
            onBack           = onBack
        )

        // ── Severity banner ───────────────────────────────────────────────
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .background(severityColor)
                .padding(horizontal = 24.dp, vertical = 20.dp)
        ) {
            Row(verticalAlignment = Alignment.Top) {
                Surface(
                    shape    = RoundedCornerShape(8.dp),
                    color    = Color.White.copy(alpha = 0.25f),
                    modifier = Modifier.size(48.dp)
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Text(
                            severityIcon,
                            fontSize   = 22.sp,
                            color      = Color.White,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
                Spacer(modifier = Modifier.width(16.dp))
                Column {
                    Text(
                        text          = severityBadge,
                        style         = MaterialTheme.typography.labelMedium,
                        color         = Color.White.copy(alpha = 0.85f),
                        letterSpacing = 1.sp
                    )
                    Text(
                        text     = headline,
                        style    = MaterialTheme.typography.headlineMedium,
                        color    = Color.White,
                        modifier = Modifier.padding(top = 4.dp)
                    )
                }
            }
        }

        // ── Body text ─────────────────────────────────────────────────────
        Text(
            text       = bodyText,
            style      = MaterialTheme.typography.bodyLarge,
            color      = Color(0xFF1A1A1A),
            fontWeight = FontWeight.Bold,
            modifier   = Modifier
                .padding(horizontal = 24.dp)
                .padding(top = 16.dp, bottom = 12.dp)
        )

        // ── What you told us ──────────────────────────────────────────────
        if (symptomChips.isNotEmpty()) {
            Text(
                text          = whatYouToldUs,
                style         = MaterialTheme.typography.labelMedium,
                color         = TextSecondary,
                letterSpacing = 1.sp,
                modifier      = Modifier
                    .padding(horizontal = 24.dp)
                    .padding(bottom = 10.dp)
            )
            Column(
                modifier            = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 24.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                symptomChips.chunked(2).forEach { rowChips ->
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        rowChips.forEach { (icon, label) ->
                            SymptomChip(
                                icon     = icon,
                                label    = label,
                                modifier = Modifier.weight(1f)
                            )
                        }
                        if (rowChips.size == 1) {
                            Spacer(modifier = Modifier.weight(1f))
                        }
                    }
                }
            }
        }

        // ── Push buttons to bottom ────────────────────────────────────────
        Spacer(modifier = Modifier.weight(1f))

        // ── Primary CTA ───────────────────────────────────────────────────
        Button(
            onClick = { /* directional advice — no phone call */ },
            shape   = RoundedCornerShape(14.dp),
            colors  = ButtonDefaults.buttonColors(
                containerColor = if (severity == Severity.HIGH) SeverityHigh else PrimaryBlue
            ),
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 24.dp)
                .height(60.dp)
        ) {
            Text(
                text       = "→  $primaryCtaLabel",
                style      = MaterialTheme.typography.bodyLarge,
                fontWeight = FontWeight.Bold,
                color      = Color.White
            )
        }

        Spacer(modifier = Modifier.height(12.dp))

        // ── Start over ────────────────────────────────────────────────────
        OutlinedButton(
            onClick  = onStartOver,
            shape    = RoundedCornerShape(14.dp),
            colors   = ButtonDefaults.outlinedButtonColors(contentColor = Color(0xFF1A1A1A)),
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 24.dp)
                .height(52.dp)
        ) {
            Text(text = startOverLabel, style = MaterialTheme.typography.bodyLarge)
        }

        Spacer(modifier = Modifier.height(28.dp))

        // ── How serious strip ─────────────────────────────────────────────
        Text(
            text          = howSeriousLabel,
            style         = MaterialTheme.typography.labelMedium,
            color         = TextSecondary,
            letterSpacing = 1.sp,
            modifier      = Modifier
                .padding(horizontal = 24.dp)
                .padding(bottom = 12.dp)
        )
        SeverityStrip(current = severity)

        Spacer(modifier = Modifier.height(32.dp))
    }
}

// ── CRITICAL full-screen composable ──────────────────────────────────────────
@Composable
private fun CriticalResultScreen(
    language        : Language,
    severityBadge   : String,
    headline        : String,
    bodyText        : String,
    suggestedChips  : List<String>,
    ctaLabel        : String,
    startOverLabel  : String,
    onBack          : () -> Unit,
    onCallEmergency : () -> Unit,
    onStartOver     : () -> Unit,
    viewModel       : TriageViewModel
) {
    // Vibrate when critical screen appears — alerts health worker
    val context = LocalContext.current
    LaunchedEffect(Unit) {
        val vibrator = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            val manager = context.getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as VibratorManager
            manager.defaultVibrator
        } else {
            @Suppress("DEPRECATION")
            context.getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            // Three strong pulses — 200ms on, 100ms off, repeat x3
            val pattern = longArrayOf(0, 200, 100, 200, 100, 200)
            vibrator.vibrate(
                VibrationEffect.createWaveform(pattern, -1)
            )
        } else {
            @Suppress("DEPRECATION")
            vibrator.vibrate(longArrayOf(0, 200, 100, 200, 100, 200), -1)
        }
    }
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(SeverityCritical)
    ) {
        Column(
            modifier = Modifier.fillMaxSize()
        ) {

            // Top bar — white on red
            Row(
                modifier          = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 12.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                TextButton(onClick = onBack) {
                    Text(
                        text  = "← Back",
                        style = MaterialTheme.typography.labelLarge,
                        color = Color.White
                    )
                }
                Spacer(modifier = Modifier.weight(1f))
                Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                    listOf(Language.ENGLISH, Language.KRIOL).forEach { lang ->
                        val isSelected = language == lang
                        val label      = if (lang == Language.ENGLISH) "EN" else "Kriol"
                        Surface(
                            onClick  = { viewModel.setLanguage(lang) },
                            shape    = RoundedCornerShape(50),
                            color    = if (isSelected) Color.White else Color.White.copy(alpha = 0.2f),
                            modifier = Modifier.height(32.dp)
                        ) {
                            Box(
                                contentAlignment = Alignment.Center,
                                modifier         = Modifier.padding(horizontal = 12.dp)
                            ) {
                                Text(
                                    text  = label,
                                    style = MaterialTheme.typography.labelMedium,
                                    color = if (isSelected) SeverityCritical else Color.White
                                )
                            }
                        }
                    }
                }
            }

            // Severity badge pill
            Surface(
                shape    = RoundedCornerShape(50),
                color    = Color.White.copy(alpha = 0.2f),
                modifier = Modifier
                    .padding(horizontal = 24.dp)
                    .padding(bottom = 8.dp)
                    .wrapContentWidth()
            ) {
                Row(
                    modifier          = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text("⚠", fontSize = 14.sp, color = Color.White)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text          = severityBadge,
                        style         = MaterialTheme.typography.labelLarge,
                        color         = Color.White,
                        letterSpacing = 1.sp
                    )
                }
            }

            // Big headline
            Text(
                text       = headline,
                fontSize   = 48.sp,
                fontWeight = FontWeight.Bold,
                lineHeight = 56.sp,
                color      = Color.White,
                modifier   = Modifier
                    .padding(horizontal = 24.dp)
                    .padding(bottom = 8.dp)
            )

            // Body text
            Text(
                text       = bodyText,
                style      = MaterialTheme.typography.bodyLarge,
                color      = Color.White,
                fontWeight = FontWeight.Bold,
                modifier   = Modifier
                    .padding(horizontal = 24.dp)
                    .padding(bottom = 20.dp)
            )

            // Suggested symptom chips
            if (suggestedChips.isNotEmpty()) {
                Column(
                    modifier            = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 24.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    suggestedChips.take(4).chunked(2).forEach { rowChips ->
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            rowChips.forEach { label ->
                                SymptomChip(
                                    icon     = "🩺",
                                    label    = label,
                                    dark     = true,
                                    modifier = Modifier.weight(1f)
                                )
                            }
                            if (rowChips.size == 1) Spacer(modifier = Modifier.weight(1f))
                        }
                    }
                }
                Spacer(modifier = Modifier.height(24.dp))
            }

            // Push buttons to bottom
            Spacer(modifier = Modifier.weight(1f))

            // Large emergency call button
            Surface(
                onClick  = onCallEmergency,
                shape    = RoundedCornerShape(16.dp),
                color    = Color.White,
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 24.dp)
                    .height(68.dp)
            ) {
                Row(
                    modifier              = Modifier.fillMaxSize(),
                    verticalAlignment     = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.Center
                ) {
                    Icon(
                        imageVector        = Icons.Filled.Call,
                        contentDescription = "Call 000",
                        tint               = SeverityCritical,
                        modifier           = Modifier.size(28.dp)
                    )
                    Spacer(modifier = Modifier.width(12.dp))
                    Text(
                        text       = ctaLabel,
                        fontSize   = 20.sp,
                        fontWeight = FontWeight.Bold,
                        color      = SeverityCritical
                    )
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Start over
            OutlinedButton(
                onClick  = onStartOver,
                shape    = RoundedCornerShape(14.dp),
                colors   = ButtonDefaults.outlinedButtonColors(contentColor = Color.White),
                border   = androidx.compose.foundation.BorderStroke(
                    1.dp, Color.White.copy(alpha = 0.5f)
                ),
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 24.dp)
                    .height(52.dp)
            ) {
                Text(
                    text  = startOverLabel,
                    style = MaterialTheme.typography.bodyLarge,
                    color = Color.White
                )
            }

            Spacer(modifier = Modifier.height(32.dp))
        }
    }
}

// ── Severity reference strip ──────────────────────────────────────────────────
@Composable
private fun SeverityStrip(current: Severity) {
    val levels = listOf(
        Triple(Severity.LOW,      SeverityLow,      "Low"),
        Triple(Severity.MEDIUM,   SeverityMedium,   "Med"),
        Triple(Severity.HIGH,     SeverityHigh,     "High"),
        Triple(Severity.CRITICAL, SeverityCritical, "Crit"),
    )
    Row(
        modifier              = Modifier
            .fillMaxWidth()
            .padding(horizontal = 24.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        levels.forEach { (severity, color, label) ->
            val isActive = current == severity
            Column(
                modifier            = Modifier.weight(1f),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Surface(
                    shape    = CircleShape,
                    color    = if (isActive) color else Color(0xFFE0DBD5),
                    modifier = Modifier.size(if (isActive) 44.dp else 32.dp)
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        if (isActive) {
                            Box(
                                modifier = Modifier
                                    .size(16.dp)
                                    .background(Color.White.copy(alpha = 0.4f), CircleShape)
                            )
                        }
                    }
                }
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    text       = label,
                    style      = MaterialTheme.typography.labelMedium,
                    color      = if (isActive) color else TextSecondary,
                    fontWeight = if (isActive) FontWeight.Bold else FontWeight.Normal,
                    textAlign  = TextAlign.Center
                )
            }
        }
    }
}

// ── Symptom chip ──────────────────────────────────────────────────────────────
@Composable
fun SymptomChip(
    icon    : String,
    label   : String,
    dark    : Boolean  = false,
    modifier: Modifier = Modifier
) {
    Surface(
        shape    = RoundedCornerShape(50),
        color    = if (dark) Color.White.copy(alpha = 0.2f) else Color(0xFFFFF8F0),
        modifier = modifier
    ) {
        Row(
            modifier          = Modifier.padding(horizontal = 14.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(icon, fontSize = 16.sp)
            Spacer(modifier = Modifier.width(6.dp))
            Text(
                text       = label,
                style      = MaterialTheme.typography.bodyLarge,
                fontWeight = FontWeight.Bold,
                color      = if (dark) Color.White else Color(0xFF1A1A1A)
            )
        }
    }
}