package com.example.saca.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
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
import com.example.saca.model.BODY_REGION_LABELS
import com.example.saca.model.BODY_REGION_SYMPTOMS
import com.example.saca.model.BodySymptom
import com.example.saca.model.label
import com.example.saca.model.title

private val Terracotta    = Color(0xFF8B3A2E)
private val TerracottaDark = Color(0xFF6B2A1E)
private val ChipBg        = Color(0xFFFDF3EE)
private val ChipBorder    = Color(0xFFD4B8B0)
private val SheetBg       = Color(0xFFFDFAF6)
private val DividerColor  = Color(0xFFE8D5CC)
private val HintText      = Color(0xFF8B6B5A)
private val HeadingColor  = Color(0xFF2D1810)

/**
 * Bottom sheet symptom picker — mirrors Windows SymptomPopup.
 *
 * @param regionKey        e.g. "chest"
 * @param alreadySelected  vocab keys already selected globally
 * @param isKriol          language toggle
 * @param onConfirm        called with (regionKey, list of selected vocab keys)
 * @param onDismiss        close without saving
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SymptomPickerSheet(
    regionKey: String,
    alreadySelected: Set<String>,
    isKriol: Boolean,
    onConfirm: (String, List<String>) -> Unit,
    onDismiss: () -> Unit,
) {
    val info     = BODY_REGION_LABELS[regionKey]
    val symptoms = BODY_REGION_SYMPTOMS[regionKey] ?: emptyList()

    // Pre-fill from globally selected that belong to this region
    val regionVocab = symptoms.map { it.vocab }.toSet()
    val initial     = alreadySelected.filter { it in regionVocab }.toSet()

    var checked by remember { mutableStateOf(initial) }

    val title = info?.title(isKriol) ?: regionKey
    val emoji = info?.emoji ?: "🩺"

    val hintText = if (isKriol) "Klik fo selektem. Klik agen fo remouvim."
                   else "Tap to select, tap again to remove."
    val cancelText  = if (isKriol) "Kansol"    else "Cancel"
    val confirmText = if (isKriol) "Aded simptom  →" else "Add symptoms  →"

    ModalBottomSheet(
        onDismissRequest = onDismiss,
        containerColor = SheetBg,
        shape = RoundedCornerShape(topStart = 24.dp, topEnd = 24.dp),
        dragHandle = {
            Box(
                Modifier
                    .padding(top = 12.dp, bottom = 8.dp)
                    .size(width = 40.dp, height = 4.dp)
                    .clip(RoundedCornerShape(2.dp))
                    .background(ChipBorder)
            )
        },
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(start = 24.dp, end = 24.dp, bottom = 32.dp)
        ) {
            // Title
            Text(
                text = "$emoji  $title",
                fontSize = 22.sp,
                fontWeight = FontWeight.Black,
                color = HeadingColor,
            )
            Spacer(Modifier.height(6.dp))

            // Hint
            Text(
                text = hintText,
                fontSize = 13.sp,
                fontWeight = FontWeight.SemiBold,
                color = HintText,
            )
            Spacer(Modifier.height(12.dp))

            HorizontalDivider(color = DividerColor, thickness = 1.dp)
            Spacer(Modifier.height(14.dp))

            // Symptom toggle grid — 2 columns, matches Windows QGridLayout
            LazyVerticalGrid(
                columns = GridCells.Fixed(2),
                horizontalArrangement = Arrangement.spacedBy(10.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp),
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(max = 320.dp),
            ) {
                items(symptoms) { symptom ->
                    SymptomToggleChip(
                        symptom  = symptom,
                        isKriol  = isKriol,
                        selected = symptom.vocab in checked,
                        onToggle = { isSelected ->
                            checked = if (isSelected) checked + symptom.vocab
                                      else checked - symptom.vocab
                        },
                    )
                }
            }

            Spacer(Modifier.height(20.dp))

            // Bottom action row
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                // Cancel
                OutlinedButton(
                    onClick = onDismiss,
                    modifier = Modifier
                        .weight(1f)
                        .height(52.dp),
                    shape = RoundedCornerShape(14.dp),
                    colors = ButtonDefaults.outlinedButtonColors(
                        contentColor = Terracotta,
                    ),
                    border = androidx.compose.foundation.BorderStroke(2.dp, ChipBorder),
                ) {
                    Text(cancelText, fontWeight = FontWeight.Bold, fontSize = 15.sp)
                }

                // Confirm
                Button(
                    onClick = { onConfirm(regionKey, checked.toList()) },
                    modifier = Modifier
                        .weight(2f)
                        .height(52.dp),
                    shape = RoundedCornerShape(14.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Terracotta,
                        contentColor   = Color.White,
                    ),
                ) {
                    Text(confirmText, fontWeight = FontWeight.Black, fontSize = 15.sp)
                }
            }
        }
    }
}

// ── Single symptom toggle button ──────────────────────────────────────────────

@Composable
private fun SymptomToggleChip(
    symptom: BodySymptom,
    isKriol: Boolean,
    selected: Boolean,
    onToggle: (Boolean) -> Unit,
) {
    val bg     = if (selected) Terracotta     else ChipBg
    val text   = if (selected) Color.White    else Color(0xFF5A2A1E)
    val border = if (selected) Terracotta     else ChipBorder
    val bWidth = if (selected) 2.dp           else 1.5.dp

    Box(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(10.dp))
            .background(bg)
            .border(bWidth, border, RoundedCornerShape(10.dp))
            .clickable { onToggle(!selected) }
            .padding(horizontal = 10.dp, vertical = 10.dp),
        contentAlignment = Alignment.CenterStart,
    ) {
        Text(
            text       = symptom.label(isKriol),
            fontSize   = 13.sp,
            fontWeight = if (selected) FontWeight.ExtraBold else FontWeight.SemiBold,
            color      = text,
            lineHeight = 17.sp,
        )
    }
}