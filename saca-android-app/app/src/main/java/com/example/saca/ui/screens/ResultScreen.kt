package com.example.saca.ui.screens

import android.content.Context
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Call
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.saca.model.Language
import com.example.saca.model.Severity
import com.example.saca.viewmodel.TriageViewModel

// ── Triage level (3-level, mirrors Windows) ───────────────────────────────────
private enum class TriageLevel { MILD, MODERATE, CRITICAL }

private fun Severity.toTriage() = when (this) {
    Severity.LOW      -> TriageLevel.MILD
    Severity.MEDIUM   -> TriageLevel.MODERATE
    Severity.HIGH     -> TriageLevel.MODERATE   // HIGH maps to MODERATE on mobile
    Severity.CRITICAL -> TriageLevel.CRITICAL
}

// ── Palette (exact Windows _P values) ────────────────────────────────────────
private data class TriagePalette(
    val bg:        Color,
    val bgDark:    Color,
    val bgLight:   Color,
    val text:      Color,
    val stepBg:    Color,
    val stepNum:   Color,
    val escBg:     Color,
    val escBorder: Color,
    val escText:   Color,
)

private val P_MILD = TriagePalette(
    bg        = Color(0xFF1CA34A),
    bgDark    = Color(0xFF157A37),
    bgLight   = Color(0xFFD8F4DF),
    text      = Color(0xFF157A37),
    stepBg    = Color(0xFFF0FAF3),
    stepNum   = Color(0xFF1CA34A),
    escBg     = Color(0xFFFFFBEA),
    escBorder = Color(0xFFE6B800),
    escText   = Color(0xFF7A5700),
)
private val P_MODERATE = TriagePalette(
    bg        = Color(0xFFC65D2E),
    bgDark    = Color(0xFF9E3D18),
    bgLight   = Color(0xFFFFF0E8),
    text      = Color(0xFF9E3D18),
    stepBg    = Color(0xFFFFF8F4),
    stepNum   = Color(0xFFC65D2E),
    escBg     = Color(0xFFFFF0E8),
    escBorder = Color(0xFFC65D2E),
    escText   = Color(0xFF9E3D18),
)
private val P_CRITICAL = TriagePalette(
    bg        = Color(0xFFC00000),
    bgDark    = Color(0xFF8B0000),
    bgLight   = Color(0xFFFFE0E0),
    text      = Color(0xFF8B0000),
    stepBg    = Color(0xFFFFF5F5),
    stepNum   = Color(0xFFC00000),
    escBg     = Color(0xFFFFE0E0),
    escBorder = Color(0xFFC00000),
    escText   = Color(0xFF8B0000),
)

private fun TriageLevel.palette() = when (this) {
    TriageLevel.MILD     -> P_MILD
    TriageLevel.MODERATE -> P_MODERATE
    TriageLevel.CRITICAL -> P_CRITICAL
}

// ── Static content (mirrors Windows _ICONS / _LABELS / _CTA / _ESC) ──────────
private fun TriageLevel.icon() = when (this) {
    TriageLevel.MILD     -> "✅"
    TriageLevel.MODERATE -> "⚠️"
    TriageLevel.CRITICAL -> "🚨"
}

private fun TriageLevel.verdictEN() = when (this) {
    TriageLevel.MILD     -> "Rest at Home"
    TriageLevel.MODERATE -> "See a Clinic"
    TriageLevel.CRITICAL -> "Call 000 Now"
}
private fun TriageLevel.verdictKR() = when (this) {
    TriageLevel.MILD     -> "Rest langa Haus"
    TriageLevel.MODERATE -> "Go langa Klinik"
    TriageLevel.CRITICAL -> "Kol 000 Nau"
}
private fun TriageLevel.verdict(kr: Boolean) = if (kr) verdictKR() else verdictEN()

private fun TriageLevel.ctaEN() = when (this) {
    TriageLevel.MILD     -> "What should I do?  →"
    TriageLevel.MODERATE -> "📞  What should I do?  →"
    TriageLevel.CRITICAL -> "📞  What should I do?  →"
}
private fun TriageLevel.ctaKR() = when (this) {
    TriageLevel.MILD     -> "Wanim fo du?  →"
    TriageLevel.MODERATE -> "📞  Wanim fo du?  →"
    TriageLevel.CRITICAL -> "📞  Wanim fo du?  →"
}
private fun TriageLevel.cta(kr: Boolean) = if (kr) ctaKR() else ctaEN()

