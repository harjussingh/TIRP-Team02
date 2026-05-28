# NLP Translation Flow Documentation

## How Kriol Translation Works in the System

### Overview
The system displays the **original Kriol text** to the user, then the **NLP pipeline automatically translates it** during processing. This provides transparency while maintaining automatic translation.

---

## Complete Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                   USER SPEAKS KRIOL                              │
│            "mi garr hedache bat mi no garr kof"                  │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                  WHISPER TRANSCRIPTION                           │
│   Uses bilingual prompt (English base + Kriol vocabulary)       │
│   Result: "mi garr hedache bat mi no garr kof"                  │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│               LANGUAGE DETECTION (voice_processor.py)            │
│   Analyzes keywords: mi, garr, bat, hedache, kof                │
│   Result: "kriol" detected                                       │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                    GUI DISPLAY                                   │
│   Text Input Field: "mi garr hedache bat mi no garr kof"        │
│   Status Bar: "Detected: Kriol"                                 │
│   [Shows ORIGINAL Kriol text as-is]                             │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼ User clicks Submit or auto-submit
┌──────────────────────────────────────────────────────────────────┐
│                   NLP PIPELINE START (main.py)                   │
│   Input: "mi garr hedache bat mi no garr kof"                   │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│   STEP 0: KRIOL-TO-ENGLISH TRANSLATION (kriol_translator.py)    │
│                                                                  │
│   1. Tokenize: ["mi", "garr", "hedache", "bat", "mi", "no",    │
│                 "garr", "kof"]                                   │
│                                                                  │
│   2. Dictionary Lookup:                                          │
│      mi      → i                                                 │
│      garr    → have                                              │
│      hedache → headache                                          │
│      bat     → but                                               │
│      no      → not                                               │
│      kof     → cough                                             │
│                                                                  │
│   3. Reconstruct: "i have headache but i not have cough"        │
│                                                                  │
│   4. Post-process: "i have a headache but i not have cough"     │
│                                                                  │
│   Result: "i have a headache but i not have cough"              │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│          STEP 1: PREPROCESSING (preprocess.py)                   │
│                                                                  │
│   1. Expand contractions: (none in this case)                   │
│   2. Remove punctuation                                          │
│   3. Normalize spaces                                            │
│   4. Spell correction using fuzzy matching                       │
│                                                                  │
│   Result: "i have a headache but i do not have cough"           │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│          STEP 2: SYNONYM MAPPING (symptom_mapper.py)             │
│                                                                  │
│   Check synonyms dictionary:                                     │
│   - "headache" → already standard                                │
│   - "cough" → already standard                                   │
│                                                                  │
│   Result: "i have a headache but i do not have cough"           │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│      STEP 3: SYMPTOM EXTRACTION (symptom_extractor.py)           │
│                                                                  │
│   Pattern matching against symptoms list:                        │
│   - "headache" → FOUND                                           │
│   - "cough" → FOUND                                              │
│                                                                  │
│   Result: ["headache", "cough"]                                  │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│      STEP 4: NEGATION DETECTION (negation_detector.py)           │
│                                                                  │
│   Analyze: "i have a headache but i do not have cough"          │
│                                                                  │
│   For "headache":                                                │
│   - Check 6-word window: "i have a headache but i"              │
│   - Negation words: none                                         │
│   - Result: PRESENT                                              │
│                                                                  │
│   For "cough":                                                   │
│   - Check 6-word window: "but i do not have cough"              │
│   - Negation pattern: "do not have" → FOUND                      │
│   - Result: NEGATED                                              │
│                                                                  │
│   Result: present=["headache"], negated=["cough"]                │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                    FINAL RESULT                                  │
│                                                                  │
│   {                                                              │
│     "input_text": "mi garr hedache bat mi no garr kof",         │
│     "translated_text": "i have a headache but i not have cough",│
│     "cleaned_text": "i have a headache but i do not have cough",│
│     "extracted_symptoms": ["headache", "cough"],                 │
│     "symptoms_present": ["headache"],                            │
│     "symptoms_negated": ["cough"],                               │
│     "input_source": "voice"                                      │
│   }                                                              │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                   GUI RESULTS DISPLAY                            │
│                                                                  │
│   Input Type: Voice                                              │
│   Original Input: "mi garr hedache bat mi no garr kof"          │
│   Translated Text: "i have a headache but i not have cough"     │
│                                                                  │
│   Symptoms Present:                                              │
│     • headache                                                   │
│                                                                  │
│   Symptoms Negated:                                              │
│     • cough                                                      │
└──────────────────────────────────────────────────────────────────┘
```

---

## Code Flow

### 1. Voice Recording (gui.py)
```python
def process_voice_input(self):
    # Transcribe with Whisper
    result = self.voice_processor.transcribe_bilingual(audio_file)
    
    original_text = result['original_text']  # "mi garr hedache..."
    detected_lang = result['detected_language']  # "kriol"
    
    # Display ORIGINAL Kriol text in input field
    self.text_input.insert("1.0", original_text)
    
    # Show detected language
    self.update_status(f"Detected: {detected_lang}")
    
    # Submit for processing
    self.submit_input()
