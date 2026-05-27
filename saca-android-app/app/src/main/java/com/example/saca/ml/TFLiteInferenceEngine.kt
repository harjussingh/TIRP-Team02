package com.example.saca.ml

import android.content.Context
import com.google.android.gms.tflite.client.TfLiteInitializationOptions
import com.google.android.gms.tflite.java.TfLite
import org.tensorflow.lite.InterpreterApi
import org.tensorflow.lite.InterpreterApi.Options.TfLiteRuntime
import java.io.FileInputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.MappedByteBuffer
import java.nio.channels.FileChannel
import com.example.saca.model.ModelInferenceResult
import com.example.saca.model.Severity

class TFLiteInferenceEngine(private val context: Context) {

    private var interpreter  : InterpreterApi?  = null
    private var vocab        : List<String>     = emptyList()
    private var vocabToIndex : Map<String, Int> = emptyMap()
    private var isReady      : Boolean          = false
    private var modelInputSize: Int             = 0

    // output_order from model_meta.json:
    // [0]=confidence, [1]=needs_follow_up, [2]=severity, [3]=suggested_symptoms
    // Corrected output indices — based on actual tensor inspection
    private val OUTPUT_DISEASE_IDX  = 0   // INT32 scalar — predicted disease index
    private val OUTPUT_SUGGESTIONS  = 1   // INT32 array  — top 5 suggested symptom indices
    private val OUTPUT_CONFIDENCE   = 2   // FLOAT32 scalar — confidence score
    private val OUTPUT_SEVERITY     = 3

    // ── Initialise ────────────────────────────────────────────────────────
    fun initialise() {
        vocab        = loadVocab()
        vocabToIndex = vocab.mapIndexed { idx, sym -> sym to idx }.toMap()
        android.util.Log.d("TFLite", "Vocab loaded: ${vocab.size} entries")
        android.util.Log.d("TFLite", "Vocab[0]=${vocab.getOrNull(0)}")

        TfLite.initialize(
            context,
            TfLiteInitializationOptions.builder()
                .setEnableGpuDelegateSupport(false)
                .build()
        ).addOnSuccessListener {
            val options = InterpreterApi.Options()
                .setRuntime(TfLiteRuntime.FROM_SYSTEM_ONLY)
            interpreter = InterpreterApi.create(loadModelFile(), options)

            val interp = interpreter!!
            interp.allocateTensors()

            modelInputSize = interp.getInputTensor(0).shape()[1]

            // Log all output tensors — mirrors Windows output_details inspection
            val numOutputs = interp.outputTensorCount
            android.util.Log.d("TFLite", "Input shape:  ${interp.getInputTensor(0).shape().contentToString()}")
            android.util.Log.d("TFLite", "Output count: $numOutputs")
            for (i in 0 until interp.outputTensorCount) {
                android.util.Log.d("TFLite",
                    "Output[$i] shape=${interp.getOutputTensor(i).shape().contentToString()} " +
                            "dtype=${interp.getOutputTensor(i).dataType()} " +
                            "name=${interp.getOutputTensor(i).name()}"
                )
            }
            android.util.Log.d("TFLite", "modelInputSize=$modelInputSize | vocab.size=${vocab.size}")

            isReady = true
        }.addOnFailureListener { e ->
            android.util.Log.e("TFLite", "LiteRT init failed: ${e.message}")
            isReady = false
        }
    }

