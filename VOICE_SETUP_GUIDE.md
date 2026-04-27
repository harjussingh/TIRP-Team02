# Voice Integration Setup Guide

## Phase 1: English Speech-to-Text (Current)

We've implemented voice input using OpenAI Whisper for English transcription.

---

## Installation Steps

### 1. Install Dependencies

```bash
# Activate your virtual environment first
source .venv/bin/activate

# Install Whisper and audio processing libraries
pip install -r requirements.txt
```

**Note**: This will download ~1GB for the 'base' Whisper model on first use.

### Alternative: Install dependencies individually
```bash
pip install openai-whisper
pip install torch torchaudio
pip install pydub soundfile numpy
```

---

## Testing Voice Input

### Option 1: Record Audio on Your Phone/Computer

**On Mac:**
```bash
# Record 5 seconds of audio
sox -d test_audio.wav trim 0 5
```

**On iPhone/Android:**
- Use voice recorder app
- Say: "I have a headache and fever"
- Export/share the audio file to your computer

### Option 2: Use Text-to-Speech to Create Test Audio

**On Mac:**
```bash
# Create test audio file
say "I have a headache and fever" -o test_audio.aiff
```

**On Linux:**
```bash
espeak "I have a headache and fever" -w test_audio.wav
```

### Option 3: Download Sample Audio

You can use any audio file (mp3, wav, m4a, etc.) with spoken English.

---

## Running the System

### Text Mode (Current - works as before):
```bash
python main.py
```
Then type your symptoms when prompted.

### Voice Mode (NEW):
```bash
python main.py test_audio.wav
```

Replace `test_audio.wav` with your audio file path.

---

## Example Usage

### 1. Create a test audio file (Mac):
```bash
say "I have a severe headache and I feel dizzy" -o symptoms.aiff
```

### 2. Process the audio:
```bash
python main.py symptoms.aiff
```

### Expected Output:
```
============================================================
SACA - Smart Adaptive Clinical Assistant
Symptom Extractor (with Kriol & Voice support)
============================================================

🎤 Processing voice input: symptoms.aiff
Loading Whisper model 'base'...
✓ Whisper model 'base' loaded successfully
Transcribing audio: symptoms.aiff
✓ Transcription: I have a severe headache and I feel dizzy
✓ Detected language: english

============================================================
RESULT:
============================================================
{
  "input_text": "I have a severe headache and I feel dizzy",
  "cleaned_text": "i have a severe headache and i feel dizzy",
  "mapped_text": "i have a severe headache and i feel dizziness",
  "extracted_symptoms": [
    "headache",
    "dizziness"
  ],
  "symptoms_present": [
    "headache",
    "dizziness"
  ],
  "symptoms_negated": [],
  "translated_text": "i have a severe headache and i feel dizzy",
  "input_source": "voice",
  "voice_transcription": "I have a severe headache and I feel dizzy",
  "detected_language": "english"
}
```

---

## Testing the Voice Module Directly

You can also test the voice processor independently:

```bash
python nlp/voice_processor.py test_audio.wav
```

---

## Whisper Model Options

In `nlp/voice_processor.py`, you can change the model size:

| Model | Size | RAM | Accuracy | Speed |
|-------|------|-----|----------|-------|
| tiny  | ~75MB | ~1GB | Low | Very Fast |
| base  | ~150MB | ~1GB | Good | Fast ⭐ (default) |
| small | ~500MB | ~2GB | Better | Medium |
| medium | ~1.5GB | ~5GB | High | Slow |
| large | ~3GB | ~10GB | Best | Very Slow |

To change model:
```python
# In main.py, line ~70:
processor = VoiceProcessor(model_name='small')  # Change 'base' to 'small', 'medium', etc.
```

---

## Supported Audio Formats

Whisper supports most common audio formats:
- ✅ WAV (.wav)
- ✅ MP3 (.mp3)
- ✅ M4A (.m4a)
- ✅ FLAC (.flac)
- ✅ OGG (.ogg)
- ✅ AIFF (.aiff)

---

## Troubleshooting

### Issue: "Module 'whisper' not found"
**Solution:**
```bash
pip install openai-whisper
```

### Issue: "ffmpeg not found"
**Solution (Mac):**
```bash
brew install ffmpeg
```

**Solution (Ubuntu/Linux):**
```bash
sudo apt-get install ffmpeg
```

**Solution (Windows):**
Download from https://ffmpeg.org/download.html

### Issue: Slow transcription
**Solutions:**
1. Use smaller model: `VoiceProcessor(model_name='tiny')`
2. Use GPU (requires CUDA): Install `torch` with GPU support
3. Reduce audio length (clip to relevant parts)

### Issue: Poor accuracy
**Solutions:**
1. Use larger model: `VoiceProcessor(model_name='small')`
2. Ensure audio quality is good (clear speech, minimal background noise)
3. Speak clearly and at moderate pace

---

## Next Steps (Phase 2)

Phase 2 will add Kriol language detection:

1. ✅ Keyword-based detection (check for 'mi', 'garr', etc.)
2. ✅ Dictionary-based scoring
3. ✅ Confidence scoring
4. ✅ Manual language override option

Coming soon!

---

## File Structure

```
nlp/
├── voice_processor.py      ← NEW: Voice-to-text module
├── kriol_translator.py     ← Existing: Kriol translation
├── preprocess.py           ← Existing: Text preprocessing
├── symptom_extractor.py    ← Existing: Symptom extraction
└── negation_detector.py    ← Existing: Negation detection

main.py                     ← Updated: Added voice support
requirements.txt            ← Updated: Added Whisper dependencies
```

---

## API Integration (Future)

For mobile app integration, you'll create an API endpoint:

```python
# api/endpoints.py (future)
from fastapi import FastAPI, UploadFile

@app.post("/voice/submit")
async def submit_voice(audio: UploadFile):
    # Save audio
    audio_path = save_uploaded_file(audio)
    
    # Process
    result = process_voice_input(audio_path)
    
    return result
```

Mobile app will:
1. Record audio
2. Upload to API
3. Receive transcription + symptoms + severity

---

## Performance Notes

**First run**: Slower (downloads model, ~1GB)
**Subsequent runs**: Fast (model cached)

**Processing time (base model, CPU):**
- 10 seconds audio: ~5-10 seconds
- 30 seconds audio: ~15-20 seconds
- 60 seconds audio: ~30-40 seconds

**With GPU:**
- 10 seconds audio: ~1-2 seconds
- Real-time or faster!

---

## Testing Checklist

- [ ] Install dependencies successfully
- [ ] Create test audio file
- [ ] Run voice mode: `python main.py test_audio.wav`
- [ ] Verify transcription is correct
- [ ] Verify symptoms are extracted
- [ ] Test with different audio files
- [ ] Test text mode still works: `python main.py`

---

## Questions?

If you encounter issues, check:
1. Virtual environment is activated
2. Dependencies are installed
3. Audio file exists and is readable
4. Audio contains clear English speech
5. ffmpeg is installed (required by Whisper)
