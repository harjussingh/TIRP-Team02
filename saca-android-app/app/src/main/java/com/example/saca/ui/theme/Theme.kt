package com.example.saca.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val SacaColorScheme = lightColorScheme(
    background = WarmClay,
    surface = LightSand,
    primary = PrimaryBlue,
    onPrimary = Color.White,
    onBackground = TextPrimary,
    onSurface = TextPrimary,
    secondary = OchreAccent,
    onSecondary = Color.White,
    error = SeverityCritical,
    onError = Color.White,
)

@Composable
fun SacaTheme(
    content: @Composable () -> Unit
) {
    MaterialTheme(
        colorScheme = SacaColorScheme,
        typography = SacaTypography,
        content = content
    )
}