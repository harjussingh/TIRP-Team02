# Kriol Language Support - Testing Examples

## System Pipeline

```
User Input (Kriol or English)
        ↓
Kriol-to-English Translation
        ↓
Text Preprocessing (expand contractions, spell correction)
        ↓
Synonym Mapping
        ↓
Symptom Extraction
        ↓
Negation Detection
        ↓
Structured Result
```

## Test Cases

### Test 1: Basic Kriol with Negation
**Input (Kriol):** `mi no garr hedache bat mi garr hot bodi`

**Translation:** `i not have a headache but i have a fever`

**Result:**
- Headache → NEGATED ✅
- Fever → PRESENT ✅

---

### Test 2: Simple Kriol Symptoms
**Input (Kriol):** `mi garr kof en fiwa`

**Translation:** `i have a cough and fever`

**Result:**
- Cough → PRESENT ✅
- Fever → PRESENT ✅

---

### Test 3: Multiple Symptoms with Negation
**Input (Kriol):** `mi no garr kof bat mi garr sowa trot`

**Translation:** `i not have a cough but i have sore throat`

**Result:**
- Cough → NEGATED ✅
- Sore throat → PRESENT ✅

---

### Test 4: Belly Pain and Dizziness
**Input (Kriol):** `mi garr beli pein en disi`

**Translation:** `i have belly pain and dizzy`

**Result:**
- Abdominal pain → PRESENT ✅
- Dizziness → PRESENT ✅

---

### Test 5: English Input (Backward Compatible)
**Input (English):** `i have a headache and fever`

**Result:**
- Headache → PRESENT ✅
- Fever → PRESENT ✅

---

## Kriol Dictionary Coverage

The system currently supports:

### Pronouns
- `mi` → I
- `yu` → you
- `wi` → we
- `dei` → they

### Verbs
- `garr/gat` → have
- `fel/feld` → feel/felt
- `slip` → sleep

### Negation
- `no` → not
- `nomo` → no more
- `nating` → nothing

### Medical Symptoms
- `hedache/hedake` → headache
- `kof/koff` → cough
- `fiwa/fiva` → fever
- `hot-bodi/hotbodi` → fever
- `disi/gidibat` → dizzy
- `beli/beliak` → belly/stomach
- `pein/pen` → pain
- `sowa trot` → sore throat
- `traubul bret` → trouble breathing
- `spew/chak-ap` → vomit

### Conjunctions
- `bat` → but
- `en` → and
- `o` → or
- `bikaj/bikos` → because

---

## How to Expand the Dictionary

To add more Kriol words, edit:
```
data/kriol_dictionary.json
```

Add entries in the appropriate category:
```json
{
  "medical_symptoms": {
    "new_kriol_word": "english_translation"
  }
}
```

The system will automatically:
1. Use the new word in translation
2. Apply fuzzy matching for spelling variations
3. Map to symptoms via the existing pipeline

---

## Notes

- The system handles spelling variations automatically using fuzzy matching (85% similarity threshold)
- Both Kriol and English inputs work seamlessly
- Negation detection works in both languages after translation
- The translation doesn't need to be grammatically perfect - just good enough for symptom extraction