private fun TriageLevel.escEN() = when (this) {
    TriageLevel.MILD     -> "ℹ If you get worse, call the clinic."
    TriageLevel.MODERATE -> "⚠ If breathing becomes hard, chest pain starts, or you collapse, use Emergency Help."
    TriageLevel.CRITICAL -> "⚠ This is serious. Get help now."
}
private fun TriageLevel.escKR() = when (this) {
    TriageLevel.MILD     -> "ℹ If yu kam nogud, kolim klinik."
    TriageLevel.MODERATE -> "⚠ If brith kam had, jes pein stat, o yu poldaun, yusim Imijensi Elp."
    TriageLevel.CRITICAL -> "⚠ Diswan mait bigwan. Garr elp nau."
}
private fun TriageLevel.esc(kr: Boolean) = if (kr) escKR() else escEN()

private fun TriageLevel.stepsEN() = when (this) {
    TriageLevel.MILD     -> listOf("Rest", "Drink water", "Monitor your symptoms")
    TriageLevel.MODERATE -> listOf(
        "Call clinic today or tomorrow",
        "Rest while waiting",
        "Seek help faster if symptoms get worse",
    )
    TriageLevel.CRITICAL -> listOf(
        "Call 000",
        "Do not drive yourself",
        "Ask someone nearby for help",
    )
}
private fun TriageLevel.stepsKR() = when (this) {
    TriageLevel.MILD     -> listOf("Rest", "Dringgim woda", "Lukluk simptom")
    TriageLevel.MODERATE -> listOf(
        "Kol klinik tidei o tumoro",
        "Rest wen yu weit",
        "Garr elp kwik if simptom kam nogud",
    )
    TriageLevel.CRITICAL -> listOf(
        "Kol 000",
        "No draib yuself",
        "Askim sambodi neba fo help",
    )
}
private fun TriageLevel.steps(kr: Boolean) = if (kr) stepsKR() else stepsEN()

// ── Hero sidebar (left panel — dark terracotta, matches Windows _HeroPanel) ───
@Composable
private fun HeroPanel(
    triage:    TriageLevel,
    condition: String,
    kr:        Boolean,
    modifier:  Modifier = Modifier,
) {
    val alpha  by remember { mutableStateOf(0f) }
    var visible by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) { visible = true }

    Box(
        modifier = modifier
            .fillMaxHeight()
            .background(Color(0xD18B3A2E))  // semi-transparent dark terracotta
            .padding(horizontal = 20.dp),
        contentAlignment = Alignment.Center,
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
        ) {
            // Gold accent bar
            Box(
                Modifier
                    .size(width = 40.dp, height = 4.dp)
                    .clip(RoundedCornerShape(2.dp))
                    .background(Color(0xFFD4A017))
            )
            Spacer(Modifier.height(20.dp))

            AnimatedVisibility(
                visible = visible,
                enter   = fadeIn(tween(500)) + scaleIn(tween(500)),
            ) {
                Text(triage.icon(), fontSize = 52.sp, textAlign = TextAlign.Center)
            }

            Spacer(Modifier.height(14.dp))

            AnimatedVisibility(
                visible = visible,
                enter   = fadeIn(tween(600, delayMillis = 120)),
            ) {
                Text(
                    text       = triage.verdict(kr),
                    fontSize   = 18.sp,
                    fontWeight = FontWeight.Black,
                    color      = Color(0xFFFDFAF6),
                    textAlign  = TextAlign.Center,
                    lineHeight = 24.sp,
                )
            }

            Spacer(Modifier.height(8.dp))

            AnimatedVisibility(
                visible = visible,
                enter   = fadeIn(tween(600, delayMillis = 200)),
            ) {
                Text(
                    text      = condition,
                    fontSize  = 12.sp,
                    color     = Color(0xB3FDFAF6),
                    textAlign = TextAlign.Center,
                    lineHeight = 17.sp,
                )
            }
        }
    }
}

