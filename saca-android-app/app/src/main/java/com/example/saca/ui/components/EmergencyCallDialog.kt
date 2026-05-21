package com.example.saca.ui.components

import androidx.compose.material3.AlertDialog
import androidx.compose.material3.TextButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import com.example.saca.model.Language

@Composable
fun EmergencyCallDialog(
    language: Language,
    onConfirm: () -> Unit,
    onDismiss: () -> Unit
) {
    val title = when (language) {
        Language.ENGLISH -> "Emergency Services"
        Language.KRIOL -> "Imerjiensi Serbis"
    }
    
    val message = when (language) {
        Language.ENGLISH -> "Are you sure you want to call emergency services (000)?"
        Language.KRIOL -> "Yu sho yu wahn kaal imerjiensi serbis (000)?"
    }
    
    val cancelLabel = when (language) {
        Language.ENGLISH -> "Cancel"
        Language.KRIOL -> "Kangko"
    }
    
    val callLabel = when (language) {
        Language.ENGLISH -> "Call 000"
        Language.KRIOL -> "Kaal 000"
    }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(title) },
        text = { Text(message) },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text(cancelLabel)
            }
        },
        confirmButton = {
            TextButton(
                onClick = onConfirm,
            ) {
                Text(
                    callLabel,
                    color = Color(0xFFD32F2F) // Emergency red
                )
            }
        }
    )
}
