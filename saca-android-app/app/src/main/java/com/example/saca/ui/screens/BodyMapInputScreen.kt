package com.example.saca.ui.screens

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.saca.R
import com.example.saca.model.*
import com.example.saca.ui.components.BodyDiagramCanvas
import com.example.saca.ui.components.SymptomPickerSheet
import com.example.saca.ui.components.SacaTopBar
import com.example.saca.viewmodel.TriageViewModel

// ── Colour palette (matches Windows SymptomSelectionPage) ─────────────────────
private val Terracotta     = Color(0xFF8B3A2E)
private val TerracottaDark = Color(0xFF6B2A1E)
private val PageBg         = Color(0xFFFDFAF6)
private val ChipBg         = Color(0xFF8B3A2E)
private val ChipText       = Color.White
private val ZoneBtnBg      = Color(0xFFF2E8E3)
private val ZoneBtnText    = Color(0xFF5A2A1E)
private val ZoneBtnBorder  = Color(0xFFD4B8B0)
private val ActiveZoneBg   = Color(0xFF8B3A2E)
private val ActiveZoneText = Color.White
private val DividerColor   = Color(0xFFE8D5CC)
private val HintText       = Color(0xFF8B6B5A)
private val HeadingColor   = Color(0xFF2D1810)
private val WholeBtnBg     = Color(0xFF8B3A2E)

