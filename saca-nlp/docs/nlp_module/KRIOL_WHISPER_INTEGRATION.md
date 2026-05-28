# Kriol Language Integration with Whisper

## Overview
This document explains how Kriol language support has been embedded into the Whisper speech-to-text system for the Smart Adaptive Clinical Assistant (SACA).

---

## The Challenge

**Problem:** OpenAI Whisper does not natively support Kriol (Australian Aboriginal English-based creole language).

**Solution:** Hybrid approach combining:
1. Phonetic similarity to English (Kriol is English-based)
2. Bilingual vocabulary prompting
3. Post-transcription language detection
4. Automatic Kriol-to-English translation

---

## How It Works

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUDIO INPUT (Kriol or English)               │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│         WHISPER TRANSCRIPTION (English base language)           │
│      + Bilingual Prompt (English + Kriol vocabulary hints)      │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LANGUAGE DETECTION                           │
│         Analyze keywords & patterns → "English" or "Kriol"      │
└───────────────┬──────────────────────────────┬──────────────────┘
                │                              │
        ┌───────▼────────┐            ┌────────▼─────────┐
        │   IF ENGLISH   │            │    IF KRIOL      │
        │   Pass through │            │   Translate to   │
        │                │            │     English      │
        └───────┬────────┘            └────────┬─────────┘
                │                              │
                └──────────────┬───────────────┘
                               ▼
                ┌──────────────────────────────┐
                │  MEDICAL ERROR CORRECTION    │
                │  (feeding→feeling, etc.)     │
                └──────────────┬───────────────┘
                               ▼
                ┌──────────────────────────────┐
                │    SYMPTOM EXTRACTION        │
                └──────────────────────────────┘
```

---

## Technical Implementation

### 1. Bilingual Vocabulary Prompting

Whisper's `initial_prompt` parameter accepts text that guides the language model toward expected vocabulary.

**Medical Prompt (English):**
```python
"Medical symptoms: fever, cough, headache, stomach pain, throat pain, 
nausea, vomiting, diarrhea, dizziness, chest pain, shortness of breath, 
abdominal pain, sore throat, feeling unwell."
```

**Kriol Prompt:**
```python
"Kriol medical words: mi garr hedache, mi garr hot-bodi, mi garr kof, 
mi garr sik-bodi, mi garr pein, belly-pein, throat-pein, mi fel sik, 
mi fel bad, mi no garr, bat, en, o, nomo, bin, gat, fel."
```

**Combined Bilingual Prompt:**
```python
bilingual_prompt = f"{medical_prompt} {kriol_prompt}"
```

This tells Whisper to expect both English medical terms AND Kriol words in the audio.

### 2. Transcription with English Base

Kriol is an English-based creole, meaning its phonetics are similar to English. We use English as the base language:

```python
result = model.transcribe(
    audio_path,
    language='en',  # Use English phonetic recognition
    initial_prompt=bilingual_prompt,  # Add Kriol vocabulary hints
    temperature=0.0,
    # ... other optimizations
)
```

### 3. Language Detection Algorithm

After transcription, we analyze the text to determine if it's Kriol or English:

```python
def _detect_language(text: str) -> str:
    # Count Kriol-specific keywords
    kriol_keywords = {
        'mi', 'garr', 'gat', 'bat', 'bikaj', 'bikos', 'bin',
        'hedache', 'hot-bodi', 'kof', 'sik-bodi', 'pein',
        'nomo', 'nating', 'neba', 'yu', 'dei', 'yumi'
    }
    
    kriol_word_count = sum(1 for word in words if word in kriol_keywords)
    kriol_ratio = kriol_word_count / total_words
    
    # If >15% Kriol words, classify as Kriol
    if kriol_ratio > 0.15:
        return 'kriol'
    
    # Check for common Kriol patterns
    kriol_patterns = ['mi garr', 'mi gat', 'mi fel', 'no garr', 'bat mi']
    if any(pattern in text for pattern in kriol_patterns):
        return 'kriol'
    
    return 'english'
```

**Detection Accuracy:** 100% on test cases (8/8)

### 4. Automatic Translation

If Kriol is detected, the system automatically translates to English using the Kriol dictionary:

```python
if detected_lang == 'kriol':
    from nlp.kriol_translator import translate_kriol_to_english
    translated_text = translate_kriol_to_english(original_text, kriol_dict)
```

**Dictionary Size:** 110 Kriol-to-English word mappings

---

## Usage Examples

### Example 1: English Input

**Audio:** "I have a headache and fever"
- **Transcription:** "I have a headache and fever"
- **Detected Language:** English
- **Translation:** None (already English)
- **Symptoms:** headache, fever

### Example 2: Kriol Input

**Audio:** "mi garr hedache en hot-bodi"
- **Transcription:** "mi garr hedache en hot-bodi"
- **Detected Language:** Kriol ✓
- **Translation:** "i have headache and fever"
- **Symptoms:** headache, fever

### Example 3: Kriol with Negation

**Audio:** "mi garr hedache bat mi no garr kof"
- **Transcription:** "mi garr hedache bat mi no garr kof"
- **Detected Language:** Kriol ✓
- **Translation:** "i have headache but i not have cough"
- **Post-processing:** "i have headache but i do not have cough"
- **Symptoms Present:** headache
- **Symptoms Negated:** cough

---

## API Reference

### VoiceProcessor Class

#### `transcribe_bilingual(audio_path: str) -> dict`

Transcribe audio with automatic language detection and translation.

**Returns:**
```python
{
    'original_text': str,        # Raw transcription
    'detected_language': str,    # 'english' or 'kriol'
    'translated_text': str,      # English translation (or same if English)
    'is_translated': bool        # True if translation occurred
}
```

**Example:**
```python
processor = VoiceProcessor(model_name='small')
result = processor.transcribe_bilingual('audio.wav')