// ── Step dot indicator ────────────────────────────────────────────────────────
@Composable
private fun StepDots(current: Int) {
    Row(
        horizontalArrangement = Arrangement.spacedBy(8.dp),
        verticalAlignment     = Alignment.CenterVertically,
    ) {
        repeat(2) { idx ->
            val active = idx == current
            Box(
                Modifier
                    .size(if (active) 10.dp else 7.dp)
                    .clip(CircleShape)
                    .background(
                        if (active) Color.White
                        else Color.White.copy(alpha = 0.40f)
                    )
            )
        }
    }
}

// ── Step 1 — Verdict card ─────────────────────────────────────────────────────
@Composable
private fun Step1Card(
    triage:    TriageLevel,
    condition: String,
    kr:        Boolean,
    palette:   TriagePalette,
    onNext:    () -> Unit,
    onEmergency: () -> Unit,
) {
    var visible by remember { mutableStateOf(false) }
    LaunchedEffect(Unit) { visible = true }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(
                Brush.verticalGradient(listOf(palette.bg, palette.bgDark))
            ),
        contentAlignment = Alignment.Center,
    ) {
        Column(
            modifier            = Modifier
                .fillMaxWidth()
                .padding(horizontal = 32.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
        ) {

            // Icon
            AnimatedVisibility(
                visible = visible,
                enter   = fadeIn(tween(500)) + scaleIn(
                    initialScale   = 0.6f,
                    animationSpec  = spring(Spring.DampingRatioMediumBouncy),
                ),
            ) {
                Text(triage.icon(), fontSize = 96.sp, textAlign = TextAlign.Center)
            }

            Spacer(Modifier.height(24.dp))

            // Verdict
            AnimatedVisibility(
                visible = visible,
                enter   = fadeIn(tween(600, delayMillis = 120)) + slideInVertically(
                    initialOffsetY = { it / 4 },
                    animationSpec  = tween(600, delayMillis = 120),
                ),
            ) {
                Text(
                    text       = triage.verdict(kr),
                    fontSize   = 42.sp,
                    fontWeight = FontWeight.ExtraBold,
                    color      = Color.White,
                    textAlign  = TextAlign.Center,
                    lineHeight = 50.sp,
                )
            }

            Spacer(Modifier.height(12.dp))

            // Condition subtitle
            AnimatedVisibility(
                visible = visible,
                enter   = fadeIn(tween(600, delayMillis = 200)),
            ) {
                Text(
                    text      = condition,
                    fontSize  = 18.sp,
                    color     = Color.White.copy(alpha = 0.80f),
                    textAlign = TextAlign.Center,
                )
            }

            Spacer(Modifier.height(36.dp))

            // CTA button — "What should I do? →"
            AnimatedVisibility(
                visible = visible,
                enter   = fadeIn(tween(500, delayMillis = 300)) + scaleIn(
                    initialScale  = 0.85f,
                    animationSpec = tween(500, delayMillis = 300),
                ),
            ) {
                Button(
                    onClick  = onNext,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(56.dp),
                    shape  = RoundedCornerShape(16.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color.White.copy(alpha = 0.18f),
                        contentColor   = Color.White,
                    ),
                    border = BorderStroke(2.dp, Color.White.copy(alpha = 0.55f)),
                ) {
                    Text(
                        text       = triage.cta(kr),
                        fontSize   = 17.sp,
                        fontWeight = FontWeight.ExtraBold,
                    )
                }
            }

            Spacer(Modifier.height(16.dp))

            // Step dots
            StepDots(current = 0)
        }

        // Emergency button — bottom right floating
        if (triage == TriageLevel.CRITICAL) {
            Button(
                onClick  = onEmergency,
                modifier = Modifier
                    .align(Alignment.BottomCenter)
                    .padding(bottom = 40.dp, start = 32.dp, end = 32.dp)
                    .fillMaxWidth()
                    .height(60.dp),
                shape  = RoundedCornerShape(16.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color.White,
                    contentColor   = Color(0xFFC00000),
                ),
            ) {
                Icon(Icons.Filled.Call, contentDescription = null, modifier = Modifier.size(22.dp))
                Spacer(Modifier.width(10.dp))
                Text(
                    text       = if (kr) "KOL 000 NAU" else "CALL 000 NOW",
                    fontSize   = 18.sp,
                    fontWeight = FontWeight.Black,
                )
            }
        }
    }
}