    // ── Main inference call ───────────────────────────────────────────────
    fun runInference(symptoms: List<String>): ModelInferenceResult {

        if (!isReady || interpreter == null) {
            android.util.Log.w("TFLite", "Model not ready — returning stub")
            return stub()
        }

        if (modelInputSize == 0) {
            android.util.Log.e("TFLite", "modelInputSize is 0 — returning stub")
            return stub()
        }

        if (symptoms.isEmpty()) {
            android.util.Log.w("TFLite", "No symptoms — returning stub")
            return stub()
        }

        // Step 1 — Normalise symptoms — mirrors Python normalise_symptom()
        val normalisedSymptoms = symptoms
            .map { normaliseSymptom(it) }
            .filter { it.isNotEmpty() && it.lowercase() != "none" }
            .toSet()

        android.util.Log.d("TFLite", "Raw symptoms:        $symptoms")
        android.util.Log.d("TFLite", "Normalised symptoms: $normalisedSymptoms")

        // Step 2 — Build ByteBuffer input — mirrors Python make_vector()
        // np.zeros((1, input_size), dtype=np.float32)
        // ByteBuffer bypasses INT32/FLOAT32 Java type conflict
        val inputBuffer = ByteBuffer
            .allocateDirect(modelInputSize * 4)
            .order(ByteOrder.nativeOrder())

        var anyMapped = false
        for (i in 0 until modelInputSize) {
            val sym = vocab.getOrNull(i)
            if (sym != null && sym in normalisedSymptoms) {
                inputBuffer.putFloat(1f)
                anyMapped = true
                android.util.Log.d("TFLite", "Mapped '$sym' → index $i")
            } else {
                inputBuffer.putFloat(0f)
            }
        }

        if (!anyMapped) {
            inputBuffer.rewind()
            inputBuffer.putFloat(1f)  // set None at index 0 — same as Python
            android.util.Log.w("TFLite", "Nothing mapped — setting None at index 0")
        }
        inputBuffer.rewind()

        // Step 3 — Build output map for all tensors
        // Mirrors Python: outputs = [interpreter.get_tensor(d["index"]) for d in output_details]
        val numOutputs = interpreter!!.outputTensorCount
        val outputMap  = mutableMapOf<Int, Any>()

        for (i in 0 until numOutputs) {
            val tensor   = interpreter!!.getOutputTensor(i)
            val shape    = tensor.shape()
            val size     = if (shape.size >= 2) shape[1] else shape[0]
            val dtype    = tensor.dataType()
            android.util.Log.d("TFLite", "Output[$i] size=$size dtype=$dtype")

            // Allocate correct array type based on tensor dtype
            outputMap[i] = if (dtype.toString().contains("INT32")) {
                Array(1) { IntArray(size) }
            } else {
                Array(1) { FloatArray(size) }
            }
        }

        // Step 4 — Run inference with all outputs
        try {
            interpreter!!.runForMultipleInputsOutputs(arrayOf(inputBuffer), outputMap)
        } catch (e: Exception) {
            android.util.Log.e("TFLite", "Inference failed: ${e.message}")
            return stub()
        }

        // Step 5 — Parse outputs
        // Helper reads either IntArray or FloatArray — handles INT32/FLOAT32 model outputs
        fun getOutputFloats(idx: Int): FloatArray {
            val raw = (outputMap[idx] as? Array<*>)?.get(0)
            return when (raw) {
                is FloatArray -> raw
                is IntArray   -> raw.map { it.toFloat() }.toFloatArray()
                else          -> FloatArray(0)
            }
        }

        val confidenceArr  = getOutputFloats(OUTPUT_CONFIDENCE)   // index 2
        val severityArr    = getOutputFloats(OUTPUT_SEVERITY)     // index 3
        val suggestionsRaw = getOutputFloats(OUTPUT_SUGGESTIONS)  // index 1

        android.util.Log.d("TFLite", "confidence output:  ${confidenceArr.toList()}")
        android.util.Log.d("TFLite", "severity output:    ${severityArr.toList()}")
        android.util.Log.d("TFLite", "suggestions output: ${suggestionsRaw.toList()}")

        // Confidence from tensor 2
        val confidence = confidenceArr.getOrElse(0) { 0.55f }

// Severity from tensor 3 — 3 class scores [MILD, MODERATE, NEEDS_REST]
        val severityOrder = listOf("MILD", "MODERATE", "NEEDS_REST")
        val severityIdx   = when {
            severityArr.size == 1 ->
                severityArr[0].toInt().coerceIn(0, severityOrder.size - 1)
            severityArr.size > 1  ->
                severityArr.indices.maxByOrNull { severityArr[it] } ?: 0
            else -> 0
        }
        val severityStr = severityOrder.getOrElse(severityIdx) { "MILD" }
        val severity    = when (severityStr) {
            "MODERATE"   -> Severity.MEDIUM
            "NEEDS_REST" -> Severity.HIGH
            else         -> Severity.LOW
        }

// NeedsFollowUp — base on confidence < 0.7 or severity != LOW
        val needsFollowUp = confidence < 0.7f || severity != Severity.LOW

// Suggestions — tensor 1 contains top 5 vocab indices as INT32
        val suggestions = suggestionsRaw
            .map { it.toInt() }
            .filter { it > 0 && it < vocab.size }
            .mapNotNull { idx ->
                val sym = vocab.getOrNull(idx)
                if (sym != null && sym.lowercase() != "none" && sym !in normalisedSymptoms)
                    sym else null
            }
            .take(4)

        android.util.Log.d("TFLite", "Confidence:    $confidence")
        android.util.Log.d("TFLite", "SeverityIdx:   $severityIdx → $severityStr")
        android.util.Log.d("TFLite", "Severity:      $severity")
        android.util.Log.d("TFLite", "NeedsFollowUp: $needsFollowUp")
        android.util.Log.d("TFLite", "Suggestions:   $suggestions")

        return ModelInferenceResult(
            severity          = severity,
            confidence        = confidence,
            needsFollowUp     = needsFollowUp,
            suggestedSymptoms = suggestions
        )
    }