print(f"Original: {result['original_text']}")
print(f"Language: {result['detected_language']}")
print(f"English: {result['translated_text']}")
```

#### `_detect_language(text: str) -> str`

Detect if text is Kriol or English.

**Algorithm:**
1. Count Kriol-specific keywords
2. Calculate keyword ratio
3. Check for Kriol phrase patterns
4. Return 'kriol' if ratio > 15% OR patterns found

---

## GUI Integration

The GUI automatically handles bilingual input:

1. **Record Voice:** Click "🎤 Record Voice" button
2. **Automatic Transcription:** Whisper transcribes with bilingual prompt
3. **Language Detection:** System detects Kriol or English
4. **Status Display:** Shows detected language in status bar
   - "Detected: Kriol | Translated to English" (if Kriol)
   - "Detected: English" (if English)
5. **Display:** Text input shows translated English version
6. **Processing:** Symptoms extracted from English text

---

## Command Line Usage

```bash
# Process English audio
python main.py audio_english.wav

# Process Kriol audio (automatic detection + translation)
python main.py audio_kriol.wav
```

**Output:**
```
🎤 Processing voice input: audio_kriol.wav
Loading Whisper model 'small'...
✓ Whisper model 'small' loaded successfully
✓ Kriol dictionary loaded
Transcribing audio: audio_kriol.wav
✓ Detected language: kriol
✓ Transcription: mi garr hedache en hot-bodi bat mi no garr kof
✓ Translated from Kriol: i have headache and fever but i do not have cough

Result:
{
  "voice_transcription_original": "mi garr hedache en hot-bodi bat mi no garr kof",
  "voice_transcription_translated": "i have headache and fever but i do not have cough",
  "detected_language": "kriol",
  "was_translated": true,
  "symptoms_present": ["headache", "fever"],
  "symptoms_negated": ["cough"]
}
```

---

## Kriol Dictionary

The system uses a comprehensive Kriol-to-English dictionary with 110+ words:

### Categories:

| Category | Examples |
|----------|----------|
| **Pronouns** | mi→i, yu→you, dei→they, yumi→we |
| **Verbs** | garr→have, gat→have, fel→feel, bin→was |
| **Negation** | no→not, nomo→no more, nating→nothing |
| **Conjunctions** | bat→but, en→and, o→or, bikaj→because |
| **Medical Symptoms** | hedache→headache, hot-bodi→fever, kof→cough, pein→pain |
| **Body Parts** | belly→stomach, throat→throat, hed→head |
| **Intensifiers** | lil-bit→little, bigwan→very, tumas→too much |

**Dictionary Location:** `data/kriol_dictionary.json`

---

## Testing

### Run Tests:
```bash
python test_kriol_whisper.py
```

### Test Results:
```
Language Detection Tests: 8/8 (100.0% accuracy)

Test Cases:
✓ "I have a headache and fever" → english
✓ "mi garr hedache en hot-bodi" → kriol
✓ "mi fel sik bat mi no garr kof" → kriol
✓ "I am feeling pain in my stomach" → english
✓ "mi garr pein long mi belly" → kriol
✓ "yu garr fever or what" → kriol
✓ "do you have a cough" → english
✓ "mi no garr no sik-bodi nomo" → kriol
```

---

## Limitations & Future Improvements

### Current Limitations:

1. **Accent Variations:** Kriol has regional dialects that may not be in the dictionary
2. **Complex Phrases:** Multi-word expressions may not translate perfectly
3. **Code-Switching:** Mixed Kriol-English sentences may confuse detection
4. **Homonyms:** Some Kriol words sound like English but mean different things

### Planned Improvements (Phase 2):

1. **Fine-tuning Whisper:**
   - Train on Kriol audio dataset
   - Improve phonetic recognition for Kriol-specific sounds

2. **Enhanced Dictionary:**
   - Add regional variations
   - Include contextual translations
   - Support compound words

3. **Confidence Scores:**
   - Show confidence for language detection
   - Allow user to override detection

4. **Real-time Correction:**
   - Let users correct misrecognitions
   - Learn from corrections to improve dictionary

---

## Technical Details

### Files Modified:

1. **`nlp/voice_processor.py`**
   - Added `kriol_prompt` attribute
   - Added `_load_kriol_dictionary()` method
   - Added `_detect_language()` method
   - Added `transcribe_bilingual()` method
   - Updated `transcribe_audio()` to use bilingual prompt

2. **`main.py`**
   - Updated `process_voice_input()` to use bilingual transcription
   - Added language detection info to results

3. **`gui.py`**
   - Updated `process_voice_input()` to show detected language
   - Display translated text in text input field

4. **`data/kriol_dictionary.json`**
   - Already exists with 110+ word mappings

### Dependencies:

- **openai-whisper:** Speech recognition
- **torch:** Deep learning framework
- **difflib:** Fuzzy matching for spell correction
- **re:** Regex for pattern matching

---

## Summary

✅ **Kriol support embedded** into Whisper via:
- Bilingual vocabulary prompting
- English base language (phonetic similarity)
- Post-transcription language detection (100% accuracy)
- Automatic Kriol-to-English translation

✅ **Seamless user experience:**
- Speak in Kriol or English
- System auto-detects language
- Shows detected language in UI
- Extracts symptoms from English translation

✅ **110+ Kriol words** in dictionary covering medical terminology

✅ **Fully integrated** into both GUI and CLI interfaces

The system now supports **bilingual medical conversations** without requiring users to specify their language!