// ── Step 2 — What to do + What we found ──────────────────────────────────────
@Composable
private fun Step2Card(
    triage:   TriageLevel,
    steps:    List<String>,
    symptoms: List<String>,
    kr:       Boolean,
    palette:  TriagePalette,
    onStartOver: () -> Unit,
    onEmergency: () -> Unit,
) {
    val scrollState = rememberScrollState()

    val todoTitle  = if (kr) "Wanim fo du"      else "What to do"
    val foundTitle = if (kr) "Wanim bin faindim" else "What we found"
    val startAgain = if (kr) "↻  Stat Agen"     else "↻  Start Again"
    val emergency  = if (kr) "⚠️  Imijensi"     else "⚠️  Emergency"

    Column(modifier = Modifier.fillMaxSize()) {

        Column(
            modifier = Modifier
                .weight(1f)
                .verticalScroll(scrollState)
                .padding(horizontal = 20.dp, vertical = 16.dp),
        ) {

            // ── "What to do" heading ──────────────────────────────────────
            Text(
                text       = todoTitle,
                fontSize   = 13.sp,
                fontWeight = FontWeight.Black,
                color      = palette.text,
                letterSpacing = 0.6.sp,
            )
            Spacer(Modifier.height(10.dp))

            // Numbered step cards (large text — low-literacy design)
            steps.forEachIndexed { idx, step ->
                StepCard(
                    number  = idx + 1,
                    text    = step,
                    palette = palette,
                )
                Spacer(Modifier.height(10.dp))
            }

            Spacer(Modifier.height(16.dp))

            // ── "What we found" heading ───────────────────────────────────
            if (symptoms.isNotEmpty()) {
                Text(
                    text       = foundTitle,
                    fontSize   = 13.sp,
                    fontWeight = FontWeight.Black,
                    color      = palette.text,
                    letterSpacing = 0.6.sp,
                )
                Spacer(Modifier.height(10.dp))

                // Symptom chip card
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .shadow(2.dp, RoundedCornerShape(14.dp))
                        .background(Color.White, RoundedCornerShape(14.dp))
                        .border(1.dp, palette.bg.copy(alpha = 0.12f), RoundedCornerShape(14.dp))
                        .padding(horizontal = 20.dp, vertical = 16.dp),
                ) {
                    Text(
                        text       = symptoms.take(6).joinToString("  ·  "),
                        fontSize   = 16.sp,
                        fontWeight = FontWeight.SemiBold,
                        color      = Color(0xFF1C1C1C),
                        lineHeight = 24.sp,
                    )
                }

                Spacer(Modifier.height(16.dp))
            }

            // ── Escalation strip ─────────────────────────────────────────
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(14.dp))
                    .background(palette.escBg)
                    .border(1.5.dp, palette.escBorder, RoundedCornerShape(14.dp))
                    .padding(horizontal = 20.dp, vertical = 16.dp),
            ) {
                Text(
                    text       = triage.esc(kr),
                    fontSize   = 15.sp,
                    fontWeight = FontWeight.SemiBold,
                    color      = palette.escText,
                    lineHeight = 22.sp,
                )
            }

            Spacer(Modifier.height(8.dp))

            // Step dots
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.Center,
            ) {
                StepDots(current = 1)
            }
        }

        // ── Nav bar — Start Again + Emergency ────────────────────────────
        HorizontalDivider(color = Color(0xFFE0D0C8), thickness = 1.dp)
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .background(Color(0xFFFDFAF6))
                .padding(horizontal = 16.dp, vertical = 12.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            OutlinedButton(
                onClick  = onStartOver,
                modifier = Modifier
                    .weight(1f)
                    .height(52.dp),
                shape  = RoundedCornerShape(14.dp),
                colors = ButtonDefaults.outlinedButtonColors(contentColor = Color(0xFF2D1810)),
                border = BorderStroke(1.5.dp, Color(0xFFD4B8B0)),
            ) {
                Text(startAgain, fontWeight = FontWeight.Bold, fontSize = 14.sp)
            }

            Button(
                onClick  = onEmergency,
                modifier = Modifier
                    .weight(1f)
                    .height(52.dp),
                shape  = RoundedCornerShape(14.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(0xFF8B3A2E),
                    contentColor   = Color.White,
                ),
            ) {
                Text(emergency, fontWeight = FontWeight.Black, fontSize = 14.sp)
            }
        }
    }
}

