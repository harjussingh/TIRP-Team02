package com.example.saca.ui.components

import androidx.compose.material3.ExtendedFloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Call
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.saca.viewmodel.TriageViewModel

@Composable
fun EmergencyCallButton(
    viewModel: TriageViewModel,
    onEmergencyCallConfirmed: () -> Unit,
    modifier: Modifier = Modifier
) {
    var showDialog by remember { mutableStateOf(false) }
    val language by viewModel.language.collectAsState()
    
    val buttonLabel = when (language) {
        com.example.saca.model.Language.ENGLISH -> "Emergency"
        com.example.saca.model.Language.KRIOL -> "Imerjiensi"
    }

    ExtendedFloatingActionButton(
        onClick = { showDialog = true },
        containerColor = Color(0xFFD32F2F), // Emergency red
        contentColor = Color.White,
        modifier = modifier,
        icon = {
            Icon(
                imageVector = Icons.Filled.Call,
                contentDescription = "Emergency Call",
                tint = Color.White
            )
        },
        text = {
            Text(
                text = buttonLabel,
                fontSize = 14.sp,
                fontWeight = FontWeight.Bold,
                color = Color.White
            )
        }
    )

    if (showDialog) {
        EmergencyCallDialog(
            language = language,
            onConfirm = {
                showDialog = false
                onEmergencyCallConfirmed()
            },
            onDismiss = { showDialog = false }
        )
    }
}
