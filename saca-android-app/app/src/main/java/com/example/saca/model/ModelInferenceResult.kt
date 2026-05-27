package com.example.saca.model

data class ModelInferenceResult(
    val severity: Severity,
    val confidence: Float,          // 0–1 raw reliability
    val needsFollowUp: Boolean,     // true if >= 0.5
    val suggestedSymptoms: List<String>  // vocab labels, NONE filtered out
)