/**
 * Body map symptom input screen.
 *
 * Replaces the old emoji-grid [PictogramInputScreen].
 * Architecture mirrors the Windows [SymptomSelectionPage]:
 *  - Left: 2D body diagram (tap zones)
 *  - Right: scrollable zone buttons
 *  - Bottom: selected symptom chips + Next button
 *
 * Tapping a zone or zone button opens [SymptomPickerSheet].
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BodyMapInputScreen(
    viewModel: TriageViewModel,
    onNext: () -> Unit,
    onBack: () -> Unit,
) {
    val language        by viewModel.language.collectAsState()
    val isKriol         = language == Language.KRIOL

    // vocab → display label (English or Kriol)
    var selected by remember { mutableStateOf<Map<String, String>>(emptyMap()) }

    // Which region popup is open (null = closed)
    var openRegion by remember { mutableStateOf<String?>(null) }

    // Compute active regions (any region that has ≥1 selected symptom)
    val activeRegions by remember(selected) {
        derivedStateOf {
            BODY_REGION_SYMPTOMS.entries
                .filter { (_, symptoms) -> symptoms.any { it.vocab in selected } }
                .map { it.key }
                .toSet()
        }
    }

    // Localised strings
    val heading    = if (isKriol) "Klik we i hati"            else "Tap where it hurts"
    val subheading = if (isKriol) "Selektem wan pat bodi"      else "Select a body part then choose your symptoms"
    val zoneHint   = if (isKriol) "Tapim wan son:"             else "Tap a zone:"
    val wholeLabel = if (isKriol) "🌡  Ol bodi / Jeneral"     else "🌡  Whole body / General"
    val nextLabel  = if (isKriol) "Nekis  →"                  else "Next  →"
    val noSymptoms = if (isKriol) "No sikwan sain jusum yet"   else "No symptoms selected yet"

    fun countLabel(): String {
        val n = selected.size
        return when {
            n == 0 -> noSymptoms
            n == 1 -> if (isKriol) "1 sikwan sain jusum — klik moa pat bodi"
                      else "1 symptom selected — tap more body parts to add"
            else   -> if (isKriol) "$n sikwan sain jusum" else "$n symptoms selected"
        }
    }

    Box(modifier = Modifier.fillMaxSize()) {

        // Background image
        Image(
            painter       = painterResource(id = R.drawable.saca_background),
            contentDescription = null,
            modifier      = Modifier.fillMaxSize(),
            contentScale  = ContentScale.Crop,
        )
        Box(
            Modifier
                .fillMaxSize()
                .background(Color(0xE6F5F0EB))
        )

        Column(modifier = Modifier.fillMaxSize()) {

            // ── Top bar ──────────────────────────────────────────────────────
            SacaTopBar(
                currentLanguage = language,
                onLanguageToggle = { viewModel.setLanguage(it) },
                onBack = onBack,
            )

            // ── Heading row ──────────────────────────────────────────────────
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 20.dp, vertical = 8.dp),
            ) {
                Text(
                    text       = heading,
                    fontSize   = 24.sp,
                    fontWeight = FontWeight.Black,
                    color      = HeadingColor,
                )
                Text(
                    text       = subheading,
                    fontSize   = 13.sp,
                    fontWeight = FontWeight.SemiBold,
                    color      = HintText,
                )
            }

            // ── Body diagram + zone buttons (side by side) ───────────────────
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f)
                    .padding(horizontal = 16.dp),
                horizontalArrangement = Arrangement.spacedBy(16.dp),
                verticalAlignment = Alignment.Top,
            ) {

                // Left: body diagram
                BodyDiagramCanvas(
                    activeRegions = activeRegions,
                    canvasWidth   = 160.dp,
                    modifier      = Modifier
                        .width(160.dp)
                        .fillMaxHeight(),
                    onRegionClick = { region -> openRegion = region },
                )

                // Right: zone buttons panel
                Column(
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxHeight(),
                    verticalArrangement = Arrangement.spacedBy(6.dp),
                ) {
                    Spacer(Modifier.height(4.dp))
                    Text(
                        text       = zoneHint,
                        fontSize   = 11.sp,
                        fontWeight = FontWeight.Black,
                        color      = Terracotta,
                    )

                    // 2-column grid of zone buttons
                    val zoneKeys = BODY_ZONE_KEYS
                    LazyVerticalGrid(
                        columns = GridCells.Fixed(2),
                        modifier = Modifier
                            .fillMaxWidth()
                            .weight(1f),
                        horizontalArrangement = Arrangement.spacedBy(6.dp),
                        verticalArrangement   = Arrangement.spacedBy(6.dp),
                        userScrollEnabled = false,
                    ) {
                        items(zoneKeys) { key ->
                            val info   = BODY_REGION_LABELS[key]
                            val label  = info?.title(isKriol) ?: key
                            val emoji  = info?.emoji ?: "•"
                            val isActive = key in activeRegions

                            ZoneButton(
                                emoji    = emoji,
                                label    = label,
                                isActive = isActive,
                                onClick  = { openRegion = key },
                            )
                        }
                    }

                    // Whole body button (full width, prominent)
                    Spacer(Modifier.height(4.dp))
                    Button(
                        onClick = { openRegion = "whole_body" },
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(38.dp),
                        shape  = RoundedCornerShape(10.dp),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = if ("whole_body" in activeRegions) TerracottaDark else WholeBtnBg,
                            contentColor   = Color.White,
                        ),
                        contentPadding = PaddingValues(horizontal = 12.dp),
                    ) {
                        Text(wholeLabel, fontSize = 11.sp, fontWeight = FontWeight.Black,
                            maxLines = 1, overflow = TextOverflow.Ellipsis)
                    }
                }
            }

            // ── Divider + chip row ───────────────────────────────────────────
            Spacer(Modifier.height(8.dp))
            HorizontalDivider(
                modifier  = Modifier.padding(horizontal = 16.dp),
                color     = DividerColor,
                thickness = 1.dp,
            )
            Spacer(Modifier.height(6.dp))

            // Count label
            Text(
                text     = countLabel(),
                modifier = Modifier.padding(horizontal = 20.dp),
                fontSize = 12.sp,
                fontWeight = FontWeight.ExtraBold,
                color = HintText,
            )
            Spacer(Modifier.height(6.dp))

            // Horizontal scroll chip strip
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(44.dp)
                    .horizontalScroll(rememberScrollState())
                    .padding(horizontal = 16.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                selected.forEach { (vocab, label) ->
                    SelectedSymptomChip(
                        label   = label,
                        onRemove = {
                            selected = selected - vocab
                        },
                    )
                }
            }

            Spacer(Modifier.height(10.dp))

            // ── Bottom action row ────────────────────────────────────────────
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 8.dp),
                horizontalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                // Emergency button
                OutlinedButton(
                    onClick = { /* viewModel.triggerEmergency() */ },
                    modifier = Modifier
                        .weight(1f)
                        .height(52.dp),
                    shape  = RoundedCornerShape(14.dp),
                    colors = ButtonDefaults.outlinedButtonColors(contentColor = Terracotta),
                    border = androidx.compose.foundation.BorderStroke(2.dp, Terracotta),
                ) {
                    Text(
                        text       = if (isKriol) "⚠  Imijensi" else "⚠  Emergency",
                        fontWeight = FontWeight.Black,
                        fontSize   = 14.sp,
                    )
                }

                // Next button
                Button(
                    onClick  = {
                        if (selected.isNotEmpty()) {
                            // Push selected vocab keys into the viewModel symptom list
                            viewModel.setSelectedSymptomsFromBodyMap(selected.keys.toList())
                            onNext()
                        }
                    },
                    enabled  = selected.isNotEmpty(),
                    modifier = Modifier
                        .weight(2f)
                        .height(52.dp),
                    shape  = RoundedCornerShape(14.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor         = Terracotta,
                        disabledContainerColor = Color(0xFFD4B8B0),
                        contentColor           = Color.White,
                        disabledContentColor   = Color.White,
                    ),
                ) {
                    Text(nextLabel, fontWeight = FontWeight.Black, fontSize = 16.sp)
                }
            }
        }
    }

    // ── Symptom picker bottom sheet ───────────────────────────────────────────
    openRegion?.let { region ->
        SymptomPickerSheet(
            regionKey       = region,
            alreadySelected = selected.keys.toSet(),
            isKriol         = isKriol,
            onConfirm       = { rk, vocabList ->
                // Remove any previously selected symptoms for this region
                val regionVocab = BODY_REGION_SYMPTOMS[rk]?.map { it.vocab }?.toSet() ?: emptySet()
                val retained    = selected.filter { it.key !in regionVocab }

                // Add newly confirmed symptoms with correct display label
                val regionSymptoms = BODY_REGION_SYMPTOMS[rk] ?: emptyList()
                val added = vocabList.associateWith { vocab ->
                    regionSymptoms.find { it.vocab == vocab }?.label(isKriol) ?: vocab
                }

                selected = retained + added
                openRegion = null
            },
            onDismiss = { openRegion = null },
        )
    }
}

