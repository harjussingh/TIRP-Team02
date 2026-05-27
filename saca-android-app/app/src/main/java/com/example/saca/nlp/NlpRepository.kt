package com.example.saca.nlp

import android.content.Context
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import com.example.saca.nlp.KriolNlpProcessor
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeoutOrNull
import org.json.JSONObject
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL

/**
 * NlpRepository — hybrid NLP processor
 *
 * Online:  POST to Python FastAPI server → full pipeline (BioClinicalBERT etc.)
 * Offline: KriolNlpProcessor.kt         → deterministic Kotlin fallback
 *
 *   Change NLP_SERVER_URL once API available
 */
class NlpRepository(private val context: Context) {

    data class NlpResult(
        val canonicalSymptoms : List<String>,
        val symptomsPresent   : List<String>,
        val symptomsNegated   : List<String>,
        val detectedLanguage  : String,
        val translatedText    : String,
        val usedRemote        : Boolean        // true = API, false = local Kotlin
    )

    // ── SERVER CONFIG ─────────────────────────────────────────────────────
    // TODO: Replace with real URL when  deploys the FastAPI server

    private val NLP_SERVER_URL  = "http://YOUR_SERVER_IP:8000"
    private val ENDPOINT        = "$NLP_SERVER_URL/nlp/process"
    private val HEALTH_ENDPOINT = "$NLP_SERVER_URL/health"
    private val TIMEOUT_MS      = 5_000L   // 5 seconds before falling back
    // ─────────────────────────────────────────────────────────────────────

    private val localProcessor = KriolNlpProcessor(context)

    fun initialise() {
        localProcessor.initialise()
    }

    /**
     * Main entry point — called from TriageViewModel.
     * Automatically picks remote or local based on network + server health.
     */
    suspend fun process(rawText: String, uiLanguage: String = "en"): NlpResult {
        // Try remote first if network is available
        if (isNetworkAvailable()) {
            val remoteResult = tryRemoteNlp(rawText, uiLanguage)
            if (remoteResult != null) {
                android.util.Log.d("NlpRepository", "✅ Used remote NLP API")
                return remoteResult
            }
            android.util.Log.w("NlpRepository", "⚠️ Remote NLP failed — falling back to local")
        } else {
            android.util.Log.d("NlpRepository", "📵 No network — using local NLP")
        }

        // Fallback to local Kotlin processor
        return runLocalNlp(rawText)
    }

    // ── REMOTE: FastAPI call ──────────────────────────────────────────────
    private suspend fun tryRemoteNlp(rawText: String, uiLanguage: String): NlpResult? {
        return withTimeoutOrNull(TIMEOUT_MS) {
            withContext(Dispatchers.IO) {
                try {
                    val url  = URL(ENDPOINT)
                    val conn = url.openConnection() as HttpURLConnection
                    conn.requestMethod  = "POST"
                    conn.setRequestProperty("Content-Type", "application/json")
                    conn.setRequestProperty("Accept", "application/json")
                    conn.doOutput      = true
                    conn.connectTimeout = 3000
                    conn.readTimeout   = 4000

                    // Build request body matching Kavishan's endpoint schema
                    val body = JSONObject().apply {
                        put("text",     rawText)
                        put("language", uiLanguage)
                    }.toString()

                    OutputStreamWriter(conn.outputStream).use { it.write(body) }

                    if (conn.responseCode == HttpURLConnection.HTTP_OK) {
                        val response = conn.inputStream.bufferedReader().readText()
                        parseRemoteResponse(response)
                    } else {
                        android.util.Log.e("NlpRepository", "Server returned ${conn.responseCode}")
                        null
                    }
                } catch (e: Exception) {
                    android.util.Log.e("NlpRepository", "Remote NLP error: ${e.message}")
                    null
                }
            }
        }
    }

    /**
     * Parse the FastAPI response JSON.
     * Expected schema (Kavishan's endpoint):
     * {
     *   "canonical_symptoms": ["fever", "cough"],
     *   "symptoms_present":   ["fever", "cough"],
     *   "symptoms_negated":   [],
     *   "detected_language":  "kriol",
     *   "translated_text":    "i have fever and cough"
     * }
     */
    private fun parseRemoteResponse(json: String): NlpResult? {
        return try {
            val obj = JSONObject(json)

            fun jsonArrayToList(key: String): List<String> {
                val arr = obj.optJSONArray(key) ?: return emptyList()
                return List(arr.length()) { i -> arr.getString(i) }
            }

            // Use canonical_symptoms as primary — falls back to symptoms key
            // Both point to same data per PipelineOutput.as_dict()
            val canonical = jsonArrayToList("canonical_symptoms")
                .ifEmpty { jsonArrayToList("symptoms") }

            NlpResult(
                canonicalSymptoms = canonical,
                symptomsPresent   = jsonArrayToList("symptoms_present"),
                symptomsNegated   = jsonArrayToList("symptoms_negated"),
                detectedLanguage  = obj.optString("detected_language", "en"),
                translatedText    = obj.optString("translated_text_en",
                    obj.optString("translated_text", "")),
                usedRemote        = true
            )
        } catch (e: Exception) {
            android.util.Log.e("NlpRepository", "Parse error: ${e.message}")
            null
        }
    }

    // ── LOCAL: Kotlin fallback ────────────────────────────────────────────
    private fun runLocalNlp(rawText: String): NlpResult {
        val local = localProcessor.process(rawText)
        return NlpResult(
            canonicalSymptoms = local.symptomsPresent,
            symptomsPresent   = local.symptomsPresent,
            symptomsNegated   = local.symptomsNegated,
            detectedLanguage  = local.detectedLanguage,
            translatedText    = local.translatedText,
            usedRemote        = false
        )
    }

    // ── Network check ─────────────────────────────────────────────────────
    private fun isNetworkAvailable(): Boolean {
        val cm = context.getSystemService(Context.CONNECTIVITY_SERVICE)
            as ConnectivityManager
        val network = cm.activeNetwork ?: return false
        val caps    = cm.getNetworkCapabilities(network) ?: return false
        return caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
    }
}