package com.example.saca.ui.components

import android.R
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.dp
import com.example.saca.model.Language
import com.example.saca.ui.theme.TextPrimary

@Composable
fun SacaTopBar(
    currentLanguage: Language,
    onLanguageToggle: (Language) -> Unit,
    onBack: (() -> Unit)? = null,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        // Back arrow — only shown when onBack is provided
        if (onBack != null) {
            IconButton(onClick = onBack) {
                Icon(
                    painter = painterResource(id = R.drawable.ic_menu_revert),
                    contentDescription = "Back",
                    tint = TextPrimary
                )
            }
        }

        // App name
        Text(
            text = "SACA",
            style = MaterialTheme.typography.labelLarge,
            modifier = Modifier.weight(1f)
        )

        // EN / Kriol pill toggle
        LanguagePillToggle(
            currentLanguage = currentLanguage,
            onToggle = onLanguageToggle
        )
    }
}

@Composable
fun LanguagePillToggle(
    currentLanguage: Language,
    onToggle: (Language) -> Unit
) {
    Row(
        modifier = Modifier
            .wrapContentWidth(),
        horizontalArrangement = Arrangement.spacedBy(4.dp)
    ) {
        listOf(Language.ENGLISH, Language.KRIOL).forEach { lang ->
            val isSelected = currentLanguage == lang
            val label = if (lang == Language.ENGLISH) "EN" else "Kriol"

            Surface(
                onClick = { onToggle(lang) },
                shape = RoundedCornerShape(50),
                color = if (isSelected) TextPrimary else Color.Transparent,
                modifier = Modifier.height(32.dp)
            ) {
                Box(
                    contentAlignment = Alignment.Center,
                    modifier = Modifier.padding(horizontal = 12.dp)
                ) {
                    Text(
                        text = label,
                        style = MaterialTheme.typography.labelMedium,
                        color = if (isSelected) Color.White else TextPrimary
                    )
                }
            }
        }
    }
}