// ── Zone button ───────────────────────────────────────────────────────────────

@Composable
private fun ZoneButton(
    emoji: String,
    label: String,
    isActive: Boolean,
    onClick: () -> Unit,
) {
    val bg     = if (isActive) ActiveZoneBg   else ZoneBtnBg
    val text   = if (isActive) ActiveZoneText else ZoneBtnText
    val border = if (isActive) ActiveZoneBg   else ZoneBtnBorder

    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(34.dp)
            .clip(RoundedCornerShape(8.dp))
            .background(bg)
            .border(1.dp, border, RoundedCornerShape(8.dp))
            .clickable(onClick = onClick)
            .padding(horizontal = 8.dp),
        contentAlignment = Alignment.CenterStart,
    ) {
        Text(
            text       = "$emoji  $label",
            fontSize   = 11.sp,
            fontWeight = FontWeight.Bold,
            color      = text,
            maxLines   = 1,
            overflow   = TextOverflow.Ellipsis,
        )
    }
}

// ── Selected symptom chip (dismissable) ───────────────────────────────────────

@Composable
private fun SelectedSymptomChip(
    label: String,
    onRemove: () -> Unit,
) {
    Surface(
        shape = RoundedCornerShape(17.dp),
        color = Terracotta,
    ) {
        Row(
            modifier            = Modifier.padding(horizontal = 14.dp, vertical = 6.dp),
            horizontalArrangement = Arrangement.spacedBy(6.dp),
            verticalAlignment   = Alignment.CenterVertically,
        ) {
            Text(
                text       = label,
                fontSize   = 13.sp,
                fontWeight = FontWeight.ExtraBold,
                color      = Color.White,
            )
            Box(
                modifier = Modifier
                    .size(18.dp)
                    .clip(CircleShape)
                    .clickable(onClick = onRemove),
                contentAlignment = Alignment.Center,
            ) {
                Text("×", fontSize = 15.sp, color = Color.White, fontWeight = FontWeight.Bold)
            }
        }
    }
}