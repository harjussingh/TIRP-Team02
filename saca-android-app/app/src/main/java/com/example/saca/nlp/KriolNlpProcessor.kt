package com.example.saca.nlp

import android.content.Context
import org.json.JSONObject

class KriolNlpProcessor(private val context: Context) {

    // ── Internal state ────────────────────────────────────────────────────
    private val kriolDict  = mutableMapOf<String, String>()
    private val synonymMap = mutableMapOf<String, String>()
    private var initialised = false

    // ── Result data class ─────────────────────────────────────────────────
    data class NlpResult(
        val originalText    : String,
        val detectedLanguage: String,   // "english" | "kriol" | "mixed"
        val translatedText  : String,
        val symptomsPresent : List<String>,   // canonical: ["fever", "cough"]
        val symptomsNegated : List<String>
    )

    // ── Kriol detection markers ───────────────────────────────────────────
    private val kriolMarkers = setOf(
        "mi", "yu", "em", "wi", "oli", "dei",
        "garr", "garra", "bin", "baimbai", "mas",
        "bat", "en", "o", "mo",
        "no", "nomo", "neva",
        "hed", "beli", "ches", "bek", "han",
        "sik", "hevi", "peyn", "bedsik",
        "kof", "fiba", "fiwa", "fiva"
    )

    // ── Negation words ────────────────────────────────────────────────────
    private val negationWords = setOf(
        "no", "not", "don't", "dont", "didn't", "didnt",
        "never", "without", "no garr", "nomo", "neva",
        "haven't", "havent", "hasn't", "hasnt", "cannot",
        "can't", "cant", "won't", "wont", "isn't", "isnt"
    )

    // ── APP_SYMPTOM_MAP  ─────────────────
    private val appSymptomMap = mapOf(
        "shortness of breath"    to "breathing_problem",
        "trouble breathing"      to "breathing_problem",
        "difficulty breathing"   to "breathing_problem",
        "breathlessness"         to "breathing_problem",
        "hard to breathe"        to "breathing_problem",
        "cannot breathe"         to "breathing_problem",
        "breathing problem"      to "breathing_problem",
        "breathing trouble"      to "breathing_problem",
        "chest pain"             to "chest_pain",
        "chest tightness"        to "chest_pain",
        "heart pain"             to "chest_pain",
        "chest tight"            to "chest_pain",
        "chest sore"             to "chest_pain",
        "sore throat"            to "sore_throat",
        "throat pain"            to "sore_throat",
        "throat sore"            to "sore_throat",
        "abdominal pain"         to "stomach_pain",
        "stomach pain"           to "stomach_pain",
        "belly pain"             to "stomach_pain",
        "stomach ache"           to "stomach_pain",
        "belly ache"             to "stomach_pain",
        "tummy pain"             to "stomach_pain",
        "tummy ache"             to "stomach_pain",
        "stomach hurts"          to "stomach_pain",
        "belly hurts"            to "stomach_pain",
        "stomach cramps"         to "stomach_pain",
        "diarrhoea"              to "diarrhea",
        "diarrhea"               to "diarrhea",
        "loose stools"           to "diarrhea",
        "runny stomach"          to "diarrhea",
        "runny tummy"            to "diarrhea",
        "watery poo"             to "diarrhea",
        "dizziness"              to "dizzy",
        "dizzy"                  to "dizzy",
        "lightheaded"            to "dizzy",
        "light headed"           to "dizzy",
        "head spinning"          to "dizzy",
        "feel dizzy"             to "dizzy",
        "feeling dizzy"          to "dizzy",
        "fatigue"                to "weak",
        "weakness"               to "weak",
        "weak"                   to "weak",
        "tired"                  to "weak",
        "very tired"             to "weak",
        "exhausted"              to "weak",
        "muscle pain"            to "body_pain",
        "joint pain"             to "body_pain",
        "body pain"              to "body_pain",
        "body ache"              to "body_pain",
        "body aches"             to "body_pain",
        "rash"                   to "rash",
        "skin rash"              to "rash",
        "itching"                to "rash",
        "itchy skin"             to "rash",
        "skin problem"           to "rash",
        "fever"                  to "fever",
        "high fever"             to "fever",
        "hot body"               to "fever",
        "body hot"               to "fever",
        "temperature"            to "fever",
        "cough"                  to "cough",
        "headache"               to "headache",
        "head hurts"             to "headache",
        "head pain"              to "headache",
        "sore head"              to "headache",
        "head ache"              to "headache",
        "vomiting"               to "vomiting",
        "vomit"                  to "vomiting",
        "throwing up"            to "vomiting",
        "throw up"               to "vomiting",
        "nausea"                 to "nausea",
        "nauseous"               to "nausea",
        "feel sick"              to "nausea",
        "feeling sick"           to "nausea",
        "want to vomit"          to "nausea",
        "upset stomach"          to "nausea",
        "bleeding"               to "bleeding",
        "blood"                  to "bleeding",
        "bleed"                  to "bleeding",
        "swelling"               to "swelling",
        "swollen"                to "swelling",
        "pain"                   to "pain"
    )

    // ── Initialise — call once at app start ───────────────────────────────
    fun initialise() {
        if (initialised) return
        loadKriolDictionary()
        loadSynonyms()
        initialised = true
        android.util.Log.d("NLP", "KriolNlpProcessor ready. " +
            "Dict: ${kriolDict.size} entries, Synonyms: ${synonymMap.size} entries")
    }