    // ── Stub ──────────────────────────────────────────────────────────────
    private fun stub() = ModelInferenceResult(
        severity          = Severity.LOW,
        confidence        = 0f,
        needsFollowUp     = false,
        suggestedSymptoms = emptyList()
    )

    // ── Symptom normalisation — mirrors Python normalise_symptom() ────────
    private fun normaliseSymptom(symptom: String): String {
        val key = symptom.lowercase().trim()
            .replace("-", " ")
            .replace("_", " ")
            .replace(Regex("\\s+"), " ")

        commonSymptomMap[key]?.let { return it }

        val underscore = key.replace(" ", "_")
        if (underscore in vocabToIndex) return underscore
        if (key in vocabToIndex) return key

        android.util.Log.w("TFLite", "Could not normalise: '$symptom'")
        return ""
    }

    // ── Release ───────────────────────────────────────────────────────────
    fun close() {
        interpreter?.close()
        interpreter = null
        isReady     = false
    }

    // ── Load model.tflite ─────────────────────────────────────────────────
    private fun loadModelFile(): MappedByteBuffer {
        val fd = context.assets.openFd("model.tflite")
        return FileInputStream(fd.fileDescriptor).channel.map(
            FileChannel.MapMode.READ_ONLY,
            fd.startOffset,
            fd.declaredLength
        )
    }

    // ── Load symptom_vocab.json ───────────────────────────────────────────
    // .drop(4) removed — was breaking index alignment
    // Index 0 must be "None" — same as Python vocab_first_token
    private fun loadVocab(): List<String> {
        return try {
            val jsonString = context.assets
                .open("symptom_vocab.json")
                .bufferedReader()
                .use { it.readText() }

            val parsed = org.json.JSONTokener(jsonString).nextValue()
            val jsonArray = when (parsed) {
                is org.json.JSONArray  -> parsed
                is org.json.JSONObject -> parsed.optJSONArray("symptom_ids")
                    ?: parsed.optJSONArray("symptoms")
                    ?: org.json.JSONArray()
                else -> org.json.JSONArray()
            }

            List(jsonArray.length()) { i -> jsonArray.optString(i) }
                .also { list ->
                    android.util.Log.d("TFLite", "Vocab[0]=${list.getOrNull(0)}")
                    android.util.Log.d("TFLite", "Total: ${list.size}")
                }
        } catch (e: Exception) {
            android.util.Log.e("TFLite", "Failed to parse vocab: ${e.message}")
            emptyList()
        }
    }