```

### 2. Submit Processing (gui.py)
```python
def submit_input(self):
    user_input = self.text_input.get("1.0", tk.END).strip()
    # user_input = "mi garr hedache bat mi no garr kof"
    
    # Call NLP pipeline
    result = self.run_pipeline(user_input, source="voice")
    
    # Display results
    self.display_results(result)
```

### 3. NLP Pipeline (main.py)
```python
def run_pipeline(user_input: str, source: str = "text") -> dict:
    kriol_dict = load_kriol_dictionary("data/kriol_dictionary.json")
    
    # STEP 0: Kriol to English translation
    english_text = translate_kriol_to_english(user_input, kriol_dict)
    # Input: "mi garr hedache bat mi no garr kof"
    # Output: "i have headache but i not have cough"
    
    english_text = post_process_translation(english_text)
    # Output: "i have a headache but i not have cough"
    
    # STEP 1: Preprocessing
    cleaned_text = clean_text(english_text, known_words=known_words)
    # Output: "i have a headache but i do not have cough"
    
    # STEP 2: Synonym mapping
    mapped_text = map_synonyms(cleaned_text, synonyms)
    # Output: "i have a headache but i do not have cough"
    
    # STEP 3: Symptom extraction
    extracted_symptoms = extractor.extract_symptoms(mapped_text)
    # Output: ["headache", "cough"]
    
    # STEP 4: Negation detection
    present, negated = detect_negations(mapped_text, extracted_symptoms)
    # Output: present=["headache"], negated=["cough"]
    
    # Build result
    result = build_result(
        input_text=user_input,  # Original Kriol
        cleaned_text=cleaned_text,
        mapped_text=mapped_text,
        extracted_symptoms=extracted_symptoms,
        present=present,
        negated=negated
    )
    
    result["translated_text"] = english_text
    result["input_source"] = source
    
    return result
```

### 4. Kriol Translation (nlp/kriol_translator.py)
```python
def translate_kriol_to_english(text: str, dictionary: Dict[str, str]) -> str:
    # Tokenize
    tokens = tokenize_kriol(text)
    # ["mi", "garr", "hedache", "bat", "mi", "no", "garr", "kof"]
    
    english_tokens = []
    for token in tokens:
        # Look up in dictionary
        if token in dictionary:
            english_tokens.append(dictionary[token])
        else:
            english_tokens.append(token)
    
    # Reconstruct
    return " ".join(english_tokens)
    # "i have headache but i not have cough"


def post_process_translation(text: str) -> str:
    # Add articles
    text = re.sub(r'\bhave\s+(headache|cough|fever)\b', r'have a \1', text)
    # "i have a headache but i not have cough"
    
    return text
```

---

## Key Points

### ✅ What Happens Now:

1. **Voice transcription** → Original Kriol text: "mi garr hedache bat mi no garr kof"
2. **Display in GUI** → Shows: "mi garr hedache bat mi no garr kof" (as-is)
3. **User clicks Submit** (or auto-submit)
4. **NLP Pipeline translates** → "i have a headache but i not have cough"
5. **Symptom extraction** → Works on English text
6. **Results show both** → Original Kriol + Translated English

### 📍 Where Translation Happens:

**File:** `main.py` → `run_pipeline()` function  
**Line:** Step 0 (first step of pipeline)  
**Functions:**
- `translate_kriol_to_english()` - Word-by-word dictionary lookup
- `post_process_translation()` - Grammar fixes

### 🔄 Translation Method:

**Type:** Dictionary-based word substitution  
**Dictionary:** `data/kriol_dictionary.json` (110+ words)  
**Approach:**
1. Tokenize Kriol text into words
2. Look up each word in dictionary
3. Replace with English equivalent
4. Reconstruct sentence
5. Apply grammar rules (add articles, fix patterns)

---

## Testing the Flow

### Test Script:
```python
from main import run_pipeline

# Kriol input
kriol_text = "mi garr hedache bat mi no garr kof"

# Run through NLP pipeline
result = run_pipeline(kriol_text, source="text")

print(f"Original (Kriol): {result['input_text']}")
print(f"Translated: {result['translated_text']}")
print(f"Cleaned: {result['cleaned_text']}")
print(f"Symptoms Present: {result['symptoms_present']}")
print(f"Symptoms Negated: {result['symptoms_negated']}")
```

### Expected Output:
```
Original (Kriol): mi garr hedache bat mi no garr kof
Translated: i have a headache but i not have cough
Cleaned: i have a headache but i do not have cough
Symptoms Present: ['headache']
Symptoms Negated: ['cough']
```

---

## Summary

✅ **GUI displays original Kriol text** (no pre-translation)  
✅ **NLP pipeline handles translation** automatically in Step 0  
✅ **Translation method**: Dictionary-based word substitution  
✅ **Results show both**: Original Kriol + Translated English  
✅ **User sees transparency**: Original input preserved  

The system now shows users their exact Kriol input while seamlessly translating it behind the scenes for medical analysis!