    // ── Main entry point ──────────────────────────────────────────────────
    fun process(rawText: String): NlpResult {
        if (!initialised) initialise()

        val cleaned    = rawText.lowercase().trim()
        val lang       = detectLanguage(cleaned)
        val translated = if (lang != "english") translateKriol(cleaned) else cleaned
        val normalised = normaliseSynonyms(translated)
        val (present, negated) = extractAndDetectNegation(normalised)

        android.util.Log.d("NLP", "Input: '$rawText'")
        android.util.Log.d("NLP", "Lang: $lang | Translated: '$translated'")
        android.util.Log.d("NLP", "Present: $present | Negated: $negated")

        return NlpResult(
            originalText     = rawText,
            detectedLanguage = lang,
            translatedText   = translated,
            symptomsPresent  = present,
            symptomsNegated  = negated
        )
    }

    private fun detectLanguage(text: String): String {
        val words      = text.split(Regex("\\s+"))
        val kriolCount = words.count { it in kriolMarkers }
        val ratio      = kriolCount.toFloat() / words.size.coerceAtLeast(1)
        return when {
            ratio >= 0.3 -> "kriol"
            ratio >= 0.1 -> "mixed"
            else         -> "english"
        }
    }

    private fun translateKriol(text: String): String {
        val words = text.split(Regex("\\s+"))
        val translated = words.map { word ->
            val stripped = word.trimEnd(',', '.', '!', '?', ';', ':')
            val suffix   = word.removePrefix(stripped)
            val english  = kriolDict[stripped] ?: stripped
            english + suffix
        }
        var result = translated.joinToString(" ")
        result = result.replace(Regex("\\bi not have\\b"), "i do not have")
        result = result.replace(Regex("\\bmi have\\b"), "i have")
        return result
    }

    // ── Step 3: Synonym normalisation ────────────────────────────────────
    private fun normaliseSynonyms(text: String): String {
        var result = text
        // Longest phrase first — prevents partial matches
        val sorted = synonymMap.keys.sortedByDescending { it.length }
        for (phrase in sorted) {
            if (result.contains(phrase)) {
                result = result.replace(phrase, synonymMap[phrase] ?: phrase)
            }
        }
        return result
    }

    // ── Step 4 + 5: Symptom extraction + negation detection ──────────────
    private fun extractAndDetectNegation(text: String): Pair<List<String>, List<String>> {
        val present = mutableSetOf<String>()
        val negated = mutableSetOf<String>()

        val sentences = text.split(Regex("[.!?]|\\bbut\\b|\\bhowever\\b"))

        for (sentence in sentences) {
            val trimmed   = sentence.trim()
            val hasNeg    = negationWords.any { neg ->
                trimmed.contains("\\b$neg\\b".toRegex())
            }
            val matched   = mutableSetOf<String>()

            // Longest phrase first to prevent partial matches
            val sorted = appSymptomMap.keys.sortedByDescending { it.length }
            for (phrase in sorted) {
                if (trimmed.contains(phrase)) {
                    matched.add(appSymptomMap[phrase]!!)
                }
            }

            for (sym in matched) {
                if (hasNeg) negated.add(sym) else present.add(sym)
            }
        }

        present.removeAll(negated)
        return Pair(present.toList(), negated.toList())
    }

    // ── Load kriol_dictionary.json ────────────────────────────────────────
    // Nested format: { "category": { "kriol_word": "english_word" } }
    // Flattened into one lookup map at load time
    private fun loadKriolDictionary() {
        try {
            val json = context.assets
                .open("nlp/kriol_dictionary.json")
                .bufferedReader()
                .use { it.readText() }

            val root = JSONObject(json)
            val categoryKeys = root.keys()

            while (categoryKeys.hasNext()) {
                val category = categoryKeys.next()
                if (category == "comment") continue   // skip metadata entry

                val section  = root.optJSONObject(category) ?: continue
                val wordKeys = section.keys()

                while (wordKeys.hasNext()) {
                    val kriol   = wordKeys.next().lowercase().trim()
                    val english = section.optString(kriol, kriol).lowercase().trim()
                    kriolDict[kriol] = english
                }
            }
            android.util.Log.d("NLP", "Kriol dict loaded: ${kriolDict.size} entries")

        } catch (e: Exception) {
            android.util.Log.e("NLP", "Failed to load kriol_dictionary.json: ${e.message}")
        }
    }

    // ── Load synonyms.json ────────────────────────────────────────────────
    // Flat format: { "phrase": "canonical_english" }
    // Section dividers like "____FEVER____": "---" are skipped
    private fun loadSynonyms() {
        try {
            val json = context.assets
                .open("nlp/synonyms.json")
                .bufferedReader()
                .use { it.readText() }

            val root = JSONObject(json)
            val keys = root.keys()

            while (keys.hasNext()) {
                val phrase    = keys.next().lowercase().trim()
                val canonical = root.optString(phrase, "").lowercase().trim()

                // Skip empty values and section dividers
                if (canonical.isNotEmpty() && canonical != "---") {
                    synonymMap[phrase] = canonical
                }
            }
            android.util.Log.d("NLP", "Synonyms loaded: ${synonymMap.size} entries")

        } catch (e: Exception) {
            android.util.Log.e("NLP", "Failed to load synonyms.json: ${e.message}")
        }
    }
}