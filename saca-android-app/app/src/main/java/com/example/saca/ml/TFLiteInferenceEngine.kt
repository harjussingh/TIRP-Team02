package com.example.saca.ml

import android.content.Context
import com.google.android.gms.tflite.client.TfLiteInitializationOptions
import com.google.android.gms.tflite.java.TfLite
import org.tensorflow.lite.InterpreterApi
import org.tensorflow.lite.InterpreterApi.Options.TfLiteRuntime
import java.io.FileInputStream
import java.nio.MappedByteBuffer
import java.nio.channels.FileChannel
import com.example.saca.model.ModelInferenceResult
import com.example.saca.model.Severity

class TFLiteInferenceEngine(private val context: Context) {

    private var interpreter: InterpreterApi? = null
    private var vocab: List<String> = emptyList()
    private var isReady = false

    // Call once at app start — loads model + vocab into memory
    fun initialise() {
        // Load vocab immediately — no async needed
        vocab = loadVocab()

        // TfLite.initialize is async — block until complete using .get()
        TfLite.initialize(
            context,
            TfLiteInitializationOptions.builder()
                .setEnableGpuDelegateSupport(false) // keep simple for now
                .build()
        ).addOnSuccessListener {
            // Only create interpreter AFTER successful init
            val options = InterpreterApi.Options()
                .setRuntime(TfLiteRuntime.FROM_SYSTEM_ONLY)
            interpreter = InterpreterApi.create(loadModelFile(), options)
            isReady = true
        }.addOnFailureListener { e ->
            android.util.Log.e("TFLite", "LiteRT init failed: ${e.message}")
            isReady = false
        }
    }