// ── Numbered step card ────────────────────────────────────────────────────────
@Composable
private fun StepCard(number: Int, text: String, palette: TriagePalette) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .shadow(2.dp, RoundedCornerShape(14.dp))
            .background(palette.stepBg, RoundedCornerShape(14.dp))
            .padding(horizontal = 18.dp, vertical = 14.dp),
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            // Numbered circle
            Box(
                modifier         = Modifier
                    .size(36.dp)
                    .clip(CircleShape)
                    .background(palette.stepNum),
                contentAlignment = Alignment.Center,
            ) {
                Text(
                    text       = number.toString(),
                    fontSize   = 16.sp,
                    fontWeight = FontWeight.ExtraBold,
                    color      = Color.White,
                )
            }

            // Step text — large for low-literacy (matches Windows 32sp)
            Text(
                text       = text,
                fontSize   = 22.sp,
                fontWeight = FontWeight.SemiBold,
                color      = Color(0xFF1C1C1C),
                lineHeight = 30.sp,
                modifier   = Modifier.weight(1f),
            )
        }
    }
}

// ── Emergency dialog ──────────────────────────────────────────────────────────
@Composable
private fun EmergencyCallDialog(
    kr:        Boolean,
    onConfirm: () -> Unit,
    onDismiss: () -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Text(
                text       = if (kr) "Kol 000?" else "Call 000?",
                fontWeight = FontWeight.Black,
                fontSize   = 20.sp,
            )
        },
        text = {
            Text(
                text     = if (kr) "Diswan bai kol imijensi sọvis."
                else "This will call emergency services.",
                fontSize = 16.sp,
            )
        },
        confirmButton = {
            Button(
                onClick = onConfirm,
                colors  = ButtonDefaults.buttonColors(containerColor = Color(0xFFC00000)),
            ) {
                Icon(Icons.Filled.Call, contentDescription = null)
                Spacer(Modifier.width(8.dp))
                Text(if (kr) "Kol 000" else "Call 000", fontWeight = FontWeight.Bold)
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text(if (kr) "Kansol" else "Cancel")
            }
        },
    )
}

// ── Main entry point ──────────────────────────────────────────────────────────
/**
 * 2-step paginated result screen — mirrors Windows ResultPage exactly.
 *
 * Step 0: Full-screen coloured verdict card with icon + verdict + CTA button
 * Step 1: Scrollable detail panel — numbered step cards, symptoms, escalation strip
 *
 * Left hero sidebar is persistent across both steps (visible on tablets / landscape).
 * On portrait phones the hero is hidden (space constrained) to keep cards full-width.
 */
