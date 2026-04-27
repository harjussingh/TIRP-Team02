# Comprehensive System Proposal: Adaptive Clinical Assistant
## Multilingual Medical Triage System with AI-Powered Severity Prediction

**Project Duration:** 10-12 weeks  
**Target Deployment:** Offline-capable Android & Windows Applications  
**Primary Languages:** English, Kriol (Australian Indigenous Language)  
**Target Accuracy:** 92%+ overall system performance

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [System Architecture Overview](#system-architecture-overview)
3. [Four-Module System Design](#four-module-system-design)
4. [Technology Stack & Justification](#technology-stack--justification)
5. [Detailed Implementation Approach](#detailed-implementation-approach)
6. [Data Flow & Integration](#data-flow--integration)
7. [Offline Deployment Strategy](#offline-deployment-strategy)
8. [Performance Benchmarks & KPIs](#performance-benchmarks--kpis)
9. [Implementation Timeline](#implementation-timeline)
10. [Risk Management & Mitigation](#risk-management--mitigation)
11. [Future Scalability](#future-scalability)

---

## Executive Summary

### Problem Statement
Indigenous Australian communities and remote healthcare facilities require an accessible, multilingual medical triage system that:
- Operates completely offline due to limited connectivity
- Supports Kriol language alongside English
- Accepts voice and text input for accessibility
- Provides accurate symptom extraction and severity assessment
- Guides healthcare workers in prioritizing patient care

### Proposed Solution
A four-module AI-powered clinical assistant system consisting of:
1. **NLP Module**: Multilingual symptom extraction and translation
2. **ML Module**: Three-model ensemble for severity prediction
3. **Android Application**: Mobile deployment for field healthcare workers
4. **Windows Application**: Desktop deployment for clinic settings

### Key Innovation
**Hybrid AI Approach**: Combines rule-based methods (fast, interpretable, offline) with deep learning models (accurate, context-aware) to achieve 92%+ accuracy while maintaining <1s response time and full offline capability.

### Expected Impact
- **78% → 92%** accuracy improvement through advanced NLP techniques
- **<1 second** end-to-end processing time
- **100% offline** operation with ~750MB total model footprint
- **Bilingual support** enabling culturally appropriate healthcare access
- **Voice input** reducing literacy barriers

---

## System Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE LAYER                      │
│  ┌──────────────────────────┐  ┌──────────────────────────────┐│
│  │   Android Application    │  │   Windows Application        ││
│  │   (Mobile - Field Use)   │  │   (Desktop - Clinic Use)     ││
│  │   - Voice Recording      │  │   - Voice Recording          ││
│  │   - Text Input           │  │   - Text Input               ││
│  │   - Offline Storage      │  │   - Patient Records          ││
│  └──────────────────────────┘  └──────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              ↓↑
┌─────────────────────────────────────────────────────────────────┐
│                       NLP PROCESSING LAYER                       │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Voice      │  │   Language   │  │  Translation │         │
│  │  Processing  │→ │  Detection   │→ │    Engine    │         │
│  │  (Whisper)   │  │  (TF-IDF)    │  │(Transformer) │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                              ↓                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Symptom    │  │   Negation   │  │   Feature    │         │
│  │  Extraction  │→ │  Detection   │→ │  Generation  │         │
│  │ (BERT+spaCy) │  │(LSTM+Rules)  │  │              │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
│  Output: Structured JSON with symptoms, context, embeddings     │
└─────────────────────────────────────────────────────────────────┘
                              ↓↑
┌─────────────────────────────────────────────────────────────────┐
│                    ML PREDICTION LAYER                           │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Three-Model Ensemble                         │  │
│  │                                                           │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐        │  │
│  │  │  Random    │  │  Gradient  │  │   Neural   │        │  │
│  │  │  Forest    │  │  Boosting  │  │  Network   │        │  │
│  │  │ (Baseline) │  │  (XGBoost) │  │  (MLP)     │        │  │
│  │  └────────────┘  └────────────┘  └────────────┘        │  │
│  │         ↓               ↓               ↓                │  │
│  │  ┌──────────────────────────────────────────────┐       │  │
│  │  │        Weighted Voting Ensemble              │       │  │
│  │  │        (Confidence-based aggregation)        │       │  │
│  │  └──────────────────────────────────────────────┘       │  │
│  │                        ↓                                  │  │
│  │         Severity Score (1-10) + Recommendations          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓↑
┌─────────────────────────────────────────────────────────────────┐
│                       DATA STORAGE LAYER                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Patient    │  │   Model      │  │   Clinical   │         │
│  │   Records    │  │   Cache      │  │   Knowledge  │         │
│  │  (SQLite)    │  │  (Offline)   │  │    Base      │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
User Input (Voice/Text)
    ↓
[Voice Processing: Whisper converts speech to text]
    ↓
[Language Detection: TF-IDF classifier identifies English vs Kriol]
    ↓
[Translation: Transformer model translates Kriol → English]
    ↓
[Preprocessing: Spell correction, normalization, contraction expansion]
    ↓
[Symptom Extraction: BioClinicalBERT NER + spaCy PhraseMatcher]
    ↓
[Negation Detection: LSTM context model + rule-based patterns]
    ↓
[Feature Engineering: Generate embeddings, symptom counts, linguistic features]
    ↓
[ML Ensemble: Three models vote on severity classification]
    ↓
[Output: Severity score + present symptoms + negated symptoms + recommendations]
    ↓
Display to User Interface (Android/Windows)
```

---

## Four-Module System Design

### Module 1: NLP Processing Engine (Your Responsibility)

**Objective**: Transform raw user input (voice/text, English/Kriol) into structured medical data for ML consumption.

#### Core Components

##### 1.1 Voice Processing Subsystem
**Technology**: OpenAI Whisper (Small Model - 460MB)

**Why Whisper?**
- State-of-the-art speech recognition (85%+ accuracy)
- Multilingual support with custom prompting
- Offline-capable with reasonable model size
- Robust to accents and background noise
- Open-source and actively maintained

**How It Works**:
```python
class VoiceProcessor:
    def __init__(self):
        # Load quantized Whisper model (460MB → 120MB after quantization)
        self.model = whisper.load_model("small")
        self.medical_prompt = "Transcript: fever, headache, cough, dizziness, nausea..."
        self.kriol_prompt = "Kriol words: mi garr hedache, nat garr fiva..."
    
    def transcribe_bilingual(self, audio_path):
        # Bilingual prompting guides Whisper to recognize both languages
        result = self.model.transcribe(
            audio_path,
            language=None,  # Auto-detect
            initial_prompt=f"{self.medical_prompt} {self.kriol_prompt}",
            temperature=0.0  # Deterministic output
        )
        
        # Post-process common medical transcription errors
        text = self._fix_medical_errors(result["text"])
        detected_language = self._detect_language(text)
        
        return text, detected_language
```

**Performance Metrics**:
- Accuracy: 85% (current) → 90% (with larger model + fine-tuning)
- Latency: 2-3 seconds per 10-second audio clip
- Model Size: 460MB (quantized to 120MB)

##### 1.2 Language Detection Subsystem
**Technology**: TF-IDF + Logistic Regression

**Why TF-IDF?**
- Fast inference (<10ms)
- Minimal model size (<1MB)
- Interpretable feature importance
- Works well with limited training data
- No GPU required

**How It Works**:
```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

class LanguageDetector:
    def __init__(self):
        # TF-IDF extracts character n-grams (language fingerprints)
        self.vectorizer = TfidfVectorizer(
            analyzer='char',
            ngram_range=(2, 4),  # Character bigrams to 4-grams
            max_features=500     # Lightweight model
        )
        self.classifier = LogisticRegression()
    
    def train(self, texts, labels):
        # Train on English and Kriol text samples
        X = self.vectorizer.fit_transform(texts)
        self.classifier.fit(X, labels)
    
    def detect(self, text):
        # Fast inference with confidence scores
        X = self.vectorizer.transform([text])
        proba = self.classifier.predict_proba(X)[0]
        
        if max(proba) < 0.7:
            return "mixed"  # Both languages present
        return self.classifier.predict(X)[0]
```

**Why Character N-grams?**
- Capture language-specific patterns ("garr" vs "have")
- Robust to spelling variations
- Work with short text (few words)

**Performance Metrics**:
- Accuracy: 85% (current) → 95% (with larger corpus)
- Latency: <10ms
- Model Size: <1MB

##### 1.3 Translation Engine
**Technology**: MarianMT (Transformer) + Dictionary Fallback

**Why Hybrid Approach?**
- **Dictionary (110 words)**: Fast, deterministic, works offline
- **Transformer**: Context-aware, handles unseen words, grammatically correct

**How It Works**:
```python
from transformers import MarianMTModel, MarianTokenizer

class HybridTranslator:
    def __init__(self):
        # Load dictionary for common words (instant lookup)
        self.dictionary = load_kriol_dictionary()  # 110 words
        
        # Load fine-tuned MarianMT for context-aware translation
        self.tokenizer = MarianTokenizer.from_pretrained("custom/kriol-en")
        self.model = MarianMTModel.from_pretrained("custom/kriol-en")
        # Quantized: 300MB → 80MB
    
    def translate(self, kriol_text):
        tokens = self.tokenize_kriol(kriol_text)
        
        # Step 1: Dictionary lookup for known words (fast)
        translated_tokens = []
        unknown_spans = []
        
        for i, token in enumerate(tokens):
            if token.lower() in self.dictionary:
                translated_tokens.append(self.dictionary[token.lower()])
            else:
                unknown_spans.append((i, token))
        
        # Step 2: Neural translation for unknown/ambiguous spans
        if unknown_spans:
            context = " ".join(tokens)
            neural_output = self._neural_translate(context)
            # Merge dictionary + neural results
            translated_tokens = self._merge_translations(
                translated_tokens, neural_output, unknown_spans
            )
        
        return " ".join(translated_tokens)
```

**Why MarianMT?**
- Specifically designed for translation
- Smaller than GPT models (300MB vs 6GB+)
- Fast inference (~100ms per sentence)
- Can be fine-tuned on Kriol data
- Open-source (Helsinki-NLP)

**Performance Metrics**:
- Accuracy: 75% (dictionary only) → 92% (hybrid)
- Latency: <10ms (dictionary) + 100ms (neural) = 110ms total
- Model Size: 300MB (quantized to 80MB)

##### 1.4 Symptom Extraction Engine
**Technology**: BioClinicalBERT + spaCy PhraseMatcher

**Why BERT for Medical Text?**
- Pre-trained on 2M+ clinical notes
- Understands medical context and terminology
- Named Entity Recognition (NER) for symptoms
- Captures semantic similarity ("dizzy" ≈ "dizziness")

**Why Keep spaCy?**
- Fast rule-based matching (backup)
- Interpretable exact phrase matching
- No GPU required for inference
- Useful for known symptom vocabulary

**How It Works**:
```python
from transformers import AutoTokenizer, AutoModelForTokenClassification
import spacy

class SymptomExtractor:
    def __init__(self):
        # Load BioClinicalBERT for NER
        self.tokenizer = AutoTokenizer.from_pretrained(
            "emilyalsentzer/Bio_ClinicalBERT"
        )
        self.model = AutoModelForTokenClassification.from_pretrained(
            "custom/symptom-ner-model"  # Fine-tuned on symptom data
        )
        # Quantized: 440MB → 110MB
        
        # Load spaCy for backup rule-based extraction
        self.nlp = spacy.load("en_core_web_sm")
        self.symptom_phrases = load_symptom_list()  # Known symptoms
        self.matcher = PhraseMatcher(self.nlp.vocab)
        self.matcher.add("SYMPTOM", self.symptom_phrases)
    
    def extract_symptoms(self, text):
        # Method 1: BERT NER (primary)
        bert_symptoms = self._bert_extract(text)
        
        # Method 2: spaCy PhraseMatcher (backup)
        spacy_symptoms = self._spacy_extract(text)
        
        # Ensemble: Combine both methods (union)
        all_symptoms = set(bert_symptoms) | set(spacy_symptoms)
        
        # Confidence scoring
        symptom_scores = {}
        for symptom in all_symptoms:
            score = 0.0
            if symptom in bert_symptoms:
                score += 0.7  # BERT is primary
            if symptom in spacy_symptoms:
                score += 0.3  # spaCy is backup
            symptom_scores[symptom] = score
        
        # Return symptoms with confidence > 0.5
        return {s: score for s, score in symptom_scores.items() if score > 0.5}
```

**Why Ensemble Approach?**
- BERT catches semantic variations ("feeling hot" → fever)
- spaCy catches exact medical terms ("myalgia")
- Union increases recall, confidence filtering maintains precision

**Performance Metrics**:
- Accuracy: 78% (spaCy only) → 92% (ensemble)
- Latency: 5ms (spaCy) + 150ms (BERT) = 155ms total
- Model Size: 440MB BERT + 15MB spaCy = 455MB (quantized to 125MB)

##### 1.5 Negation Detection Engine
**Technology**: LSTM + Rule-Based Patterns

**Why LSTM?**
- Captures sequential context ("don't have X but do have Y")
- Learns negation scope from training data
- Handles complex sentence structures
- Lightweight compared to BERT (50MB vs 440MB)

**Why Keep Rules?**
- Fast inference for simple cases ("no fever")
- Interpretable and debuggable
- 100% accurate on common patterns
- Fallback when LSTM confidence is low

**How It Works**:
```python
import tensorflow as tf
import re

class NegationDetector:
    def __init__(self):
        # Load LSTM model for context-aware negation
        self.lstm_model = tf.keras.models.load_model("negation_lstm.h5")
        # Architecture: Embedding(10000) → Bi-LSTM(128) → Dense(1, sigmoid)
        # Size: 50MB → 15MB quantized
        
        # Rule-based patterns for simple cases
        self.negation_patterns = [
            r'\b(no|not|never|without)\s+(\w+\s+){0,3}',
            r'\b(don\'t|doesn\'t|didn\'t|haven\'t)\s+(\w+\s+){0,3}',
            r'\b(deny|denies|negative for)\s+(\w+\s+){0,3}'
        ]
    
    def detect_negations(self, text, symptoms):
        negated_symptoms = []
        
        for symptom in symptoms:
            # Method 1: Rule-based (fast)
            rule_negated = self._rule_based_check(text, symptom)
            
            # Method 2: LSTM (context-aware)
            lstm_confidence = self._lstm_check(text, symptom)
            
            # Decision logic
            if rule_negated:
                negated_symptoms.append({
                    'symptom': symptom,
                    'method': 'rule',
                    'confidence': 1.0
                })
            elif lstm_confidence > 0.7:
                negated_symptoms.append({
                    'symptom': symptom,
                    'method': 'lstm',
                    'confidence': lstm_confidence
                })
        
        return negated_symptoms
    
    def _lstm_check(self, text, symptom):
        # Create context window around symptom
        context = self._get_context_window(text, symptom, window_size=6)
        
        # Tokenize and pad
        tokens = self.tokenizer.texts_to_sequences([context])
        padded = tf.keras.preprocessing.sequence.pad_sequences(tokens, maxlen=15)
        
        # Predict negation probability
        negation_prob = self.lstm_model.predict(padded)[0][0]
        return negation_prob
```

**Why Bidirectional LSTM?**
- Reads sentence forwards and backwards
- Captures "but" transitions ("no X but Y")
- Learns negation scope from context
- Fast inference (~20ms per symptom)

**Performance Metrics**:
- Accuracy: 82% (rules only) → 96% (hybrid)
- Latency: <2ms (rules) + 20ms (LSTM) = 22ms per symptom
- Model Size: 50MB (quantized to 15MB)

##### 1.6 Feature Engineering
**Purpose**: Generate ML-ready features for severity prediction

```python
class FeatureGenerator:
    def generate_features(self, nlp_output):
        features = {}
        
        # Symptom counts
        features['num_symptoms_present'] = len(nlp_output['symptoms_present'])
        features['num_symptoms_negated'] = len(nlp_output['symptoms_negated'])
        
        # Symptom severity weights (pre-defined medical knowledge)
        features['weighted_symptom_score'] = self._calculate_weighted_score(
            nlp_output['symptoms_present']
        )
        
        # Linguistic features
        features['input_length'] = len(nlp_output['input_text'].split())
        features['language'] = nlp_output['detected_language']
        features['has_negations'] = int(len(nlp_output['symptoms_negated']) > 0)
        
        # BERT embeddings (768-dim vector for semantic similarity)
        features['symptom_embeddings'] = self._get_bert_embeddings(
            " ".join(nlp_output['symptoms_present'])
        )
        
        # Symptom co-occurrence patterns
        features['symptom_pattern'] = self._get_pattern_encoding(
            nlp_output['symptoms_present']
        )
        
        return features
```

#### NLP Module Output Format

```json
{
  "timestamp": "2026-03-27T10:30:45Z",
  "input_text": "Mi garr hedache en mi stomach sore-one",
  "detected_language": "kriol",
  "translated_text": "I have headache and my stomach is sore",
  "cleaned_text": "i have headache and my stomach is sore",
  
  "symptoms_present": [
    {"symptom": "headache", "confidence": 0.95, "method": "bert"},
    {"symptom": "abdominal pain", "confidence": 0.88, "method": "bert"}
  ],
  
  "symptoms_negated": [],
  
  "features_for_ml": {
    "num_symptoms_present": 2,
    "num_symptoms_negated": 0,
    "weighted_symptom_score": 4.5,
    "input_length": 8,
    "language": "kriol",
    "has_negations": 0,
    "symptom_embeddings": [0.23, -0.45, 0.12, ...],  // 768-dim vector
    "symptom_pattern": "headache+abdominal_pain"
  },
  
  "processing_time_ms": 385,
  "model_versions": {
    "whisper": "small-quantized-v1",
    "language_detector": "tfidf-v2",
    "translator": "marianmt-kriol-v1",
    "symptom_extractor": "bioclinicalbert-v3",
    "negation_detector": "lstm-hybrid-v2"
  }
}
```

---

### Module 2: ML Severity Prediction (Team Member Responsibility)

**Objective**: Predict patient severity (1-10 scale) and provide triage recommendations.

#### Why Three-Model Ensemble?

**Individual Model Strengths**:
1. **Random Forest**: Robust to noise, captures non-linear relationships
2. **XGBoost**: Superior accuracy, handles imbalanced data
3. **Neural Network**: Learns complex feature interactions, uses embeddings

**Ensemble Benefit**: Combines strengths, reduces overfitting, provides confidence estimates

#### Architecture

```python
class SeverityPredictor:
    def __init__(self):
        # Model 1: Random Forest (Baseline)
        self.rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=15,
            class_weight='balanced'
        )
        
        # Model 2: XGBoost (Gradient Boosting)
        self.xgb_model = xgb.XGBClassifier(
            n_estimators=150,
            max_depth=8,
            learning_rate=0.1,
            objective='multi:softmax',
            num_class=10
        )
        
        # Model 3: Neural Network (MLP)
        self.nn_model = tf.keras.Sequential([
            tf.keras.layers.Dense(256, activation='relu', input_dim=800),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(10, activation='softmax')
        ])
    
    def predict_severity(self, nlp_features):
        # Extract features
        X = self._prepare_features(nlp_features)
        
        # Get predictions from all models
        rf_pred = self.rf_model.predict_proba(X)[0]
        xgb_pred = self.xgb_model.predict_proba(X)[0]
        nn_pred = self.nn_model.predict(X)[0]
        
        # Weighted voting (based on validation accuracy)
        ensemble_pred = (
            0.25 * rf_pred +  # 25% weight
            0.40 * xgb_pred + # 40% weight (best individual model)
            0.35 * nn_pred    # 35% weight
        )
        
        severity_score = np.argmax(ensemble_pred) + 1  # 1-10 scale
        confidence = np.max(ensemble_pred)
        
        return {
            'severity_score': severity_score,
            'confidence': confidence,
            'recommendation': self._get_recommendation(severity_score),
            'individual_predictions': {
                'random_forest': int(np.argmax(rf_pred)) + 1,
                'xgboost': int(np.argmax(xgb_pred)) + 1,
                'neural_network': int(np.argmax(nn_pred)) + 1
            }
        }
    
    def _get_recommendation(self, severity):
        if severity <= 3:
            return "Low Priority: Self-care with monitoring"
        elif severity <= 6:
            return "Medium Priority: Schedule appointment within 24-48 hours"
        elif severity <= 8:
            return "High Priority: Seek medical attention within 4-6 hours"
        else:
            return "Emergency: Immediate medical attention required"
```

#### Training Data Requirements

**Dataset Size**: 10,000+ patient records with:
- Symptoms (from NLP module output)
- Severity labels (1-10) from medical professionals
- Actual diagnoses (for validation)

**Data Augmentation**:
- Synthetic symptom combinations
- Severity label smoothing
- Cross-validation for robustness

#### Performance Metrics
- **Accuracy**: 88-92% on severity classification
- **RMSE**: <1.2 on 10-point scale
- **Latency**: <50ms inference time
- **Model Size**: 150MB total (all three models quantized)

---

### Module 3: Android Application (Team Member Responsibility)

**Objective**: Mobile app for field healthcare workers with offline capability.

#### Technology Stack

**Framework**: **Kotlin + Jetpack Compose**

**Why Kotlin?**
- Official Android language (Google-backed)
- Modern, concise syntax
- Null-safety built-in
- Coroutines for async operations
- Full ecosystem support

**Why Jetpack Compose?**
- Declarative UI (like React)
- Less boilerplate than XML layouts
- Better performance
- Built-in Material Design 3

#### Core Features

##### 1. Voice Recording
```kotlin
class VoiceRecorder(context: Context) {
    private val audioRecord = AudioRecord(
        MediaRecorder.AudioSource.MIC,
        16000, // Sample rate
        AudioFormat.CHANNEL_IN_MONO,
        AudioFormat.ENCODING_PCM_16BIT,
        bufferSize
    )
    
    suspend fun recordAudio(): File = withContext(Dispatchers.IO) {
        val outputFile = File(context.cacheDir, "recording.wav")
        audioRecord.startRecording()
        
        // Record for max 30 seconds or until stopped
        val audioData = ByteArray(bufferSize)
        while (isRecording) {
            val read = audioRecord.read(audioData, 0, bufferSize)
            outputStream.write(audioData, 0, read)
        }
        
        audioRecord.stop()
        return@withContext outputFile
    }
}
```

##### 2. Offline Model Integration
```kotlin
class OfflineMLProcessor(context: Context) {
    private val whisperModel: WhisperModel
    private val nlpPipeline: NLPPipeline
    private val severityPredictor: SeverityModel
    
    init {
        // Load quantized models from assets folder (~750MB total)
        whisperModel = WhisperModel.loadFromAssets(context, "whisper_small_quantized.tflite")
        nlpPipeline = NLPPipeline.loadFromAssets(context, "nlp_models/")
        severityPredictor = SeverityModel.loadFromAssets(context, "ml_ensemble_quantized.tflite")
    }
    
    suspend fun processPatientInput(audioFile: File): PredictionResult {
        // Step 1: Transcribe audio
        val transcription = whisperModel.transcribe(audioFile)
        
        // Step 2: NLP processing
        val nlpOutput = nlpPipeline.process(transcription.text)
        
        // Step 3: Severity prediction
        val severity = severityPredictor.predict(nlpOutput.features)
        
        return PredictionResult(
            transcription = transcription.text,
            language = nlpOutput.language,
            symptoms = nlpOutput.symptomsPresent,
            severityScore = severity.score,
            recommendation = severity.recommendation
        )
    }
}
```

##### 3. Local Database (SQLite)
```kotlin
@Database(
    entities = [PatientRecord::class, PredictionHistory::class],
    version = 1
)
abstract class ClinicalDatabase : RoomDatabase() {
    abstract fun patientDao(): PatientDao
    abstract fun predictionDao(): PredictionDao
}

@Entity
data class PatientRecord(
    @PrimaryKey val patientId: String,
    val name: String,
    val age: Int,
    val lastVisit: Long,
    val recordingFiles: List<String>
)

@Entity
data class PredictionHistory(
    @PrimaryKey(autoGenerate = true) val id: Int,
    val patientId: String,
    val timestamp: Long,
    val inputText: String,
    val symptoms: List<String>,
    val severityScore: Int,
    val synced: Boolean
)
```

##### 4. UI Components (Jetpack Compose)
```kotlin
@Composable
fun ClinicalAssistantScreen(viewModel: ClinicalViewModel) {
    val uiState by viewModel.uiState.collectAsState()
    
    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        // Voice recording button
        VoiceRecordingButton(
            isRecording = uiState.isRecording,
            onStartRecording = { viewModel.startRecording() },
            onStopRecording = { viewModel.stopRecording() }
        )
        
        // Text input alternative
        TextField(
            value = uiState.textInput,
            onValueChange = { viewModel.updateTextInput(it) },
            label = { Text("Or type symptoms here") },
            modifier = Modifier.fillMaxWidth()
        )
        
        // Submit button
        Button(
            onClick = { viewModel.submitInput() },
            enabled = !uiState.isProcessing
        ) {
            Text("Analyze Symptoms")
        }
        
        // Results display
        if (uiState.result != null) {
            ResultCard(result = uiState.result)
        }
    }
}

@Composable
fun ResultCard(result: PredictionResult) {
    Card(modifier = Modifier.fillMaxWidth().padding(8.dp)) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = "Severity: ${result.severityScore}/10",
                style = MaterialTheme.typography.headlineMedium,
                color = getSeverityColor(result.severityScore)
            )
            
            Text("Detected Language: ${result.language}")
            
            Text("Symptoms Detected:", fontWeight = FontWeight.Bold)
            result.symptoms.forEach { symptom ->
                Text("  • ${symptom.name} (${symptom.confidence}%)")
            }
            
            Text(
                text = result.recommendation,
                modifier = Modifier.padding(top = 8.dp),
                style = MaterialTheme.typography.bodyLarge
            )
        }
    }
}
```

#### Offline-First Architecture

**Strategy**: 
1. Package all models in APK assets (~750MB app size)
2. Use TensorFlow Lite for model inference
3. SQLite for local data storage
4. Sync to cloud when internet available (optional)

**Model Conversion**:
```bash
# Convert PyTorch Whisper → TFLite
python -m transformers.convert_graph_to_onnx whisper-small whisper.onnx
python -m tf2onnx.convert --opset 13 whisper.onnx whisper.tflite --quantize int8

# Convert BERT → TFLite
python convert_bert_to_tflite.py --quantize --optimize
```

---

### Module 4: Windows Desktop Application (Team Member Responsibility)

**Objective**: Clinic-based desktop application with patient record management.

#### Technology Stack

**Framework**: **Electron + React + TypeScript**

**Why Electron?**
- Cross-platform (Windows, macOS, Linux)
- Modern web technologies (React)
- Large ecosystem (npm packages)
- Easy to integrate Python ML models (via Python subprocess)

**Alternative**: **WPF (.NET)** if Windows-only

#### Core Features

##### 1. Main Application Structure
```typescript
// Main Process (Node.js)
import { app, BrowserWindow, ipcMain } from 'electron';
import { PythonShell } from 'python-shell';

class DesktopApp {
  private mainWindow: BrowserWindow;
  private pythonProcess: PythonShell;
  
  constructor() {
    this.createWindow();
    this.initializePythonBackend();
    this.setupIPC();
  }
  
  private initializePythonBackend() {
    // Launch bundled Python environment with ML models
    this.pythonProcess = new PythonShell('ml_backend.py', {
      mode: 'json',
      pythonPath: './python_env/python.exe',
      scriptPath: './ml_models/'
    });
  }
  
  private setupIPC() {
    // Handle renderer process requests
    ipcMain.handle('process-audio', async (event, audioPath) => {
      return await this.processAudioFile(audioPath);
    });
    
    ipcMain.handle('process-text', async (event, text) => {
      return await this.processTextInput(text);
    });
  }
  
  private async processAudioFile(audioPath: string): Promise<PredictionResult> {
    return new Promise((resolve, reject) => {
      this.pythonProcess.send({
        action: 'transcribe_and_predict',
        audioPath: audioPath
      });
      
      this.pythonProcess.once('message', (result) => {
        resolve(result);
      });
    });
  }
}
```

##### 2. React UI Components
```typescript
// Renderer Process (React)
import React, { useState } from 'react';
import { ipcRenderer } from 'electron';

interface ClinicalDashboardProps {
  patientId: string;
}

const ClinicalDashboard: React.FC<ClinicalDashboardProps> = ({ patientId }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [result, setResult] = useState<PredictionResult | null>(null);
  const [loading, setLoading] = useState(false);
  
  const handleVoiceInput = async () => {
    setIsRecording(true);
    const audioPath = await startRecording();
    setIsRecording(false);
    
    setLoading(true);
    const prediction = await ipcRenderer.invoke('process-audio', audioPath);
    setResult(prediction);
    setLoading(false);
  };
  
  const handleTextSubmit = async (text: string) => {
    setLoading(true);
    const prediction = await ipcRenderer.invoke('process-text', text);
    setResult(prediction);
    setLoading(false);
  };
  
  return (
    <div className="clinical-dashboard">
      <PatientInfoPanel patientId={patientId} />
      
      <InputPanel
        onVoiceInput={handleVoiceInput}
        onTextSubmit={handleTextSubmit}
        isRecording={isRecording}
      />
      
      {loading && <LoadingSpinner />}
      
      {result && (
        <ResultsPanel
          severity={result.severityScore}
          symptoms={result.symptoms}
          recommendation={result.recommendation}
          onSave={() => saveToPatientRecord(patientId, result)}
        />
      )}
      
      <PatientHistoryPanel patientId={patientId} />
    </div>
  );
};
```

##### 3. Patient Record Management
```typescript
import Database from 'better-sqlite3';

class PatientDatabase {
  private db: Database.Database;
  
  constructor(dbPath: string) {
    this.db = new Database(dbPath);
    this.initializeTables();
  }
  
  private initializeTables() {
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS patients (
        patient_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        age INTEGER,
        created_at INTEGER
      );
      
      CREATE TABLE IF NOT EXISTS consultations (
        consultation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT,
        timestamp INTEGER,
        input_text TEXT,
        detected_language TEXT,
        symptoms_json TEXT,
        severity_score INTEGER,
        recommendation TEXT,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
      );
    `);
  }
  
  public saveConsultation(data: ConsultationData) {
    const stmt = this.db.prepare(`
      INSERT INTO consultations 
      (patient_id, timestamp, input_text, detected_language, 
       symptoms_json, severity_score, recommendation)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `);
    
    stmt.run(
      data.patientId,
      Date.now(),
      data.inputText,
      data.language,
      JSON.stringify(data.symptoms),
      data.severityScore,
      data.recommendation
    );
  }
  
  public getPatientHistory(patientId: string): Consultation[] {
    const stmt = this.db.prepare(`
      SELECT * FROM consultations 
      WHERE patient_id = ? 
      ORDER BY timestamp DESC
    `);
    
    return stmt.all(patientId);
  }
}
```

##### 4. Offline Model Integration
```python
# ml_backend.py (Python subprocess)
import sys
import json
from main import run_pipeline
from ml_ensemble import SeverityPredictor

whisper_model = None
nlp_pipeline = None
ml_predictor = None

def initialize_models():
    global whisper_model, nlp_pipeline, ml_predictor
    # Load models once at startup
    whisper_model = load_whisper_model('models/whisper_small_quantized.bin')
    nlp_pipeline = load_nlp_pipeline('models/nlp_pipeline/')
    ml_predictor = SeverityPredictor.load('models/ensemble_quantized.pkl')

def process_request(request):
    action = request['action']
    
    if action == 'transcribe_and_predict':
        # Step 1: Transcribe audio
        audio_path = request['audioPath']
        transcription = whisper_model.transcribe(audio_path)
        
        # Step 2: NLP processing
        nlp_output = run_pipeline(transcription['text'])
        
        # Step 3: ML prediction
        prediction = ml_predictor.predict(nlp_output['features_for_ml'])
        
        return {
            'transcription': transcription['text'],
            'language': nlp_output['detected_language'],
            'symptoms': nlp_output['symptoms_present'],
            'severityScore': prediction['severity_score'],
            'recommendation': prediction['recommendation']
        }
    
    elif action == 'process_text':
        text = request['text']
        nlp_output = run_pipeline(text)
        prediction = ml_predictor.predict(nlp_output['features_for_ml'])
        
        return {
            'symptoms': nlp_output['symptoms_present'],
            'severityScore': prediction['severity_score'],
            'recommendation': prediction['recommendation']
        }

if __name__ == '__main__':
    initialize_models()
    
    # Listen for JSON requests on stdin
    for line in sys.stdin:
        try:
            request = json.loads(line)
            result = process_request(request)
            print(json.dumps(result))
            sys.stdout.flush()
        except Exception as e:
            print(json.dumps({'error': str(e)}))
            sys.stdout.flush()
```

#### Packaging for Windows

```json
{
  "name": "adaptive-clinical-assistant",
  "version": "1.0.0",
  "main": "dist/main.js",
  "build": {
    "appId": "com.healthcare.clinical-assistant",
    "productName": "Adaptive Clinical Assistant",
    "directories": {
      "output": "release"
    },
    "files": [
      "dist/**/*",
      "python_env/**/*",
      "ml_models/**/*"
    ],
    "win": {
      "target": "nsis",
      "icon": "assets/icon.ico"
    },
    "extraResources": [
      {
        "from": "python_env/",
        "to": "python_env/",
        "filter": ["**/*"]
      },
      {
        "from": "ml_models/",
        "to": "ml_models/",
        "filter": ["**/*"]
      }
    ]
  }
}
```

**Build Process**:
```bash
# 1. Bundle Python environment
pip install pyinstaller
pyinstaller --onedir --add-data "models:models" ml_backend.py

# 2. Build Electron app
npm run build
electron-builder --win

# Result: Installer (~1.2GB including Python + models)
```

---

# NLP Module Proposal for Adaptive Clinical Assistant

## Overview
The NLP module is the backbone of the Adaptive Clinical Assistant, designed to process multilingual user input, extract medical symptoms, and prepare structured data for severity prediction. This module supports both English and Kriol, ensuring accessibility for Indigenous Australian communities. It integrates advanced natural language processing techniques with rule-based methods to achieve high accuracy while maintaining offline functionality.

## Voice Processing
The voice processing subsystem uses OpenAI Whisper, a state-of-the-art speech-to-text model, to transcribe user speech into text. Whisper is chosen for its multilingual capabilities, robustness to accents, and ability to operate offline. The model is fine-tuned with medical vocabulary and Kriol-specific prompts to improve transcription accuracy. This ensures that both English and Kriol inputs are accurately converted into text for further processing.

## Language Detection
To handle bilingual input, a language detection subsystem identifies whether the text is in English, Kriol, or a mix of both. This is achieved using a TF-IDF (Term Frequency-Inverse Document Frequency) classifier, which analyzes character-level patterns unique to each language. The lightweight model ensures fast and accurate detection, enabling the system to route Kriol text to the translation engine while processing English text directly.

## Translation Engine
For Kriol inputs, the translation engine converts text into English using a hybrid approach. A dictionary-based method handles common words and phrases, while a MarianMT Transformer model provides context-aware translations for more complex sentences. This combination ensures both speed and accuracy, with the dictionary offering deterministic results and the Transformer handling grammatical nuances and unseen words.

## Text Preprocessing
Once the input is in English, the text preprocessing subsystem cleans and normalizes it. This includes expanding contractions (e.g., "don’t" to "do not"), correcting spelling errors using fuzzy matching, and normalizing punctuation. These steps ensure that the text is standardized for downstream processing, reducing errors in symptom extraction and negation detection.

## Symptom Extraction
The symptom extraction subsystem identifies medical symptoms mentioned in the text. It uses BioClinicalBERT, a pre-trained language model fine-tuned on clinical data, to recognize symptoms with high accuracy. As a backup, spaCy’s PhraseMatcher is employed to detect exact matches for known symptom phrases. The ensemble approach combines the strengths of both methods, ensuring high recall and precision even for variations in symptom descriptions.

## Negation Detection
To determine whether symptoms are present or negated, the negation detection subsystem uses a hybrid approach. A rule-based method quickly identifies simple negation patterns (e.g., "no fever"), while a Bi-LSTM (Bidirectional Long Short-Term Memory) model handles more complex contexts (e.g., "I don’t have fever but I do have a headache"). This ensures accurate classification of symptoms as present or negated, even in linguistically challenging sentences.

## Feature Engineering
The final step in the NLP module is feature engineering, where structured data is generated for the ML severity prediction module. This includes counts of symptoms, weighted severity scores based on medical knowledge, and embeddings generated by BERT for semantic understanding. These features provide a comprehensive representation of the input, enabling the ML module to make accurate severity predictions.

## Offline Capability
All components of the NLP module are optimized for offline use. Models are quantized to reduce size without significant loss of accuracy, and lightweight methods like TF-IDF and dictionary-based translation ensure fast processing. This design ensures that the system can operate effectively in remote areas with limited connectivity.

## Conclusion
The NLP module combines cutting-edge AI techniques with practical optimizations to deliver a robust, multilingual processing pipeline. By integrating voice processing, language detection, translation, symptom extraction, and negation detection, it ensures accurate and culturally appropriate medical triage for diverse user groups. This module is a critical enabler of the Adaptive Clinical Assistant’s mission to provide accessible healthcare support in resource-constrained settings.