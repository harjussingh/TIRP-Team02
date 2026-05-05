# Model Output Contract
## Inference API — Output Specification
v1.0 · Requires: symptom_vocab.json

---

## Pipeline Overview

  ML Model (TensorFlow) → TensorFlow Lite (.tflite) → Kotlin (Android)

---

## Outputs

### → confidence
- **Shape:** [1, 1] float32
- **Meaning:** How reliable / complete the current input is.
- **Usage:** Use to gate UI trust indicators. No threshold required — pass raw value to UI.

---

### → needs_follow_up
- **Shape:** [1, 1] float32 (sigmoid)  OR  [1, 2] float32 (logits)
- **Meaning:** Probability that the user should be asked for more symptoms.
- **Usage:** Threshold at 0.5 to get boolean.
  ```
  val showFollowUp = needsFollowUp[0] >= 0.5f
  ```

---

### → severity
- **Shape:** [1, 3] float32 (softmax)
- **Meaning:** 3-class severity probabilities. Index order is fixed.
- **Usage:** Take argmax for predicted class. Map index to your severity enum.
  ```
  val severityIndex = severity[0].indices.maxByOrNull { severity[0][it] } ?: 0
  ```
- **Index order (define in your app):**
  ```
  enum class Severity { MILD, MODERATE, NEEDS_REST }
  // severity[0][0] = MILD
  // severity[0][1] = MODERATE
  // severity[0][2] = NEEDS_REST
  ```

---

### → suggested_symptoms
- **Shape:** [1, 5] int32  OR  [1, 5] float32 logits → argmax in app
- **Meaning:** Up to 5 indices into symptom_vocab.json. Index 0 = NONE / unused slot.
- **Usage:** Only render in UI when needs_follow_up >= 0.5. Skip any slot where index == 0.
  ```
  val suggestions = suggestedSymptoms[0]
      .filter { it != 0 }
      .map { vocab[it] }
  ```

---

## Conditional Rendering Rule

  ONLY display suggested_symptoms in the UI when needs_follow_up >= 0.5.
  Skip any slot whose index is 0 (NONE).

---

## TFLite — Kotlin Interpreter Notes

```kotlin
// Output buffers
val confidence      = Array(1) { FloatArray(1) }
val needsFollowUp   = Array(1) { FloatArray(1) }
val severity        = Array(1) { FloatArray(3) }
val suggestedSymptoms = Array(1) { IntArray(5) }   // or FloatArray(5) if logits

val outputMap = mapOf(
    0 to confidence,
    1 to needsFollowUp,
    2 to severity,
    3 to suggestedSymptoms
)

interpreter.runForMultipleInputsOutputs(inputs, outputMap)
```

Output index order must match the order your model was exported with.
Verify with Netron or tf.lite.Interpreter(model_path).get_output_details().

---

## symptom_vocab.json

Location: assets/symptom_vocab.json

Format:
```json
["NONE", "FEVER", "COUGH", "SHORTNESS_OF_BREATH", "CHEST_PAIN", "FATIGUE", "..."]
```

- Index 0 is always NONE (unused/padding slot).
- Load once at app start; keep in memory for the session.

```kotlin
val vocab: List<String> = context.assets
    .open("symptom_vocab.json")
    .bufferedReader()
    .use { Json.decodeFromString(it.readText()) }
```

---

## Slot Mapping — Example Inference Output

```
needs_follow_up :  1.0          → show suggestions (>= 0.5 threshold met)
confidence      :  0.42         → moderate reliability
severity        :  [0.1, 0.2, 0.7]  → argmax = index 2 → NEEDS_REST
suggested_symptoms (raw indices): [12, 45, 7, 0, 0]
```

Mapped for display:

  Slot  Index  Label
  ----  -----  ----------------------
  1     12     SHORTNESS_OF_BREATH
  2     45     CHEST_PAIN
  3     7      FATIGUE
  4     0      skip (NONE)
  5     0      skip (NONE)

---

## Summary Table

  Output              Shape     Type     Activation  Notes
  ------------------  --------  -------  ----------  ----------------------------------
  confidence          [1, 1]    float32  none        Raw reliability score 0–1
  needs_follow_up     [1, 1]    float32  sigmoid     Threshold at 0.5 for boolean
  severity            [1, 3]    float32  softmax     argmax → fixed-index severity enum
  suggested_symptoms  [1, 5]    int32    none        Index 0 = NONE; skip in UI

---

## Assets Checklist

  [ ] model.tflite              — exported TFLite model
  [ ] symptom_vocab.json        — symptom index → string label
  [ ] severity enum defined     — matches fixed index order above
  [ ] Output index order verified with get_output_details()