@Composable
fun ResultScreen(
    viewModel:                TriageViewModel,
    onBack:                   () -> Unit,
    onStartOver:              () -> Unit,
    onEmergencyCallConfirmed: () -> Unit,
) {
    val inferenceResult  by viewModel.inferenceResult.collectAsState()
    val language         by viewModel.language.collectAsState()
    val kr               = language == Language.KRIOL

    val severity = inferenceResult?.severity ?: Severity.LOW
    val triage   = severity.toTriage()
    val palette  = triage.palette()

    // Collect detected symptoms for Step 2
    val suggestedSymptoms = inferenceResult?.suggestedSymptoms ?: emptyList()

    // Condition name from suggested symptoms or generic fallback
    val condition = remember(suggestedSymptoms, triage, kr) {
        conditionName(suggestedSymptoms, triage, kr)
    }

    // Steps for Step 2 — use inferenceResult steps if available, else defaults
    val steps = remember(triage, kr) { triage.steps(kr) }

    // Pagination state (0 = verdict, 1 = details)
    var currentStep by remember { mutableStateOf(0) }

    // Emergency dialog
    var showEmergencyDialog by remember { mutableStateOf(false) }

    // Vibrate on CRITICAL
    val context = LocalContext.current
    LaunchedEffect(triage) {
        if (triage == TriageLevel.CRITICAL) vibrateDevice(context)

        // narrate verdict
        val severityKey = when (severity) {
            Severity.LOW -> "result_mild"
            Severity.MEDIUM -> "result_moderate"
            Severity.HIGH -> "result_moderate"
            Severity.CRITICAL -> "result_critical"
        }

            viewModel.narrationManager.narrate(
            text      = triage.verdict(kr),
            language  = language,
            screenKey = severityKey,
        )
    }

    if (showEmergencyDialog) {
        EmergencyCallDialog(
            kr        = kr,
            onConfirm = { showEmergencyDialog = false; onEmergencyCallConfirmed() },
            onDismiss = { showEmergencyDialog = false },
        )
    }

    // ── Layout: left hero + right paginated content ───────────────────────
    Row(modifier = Modifier.fillMaxSize()) {

        // Hero sidebar — hidden on narrow screens to give cards full width
        // Use windowSizeClass in production; here we fix at 100dp which collapses cleanly
        Box(
            modifier = Modifier
                .width(100.dp)
                .fillMaxHeight()
        ) {
            HeroPanel(triage = triage, condition = condition, kr = kr, modifier = Modifier.fillMaxSize())
        }

        // Right content — animated crossfade between steps
        Box(modifier = Modifier.weight(1f).fillMaxHeight()) {
            AnimatedContent(
                targetState   = currentStep,
                transitionSpec = {
                    if (targetState > initialState) {
                        slideInHorizontally { it } + fadeIn() togetherWith
                                slideOutHorizontally { -it } + fadeOut()
                    } else {
                        slideInHorizontally { -it } + fadeIn() togetherWith
                                slideOutHorizontally { it } + fadeOut()
                    }
                },
                label = "result_step",
            ) { step ->
                when (step) {
                    0 -> Step1Card(
                        triage    = triage,
                        condition = condition,
                        kr        = kr,
                        palette   = palette,
                        onNext    = { currentStep = 1 },
                        onEmergency = { showEmergencyDialog = true },
                    )
                    else -> Step2Card(
                        triage      = triage,
                        steps       = steps,
                        symptoms    = suggestedSymptoms,
                        kr          = kr,
                        palette     = palette,
                        onStartOver = onStartOver,
                        onEmergency = { showEmergencyDialog = true },
                    )
                }
            }
        }
    }
}

// ── Condition name helper (mirrors Windows _condition_name) ───────────────────
private fun conditionName(symptoms: List<String>, triage: TriageLevel, kr: Boolean): String {
    val s = symptoms.toSet()
    return when {
        triage == TriageLevel.CRITICAL && s.any { it in setOf(
            "chest_pain","severe_chest_pain","difficulty_breathing","shortness_of_breath") } ->
            if (kr) "Mait bigwan hat o lank trabul" else "Possible heart or lung emergency"

        triage == TriageLevel.CRITICAL && s.any { it in setOf(
            "severe_headache","confusion","facial_drooping","seizure") } ->
            if (kr) "Mait bigwan bren trabul" else "Possible brain emergency"

        triage == TriageLevel.CRITICAL ->
            if (kr) "Bigwan imijensi" else "Medical emergency"

        s.any { it in setOf("chest_pain","chest_tightness","palpitations","coughing_blood") } ->
            if (kr) "Jes o hat trabul" else "Chest or heart concern"

        s.any { it in setOf("abdominal_pain","severe_abdominal_pain","nausea","vomiting") } ->
            if (kr) "Beli trabul" else "Abdominal concern"

        s.any { it in setOf("headache","severe_headache","dizziness","blurred_vision") } ->
            if (kr) "Hedake o dizi" else "Headache or dizziness"

        s.any { it in setOf("fever","high_fever","chills","body_aches") } ->
            if (kr) "Fiba o infeksen" else "Fever or infection"

        s.any { it in setOf("cough","wheezing","shortness_of_breath","difficulty_breathing") } ->
            if (kr) "Brith trabul" else "Breathing concern"

        else ->
            if (kr) "Jeneral helt trabul" else "General health concern"
    }
}

// ── Vibrate helper ────────────────────────────────────────────────────────────
private fun vibrateDevice(context: Context) {
    try {
        val vibrator = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            (context.getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as VibratorManager).defaultVibrator
        } else {
            @Suppress("DEPRECATION")
            context.getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            vibrator.vibrate(VibrationEffect.createWaveform(longArrayOf(0, 200, 100, 200, 100, 200), -1))
        } else {
            @Suppress("DEPRECATION")
            vibrator.vibrate(longArrayOf(0, 200, 100, 200, 100, 200), -1)
        }
    } catch (_: Exception) {}
}