    // Main inference call — takes symptom text, returns structured result
    fun runInference(symptomText: String): ModelInferenceResult {
        // Return stub if model not ready yet
        if (!isReady || interpreter == null) {
            return ModelInferenceResult(
                severity = Severity.LOW,
                confidence = 0f,
                needsFollowUp = false,
                suggestedSymptoms = emptyList()
            )
        }

        // Build input vector from vocab
        val inputVector = FloatArray(vocab.size) { index ->
            if (symptomText.lowercase().contains(
                    vocab.getOrNull(index)?.lowercase() ?: ""
                )) 1f else 0f
        }
        val inputs = arrayOf(inputVector)

        // --- Prepare output buffers (matches contract exactly) ---
            // Inspect model outputs via reflection to allocate exact buffers
            val outputMap = mutableMapOf<Int, Any>()
            var detectedShapes: List<IntArray>? = null
            try {
                val interpCls = interpreter!!.javaClass
                val getOutputCount = interpCls.methods.firstOrNull { it.name == "getOutputTensorCount" }
                val count = getOutputCount?.invoke(interpreter) as? Int
                val getOutputTensor = interpCls.methods.firstOrNull { it.name == "getOutputTensor" && it.parameterTypes.size == 1 }
                if (count != null && getOutputTensor != null) {
                    val shapes = mutableListOf<IntArray>()
                    for (i in 0 until count) {
                        val tensorObj = getOutputTensor.invoke(interpreter, i)
                        // try shape(), then shapeSignature()
                        val shapeMethod = tensorObj.javaClass.methods.firstOrNull { it.name == "shape" && it.parameterCount == 0 }
                        val shapeSigMethod = tensorObj.javaClass.methods.firstOrNull { it.name == "shapeSignature" && it.parameterCount == 0 }
                        val shape = when {
                            shapeMethod != null -> shapeMethod.invoke(tensorObj) as? IntArray
                            shapeSigMethod != null -> shapeSigMethod.invoke(tensorObj) as? IntArray
                            else -> null
                        }
                        if (shape == null) throw IllegalStateException("Cannot determine tensor shape for output $i")
                        shapes.add(shape)

                        // determine data type (try dataType().name())
                        val dataTypeMethod = tensorObj.javaClass.methods.firstOrNull { it.name == "dataType" && it.parameterCount == 0 }
                        val dtName = dataTypeMethod?.invoke(tensorObj)?.let { dt ->
                            dt.javaClass.methods.firstOrNull { it.name == "name" && it.parameterCount == 0 }?.invoke(dt) as? String
                        }

                        val inner = if (shape.size >= 2) shape[1] else shape[0]
                        if (dtName == "INT32") {
                            outputMap[i] = Array(1) { IntArray(inner) }
                        } else {
                            outputMap[i] = Array(1) { FloatArray(inner) }
                        }
                    }
                    detectedShapes = shapes
                }
            } catch (e: Exception) {
                android.util.Log.w("TFLite", "Reflection of output tensors failed: ${e.message}")
            }

            // Fallback: if reflection failed, allocate reasonable defaults
            if (outputMap.isEmpty()) {
                val maxVocab = maxOf(1, vocab.size)
                outputMap[0] = Array(1) { FloatArray(maxVocab) }
                outputMap[1] = Array(1) { FloatArray(3) }
                outputMap[2] = Array(1) { FloatArray(1) }
                outputMap[3] = Array(1) { FloatArray(1) }
            }

            interpreter!!.runForMultipleInputsOutputs(inputs, outputMap)

            // Extract outputs into a uniform structure for mapping
            val outputs = outputMap.keys.sorted().map { key ->
                val obj = outputMap[key]
                when (obj) {
                    is Array<*> -> {
                        val inner = obj.getOrNull(0)
                        when (inner) {
                            is FloatArray -> inner
                            is IntArray -> inner.map { it.toFloat() }.toFloatArray()
                            else -> FloatArray(0)
                        }
                    }
                    else -> FloatArray(0)
                }
            }

            // Map outputs by length
            val suggestionScores = outputs.firstOrNull { it.size == vocab.size }
                ?: outputs.maxByOrNull { it.size }

            val severityArr = outputs.firstOrNull { it.size == 3 } ?: FloatArray(3) { 0f }

            val scalarOutputs = outputs.filter { it.size == 1 }
            val confidenceVal = scalarOutputs.getOrNull(0)?.getOrNull(0) ?: 0f
            val followUpScore = when {
                scalarOutputs.size >= 2 -> scalarOutputs[1].getOrNull(0) ?: 0f
                scalarOutputs.size == 1 -> scalarOutputs[0].getOrNull(0) ?: 0f
                else -> 0f
            }

            val severityIndex = severityArr.indices.maxByOrNull { severityArr[it] } ?: 0
            val followUpNeeded = followUpScore >= 0.5f

            val suggestions = suggestionScores
                ?.mapIndexed { idx, score -> idx to score }
                ?.sortedByDescending { it.second }
                ?.take(5)
                ?.map { it.first }
                ?.filter { it != 0 }
                ?.mapNotNull { vocab.getOrNull(it) }
                ?: emptyList()

        return ModelInferenceResult(
            severity          = Severity.fromModelIndex(severityIndex),
            confidence        = confidenceVal,
            needsFollowUp     = followUpNeeded,
            suggestedSymptoms = if (followUpNeeded) suggestions else emptyList()
        )
    }

    // Release TFLite resources when done
    fun close() {
        interpreter?.close()
        interpreter = null
        isReady = false
    }

    // Load .tflite file from assets into a MappedByteBuffer
    private fun loadModelFile(): MappedByteBuffer {
        val fileDescriptor = context.assets.openFd("model.tflite")
        val inputStream = FileInputStream(fileDescriptor.fileDescriptor)
        return inputStream.channel.map(
            FileChannel.MapMode.READ_ONLY,
            fileDescriptor.startOffset,
            fileDescriptor.declaredLength
        )
    }

    // Load vocab JSON from assets
    private fun loadVocab(): List<String> {
        val jsonString = context.assets
            .open("symptom_vocab.json")
            .bufferedReader()
            .use { it.readText() }

        try {
            val parsed = org.json.JSONTokener(jsonString).nextValue()
            val jsonArray = when (parsed) {
                is org.json.JSONArray -> parsed
                is org.json.JSONObject -> {
                    // Some vocab files wrap the array in an object under `symptom_ids`
                    parsed.optJSONArray("symptom_ids") ?: parsed.optJSONArray("symptoms") ?: org.json.JSONArray()
                }
                else -> org.json.JSONArray()
            }
            return List(jsonArray.length()) { i -> jsonArray.optString(i) }
        } catch (e: Exception) {
            android.util.Log.e("TFLite", "Failed to parse vocab JSON: ${e.message}")
            return emptyList()
        }
    }
}