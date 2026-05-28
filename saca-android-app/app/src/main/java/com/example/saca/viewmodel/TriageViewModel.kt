package com.example.saca.viewmodel

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.example.saca.ml.TFLiteInferenceEngine
import com.example.saca.model.*
import com.example.saca.nlp.NlpRepository
import com.example.saca.nlp.QuestionRepository
import com.example.saca.util.NarrationManager
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class TriageViewModel(application: Application) : AndroidViewModel(application) {

    private val inferenceEngine = TFLiteInferenceEngine(application)
    private val nlpRepository   = NlpRepository(application)
    val narrationManager        = NarrationManager(application)

    // ── Loading state ─────────────────────────────────────────────────────
    private val _isLoading       = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    private val _loadingProgress = MutableStateFlow(0f)
    val loadingProgress: StateFlow<Float> = _loadingProgress.asStateFlow()

    private val _loadingStatus   = MutableStateFlow("")
    val loadingStatus: StateFlow<String> = _loadingStatus.asStateFlow()

    private val _usedRemoteNlp   = MutableStateFlow(false)
    val usedRemoteNlp: StateFlow<Boolean> = _usedRemoteNlp.asStateFlow()

    // ── App state ─────────────────────────────────────────────────────────
    private val _language = MutableStateFlow(Language.ENGLISH)
    val language: StateFlow<Language> = _language.asStateFlow()

    private val _inputMode = MutableStateFlow<InputMode?>(null)
    val inputMode: StateFlow<InputMode?> = _inputMode.asStateFlow()

    private val _selectedSymptoms = MutableStateFlow<Set<Symptom>>(emptySet())
    val selectedSymptoms: StateFlow<Set<Symptom>> = _selectedSymptoms.asStateFlow()

    private val _speechTranscript = MutableStateFlow("")
    val speechTranscript: StateFlow<String> = _speechTranscript.asStateFlow()

    private val _typedInput = MutableStateFlow("")
    val typedInput: StateFlow<String> = _typedInput.asStateFlow()

    private val _inferenceResult = MutableStateFlow<ModelInferenceResult?>(null)
    val inferenceResult: StateFlow<ModelInferenceResult?> = _inferenceResult.asStateFlow()

    // ── Follow-up questions state ─────────────────────────────────────────
    private val _followUpQuestions = MutableStateFlow<List<FollowUpQuestion>>(emptyList())
    val followUpQuestions: StateFlow<List<FollowUpQuestion>> = _followUpQuestions.asStateFlow()

    // Map follow-up question IDs → canonical symptoms when answered "yes"
    private val answerToSymptom = mapOf(
        "fever_now"              to "fever",
        "fever_cough"            to "cough",
        "fever_rash"             to "rash",
        "cough_breathing"        to "difficulty_breathing",
        "cough_fever"            to "fever",
        "breathing_chest_pain"   to "chest_pain",
        "chest_pain_breathing"   to "difficulty_breathing",
        "headache_vomiting"      to "vomiting",
        "headache_fever"         to "fever",
        "headache_light"         to "light_sensitivity",
        "stomach_vomiting"       to "vomiting",
        "stomach_fever"          to "fever",
        "vomiting_stomach_pain"  to "stomach_pain",
        "diarrhea_stomach_pain"  to "stomach_pain",
        "diarrhea_fever"         to "fever",
        "rash_fever"             to "fever",
        "rash_swelling"          to "swelling",
        "throat_fever"           to "fever",
        "throat_cough"           to "cough"
    )

    private var _lastCanonicalSymptoms: List<String> = emptyList()


    private val _followUpIndex = MutableStateFlow(0)
    val followUpIndex: StateFlow<Int> = _followUpIndex.asStateFlow()

    private val _followUpAnswers = MutableStateFlow<Map<String, String>>(emptyMap())
    val followUpAnswers: StateFlow<Map<String, String>> = _followUpAnswers.asStateFlow()

    private val _bodyMapVocabKeys = MutableStateFlow<List<String>>(emptyList())
   val bodyMapVocabKeys: StateFlow<List<String>> = _bodyMapVocabKeys.asStateFlow()

    init {
        inferenceEngine.initialise()
        nlpRepository.initialise()
    }

    // ── Setters ───────────────────────────────────────────────────────────
    fun setLanguage(lang: Language)       { _language.value = lang }
    fun setInputMode(mode: InputMode)     { _inputMode.value = mode }
    fun setSpeechTranscript(text: String) { _speechTranscript.value = text }
    fun setTypedInput(text: String)       { _typedInput.value = text }
    fun switchToSpeech()                  { _inputMode.value = InputMode.SPEAK }
    fun setSelectedSymptomsFromBodyMap(vocabKeys: List<String>) {
       _bodyMapVocabKeys.value = vocabKeys
   }

    fun toggleSymptom(symptom: Symptom) {
        _selectedSymptoms.value = _selectedSymptoms.value.toMutableSet().apply {
            if (contains(symptom)) remove(symptom) else add(symptom)
        }
    }

    // ── Follow-up helpers ─────────────────────────────────────────────────
    fun prepareFollowUpQuestions(canonicalSymptoms: List<String>) {
        val questions = QuestionRepository.selectQuestions(canonicalSymptoms)
        _followUpQuestions.value = questions
        _followUpIndex.value     = 0
        _followUpAnswers.value   = emptyMap()
        android.util.Log.d("ViewModel", "Prepared ${questions.size} follow-up questions")
    }

    /**
     * Returns true when all questions are answered — caller navigates to result.
     * Returns false when more questions remain — caller stays on follow-up screen.
     */
    fun answerFollowUp(questionId: String, answer: String): Boolean {
        _followUpAnswers.value = _followUpAnswers.value + (questionId to answer)
        val next = _followUpIndex.value + 1
        return if (next < _followUpQuestions.value.size) {
            _followUpIndex.value = next
            false   // more questions remain
        } else {
            true    // all done
        }
    }

    // ── Main inference pipeline ───────────────────────────────────────────
    /**
     * onComplete(needsFollowUp):
     *   true  → NavGraph navigates to FollowUp screen
     *   false → NavGraph navigates directly to Result screen
     */
    fun runInference(onComplete: (needsFollowUp: Boolean) -> Unit) {
        viewModelScope.launch {
            _isLoading.value       = true
            _loadingProgress.value = 0f
            _loadingStatus.value   = if (_language.value == Language.ENGLISH)
                "Reading your symptoms..." else "Ridin yu simptoms..."

            // Step 1 — get raw text safely
            val rawText = when (_inputMode.value) {
                InputMode.TYPE     -> _typedInput.value.takeIf { it.isNotBlank() } ?: ""
                InputMode.SPEAK    -> _speechTranscript.value.takeIf { it.isNotBlank() } ?: ""
                InputMode.PICTURES -> {
                    _bodyMapVocabKeys.value.joinToString(" ")
                }
                null -> {
                    _isLoading.value = false
                    return@launch
                }
            }

            // Guard — nothing to process
            if (rawText.isBlank()) {
                android.util.Log.w("ViewModel", "rawText is blank — aborting")
                _isLoading.value = false
                onComplete(false)
                return@launch
            }

            // Progress: 20%
            _loadingProgress.value = 0.2f
            _loadingStatus.value   = if (_language.value == Language.ENGLISH)
                "Running language detection..." else "Fainding langwij..."
            delay(300)

            // Step 2 — NLP (remote or local) with null safety
            _loadingProgress.value = 0.4f
            android.util.Log.d("ViewModel", "rawText='$rawText' | inputMode=${_inputMode.value} | lang=${_language.value}")

            val uiLang = if (_language.value == Language.KRIOL) "kriol" else "en"

            val nlpResult = try {
                nlpRepository.process(rawText, uiLang)
            } catch (e: Exception) {
                android.util.Log.e("ViewModel", "NLP failed: ${e.message}")
                NlpRepository.NlpResult(
                    canonicalSymptoms = rawText.lowercase()
                        .split(" ", ",", ".")
                        .map { it.trim() }
                        .filter { it.length > 2 },
                    symptomsPresent   = emptyList(),
                    symptomsNegated   = emptyList(),
                    detectedLanguage  = "english",
                    translatedText    = rawText,
                    usedRemote        = false
                )
            }

            // ← Store canonical symptoms for runFinalInference
            _lastCanonicalSymptoms = nlpResult.canonicalSymptoms

            _usedRemoteNlp.value = nlpResult.usedRemote

            _loadingStatus.value = if (nlpResult.usedRemote) {
                if (_language.value == Language.ENGLISH)
                    "NLP pipeline complete ✓" else "NLP pipeline don ✓"
            } else {
                if (_language.value == Language.ENGLISH)
                    "On-device analysis complete ✓" else "Dibais analysis don ✓"
            }
            delay(300)

            // Progress: 70%
            _loadingProgress.value = 0.7f
            _loadingStatus.value   = if (_language.value == Language.ENGLISH)
                "Running triage model..." else "Ronin triage model..."
            delay(200)

            // Step 3 — TFLite inference
            val result = inferenceEngine.runInference(nlpResult.canonicalSymptoms)

            // Step 4 — debug severity override (null = use real result)
            val debugSeverity: Severity? = null
            _inferenceResult.value = if (debugSeverity != null)
                result.copy(severity = debugSeverity)
            else
                result

            // Progress: 100%
            _loadingProgress.value = 1.0f
            _loadingStatus.value   = if (_language.value == Language.ENGLISH)
                "Done!" else "Don!"
            delay(400)

            _isLoading.value = false

            // Step 5 — check if follow-up needed
            val needsFollowUp = result.needsFollowUp &&
                    nlpResult.canonicalSymptoms.isNotEmpty()

            if (needsFollowUp) {
                prepareFollowUpQuestions(nlpResult.canonicalSymptoms)
            }

            android.util.Log.d("ViewModel", "NeedsFollowUp: $needsFollowUp")
            android.util.Log.d("ViewModel", "Canonical symptoms: ${nlpResult.canonicalSymptoms}")

            // Step 6 — notify NavGraph
            onComplete(needsFollowUp)
        }
    }

    // Called when all follow-up questions are answered
    fun runFinalInference() {
        viewModelScope.launch {

            // Step 1 — extract symptoms from yes answers
            val answeredSymptoms = _followUpAnswers.value
                .filter { (_, answer) -> answer.lowercase() == "yes" }
                .mapNotNull { (questionId, _) -> answerToSymptom[questionId] }

            android.util.Log.d("ViewModel", "Answered symptoms: $answeredSymptoms")

            // Step 2 — merge with original canonical symptoms
            val currentResult   = _inferenceResult.value
            val allSymptoms      = (_lastCanonicalSymptoms + answeredSymptoms).distinct()

            android.util.Log.d("ViewModel", "Final merged symptoms: $allSymptoms")

            // Step 3 — re-run TFLite with merged symptoms
            if (allSymptoms.isNotEmpty()) {
                val finalResult = inferenceEngine.runInference(allSymptoms)
                _inferenceResult.value = finalResult
                android.util.Log.d("ViewModel", "Final severity: ${finalResult.severity}")
            }
        }
    }

    // ── Reset ─────────────────────────────────────────────────────────────
    fun resetSession() {
        _inferenceResult.value   = null
        _selectedSymptoms.value  = emptySet()
        _speechTranscript.value  = ""
        _typedInput.value        = ""
        _inputMode.value         = null
        _isLoading.value         = false
        _loadingProgress.value   = 0f
        _loadingStatus.value     = ""
        _followUpQuestions.value = emptyList()
        _followUpIndex.value     = 0
        _followUpAnswers.value   = emptyMap()
        _lastCanonicalSymptoms   = emptyList()
    }

    override fun onCleared() {
        super.onCleared()
        inferenceEngine.close()
        narrationManager.release()
    }
}