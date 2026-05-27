package com.example.saca.model

enum class Language {
    ENGLISH,
    KRIOL;

    // Returns the correct string for any UI label based on active language
    fun label(): String = when (this) {
        ENGLISH -> "English"
        KRIOL -> "Kriol"
    }
}