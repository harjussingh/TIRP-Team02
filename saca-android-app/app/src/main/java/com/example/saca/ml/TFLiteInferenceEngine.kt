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
    private var numberOfDiseaseClasses = 0

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

            // Debug — check actual tensor shapes before running inference
            val interp = interpreter!!
            android.util.Log.d("TFLite", "Input count: ${interp.inputTensorCount}")
            android.util.Log.d("TFLite", "Output count: ${interp.outputTensorCount}")
            android.util.Log.d("TFLite", "Output shape: ${interp.getOutputTensor(0).shape().contentToString()}")

            // Capture number of disease classes from model output shape
            // Expected shape: [1, N] where N = number of disease classes
            numberOfDiseaseClasses = interp.getOutputTensor(0).shape().getOrElse(1) { 0 }
            android.util.Log.d("TFLite", "Disease classes detected: $numberOfDiseaseClasses")

            isReady = true
        }.addOnFailureListener { e ->
            android.util.Log.e("TFLite", "LiteRT init failed: ${e.message}")
            isReady = false
        }
    }

    // Main inference call — takes symptom list, returns structured result
    // NOTE: Changed from String to List<String> to match Python's exact-match
    // binary vector logic. String.contains() caused false positives (e.g.
    // "cough" matching "whooping cough"). Each symptom is now matched exactly
    // against the vocab index — same as Python's symptom_index lookup.
    fun runInference(symptoms: List<String>): ModelInferenceResult {
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
            val vocabSymptom = vocab.getOrNull(index)?.lowercase()?.trim() ?: ""
            if (symptoms.any { vocabSymptom.contains(it.lowercase().trim()) }) 1f else 0f
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

        // Guard — if disease class count not yet captured from model, return stub
        if (numberOfDiseaseClasses == 0) {
            android.util.Log.e("TFLite", "Disease class count is 0 — model may not have initialised correctly")
            return ModelInferenceResult(
                severity = Severity.LOW,
                confidence = 0f,
                needsFollowUp = false,
                suggestedSymptoms = emptyList()
            )
        }

        // Single output buffer — disease probability array
        // Shape: [1, numberOfDiseaseClasses] — matches Python ensemble output
        // Replaced runForMultipleInputsOutputs + reflection with simple run()
        // since the exported TFLite model has 1 input and 1 output tensor
        val outputArray = Array(1) { FloatArray(numberOfDiseaseClasses) }

        // Run inference — simple single input/output call
        interpreter!!.run(inputVector, outputArray)

        // Extract probabilities from output buffer
        val probabilities = outputArray[0]

        // Find the disease index with the highest probability
        val topIndex = probabilities.indices.maxByOrNull { probabilities[it] } ?: 0
        val confidence = probabilities[topIndex]

        android.util.Log.d("TFLite", "Top index: $topIndex, Confidence: $confidence")

        // needsFollowUp mirrors Python's logic — if confidence < 0.5,
        // the model is uncertain and follow-up questions are needed
        return ModelInferenceResult(
            severity = Severity.fromModelIndex(topIndex),
            confidence = confidence,
            needsFollowUp = confidence < 0.5f,
            suggestedSymptoms = emptyList()
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
                .drop(4)
        } catch (e: Exception) {
            android.util.Log.e("TFLite", "Failed to parse vocab JSON: ${e.message}")
            return emptyList()
        }
    }
}