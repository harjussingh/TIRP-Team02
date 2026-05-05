package com.example.saca.model

data class Symptom(
    val id: String,
    val labelEN: String,
    val labelKR: String,
    val icon: String           // emoji placeholder — todo: swap for R.drawable.* later
)

// Master symptom list
val ALL_SYMPTOMS = listOf(
    Symptom("cough", "Cough", "Kof", "🤧"),
    Symptom("fever", "Hot / fever", "Hot / fiva", "🌡️"),
    Symptom("head", "Head hurts", "Hed haat", "🤕"),
    Symptom("chest", "Chest hurts", "Ches haat", "💢"),
    Symptom("belly", "Belly hurts", "Beli haat", "😣"),
    Symptom("breathe", "Hard to breathe", "Had fo brith", "😮‍💨"),
    Symptom("tired", "Very tired", "Tumach taiad", "😴"),
    Symptom("skin", "Skin problem", "Skin problem", "🩹"),
)