    // ── COMMON_SYMPTOM_MAP — exact copy from ml_tflite_service.py ────────
    private val commonSymptomMap = mapOf(
        "none"                        to "None",
        "nil"                         to "None",
        "no symptom"                  to "None",
        "headache"                    to "headache",
        "head ache"                   to "headache",
        "head pain"                   to "headache",
        "hedake"                      to "headache",
        "hedache"                     to "headache",
        "mild headache"               to "mild_headache",
        "bad headache"                to "severe_headache",
        "big headache"                to "severe_headache",
        "severe headache"             to "severe_headache",
        "sudden headache"             to "sudden_severe_headache",
        "fever"                       to "fever",
        "fiba"                        to "fever",
        "fiwa"                        to "fever",
        "fiva"                        to "fever",
        "body hot"                    to "fever",
        "hot body"                    to "fever",
        "hot-bodi"                    to "fever",
        "hotbodi"                     to "fever",
        "mild fever"                  to "mild_fever",
        "high fever"                  to "high_fever",
        "cough"                       to "cough",
        "kof"                         to "cough",
        "koff"                        to "cough",
        "mild cough"                  to "mild_cough",
        "productive cough"            to "productive_cough",
        "runny nose"                  to "runny_nose",
        "blocked nose"                to "nasal_congestion",
        "congestion"                  to "congestion",
        "breathing_problem"           to "difficulty_breathing",
        "breathing problem"           to "difficulty_breathing",
        "breathing trouble"           to "difficulty_breathing",
        "trouble breathing"           to "difficulty_breathing",
        "hard to breathe"             to "difficulty_breathing",
        "difficulty breathing"        to "difficulty_breathing",
        "brithin trabul"              to "difficulty_breathing",
        "cannot breathe"              to "severe_difficulty_breathing",
        "can't breathe"               to "severe_difficulty_breathing",
        "not breathing"               to "not_breathing",
        "shortness of breath"         to "shortness_of_breath",
        "short breath"                to "shortness_of_breath",
        "shortness_of_breath"         to "shortness_of_breath",
        "severe shortness of breath"  to "severe_shortness_of_breath",
        "severe difficulty breathing" to "severe_difficulty_breathing",
        "wheezing"                    to "wheezing",
        "chest pain"                  to "chest_pain",
        "chest_pain"                  to "chest_pain",
        "chest tightness"             to "chest_pain",
        "heart pain"                  to "chest_pain",
        "heartache"                   to "chest_pain",
        "heart hurts"                 to "chest_pain",
        "heart attack"                to "chest_pain",
        "chest hurts"                 to "chest_pain",
        "sore throat"                 to "sore_throat",
        "throat pain"                 to "sore_throat",
        "stomach pain"                to "stomach_pain",
        "stomach_pain"                to "stomach_pain",
        "abdominal pain"              to "stomach_pain",
        "belly pain"                  to "stomach_pain",
        "belly hurts"                 to "stomach_pain",
        "tummy pain"                  to "stomach_pain",
        "stomach ache"                to "stomach_pain",
        "diarrhoea"                   to "diarrhea",
        "diarrhea"                    to "diarrhea",
        "loose stools"                to "diarrhea",
        "runny stomach"               to "diarrhea",
        "dizziness"                   to "dizziness",
        "dizzy"                       to "dizziness",
        "lightheaded"                 to "dizziness",
        "fatigue"                     to "fatigue",
        "weakness"                    to "weakness",
        "weak"                        to "weakness",
        "tired"                       to "fatigue",
        "very tired"                  to "fatigue",
        "exhausted"                   to "fatigue",
        "muscle pain"                 to "muscle_pain",
        "joint pain"                  to "joint_pain",
        "body pain"                   to "body_aches",
        "body ache"                   to "body_aches",
        "body aches"                  to "body_aches",
        "rash"                        to "rash",
        "skin rash"                   to "rash",
        "itching"                     to "itching",
        "itchy skin"                  to "itching",
        "skin problem"                to "rash",
        "vomiting"                    to "vomiting",
        "vomit"                       to "vomiting",
        "throwing up"                 to "vomiting",
        "nausea"                      to "nausea",
        "feel sick"                   to "nausea",
        "feeling sick"                to "nausea",
        "bleeding"                    to "bleeding",
        "blood"                       to "bleeding",
        "swelling"                    to "swelling",
        "swollen"                     to "swollen",
        "pain"                        to "pain"
    )
}