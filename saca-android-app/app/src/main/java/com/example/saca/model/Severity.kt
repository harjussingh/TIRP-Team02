package com.example.saca.model

enum class Severity {
    LOW,
    MEDIUM,
    HIGH,
    CRITICAL;

    val displayName: String
        get() = when (this) {
            LOW -> "Low"
            MEDIUM -> "Medium"
            HIGH -> "High"
            CRITICAL -> "Critical"
        }

    companion object {
        // Maps TFLite model's 3-class output to our 4-level UI scale
        // CRITICAL is reserved — set by override rules, not the model directly
        fun fromModelIndex(index: Int): Severity = when (index) {
            0 -> LOW        // MILD
            1 -> MEDIUM     // MODERATE
            2 -> HIGH       // NEEDS_REST
            else -> LOW
        }
    }
}