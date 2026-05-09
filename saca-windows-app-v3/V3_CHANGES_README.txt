SACA Windows App - V3 Update

Implemented in this package:
1. Pattern background image applied behind all normal app pages.
2. Emergency page stays plain clay/off-white for readability.
3. main.py now loads the stylesheet using an absolute project path.
4. main_window.py now uses a PatternBackgroundWidget instead of relying on fragile QSS background-image paths.
5. Input page mic button now records microphone audio using PySide6 QtMultimedia.
6. If Whisper is installed, the recorded audio is transcribed and added to the text box.
7. If Whisper/QtMultimedia is not available, the app gives a clear fallback message and lets the user type.

How to run:
python main.py

Optional voice transcription:
pip install -r requirements-voice.txt

Background image path:
assets/backgrounds/saca_pattern_bg.jpg


--------------------------------------------------

how to run in mac:


Use this **one-page README.md**:

````markdown
# SACA - Smart Adaptive Clinical Assistant

SACA is a desktop healthcare triage prototype for English and Kriol-style input. It supports Type, Speak, and Picture modes, then uses NLP and ML to detect symptoms, ask follow-up questions, and show a final result.

## Run on Mac

Do not run the Windows `.exe` on Mac. Run the app using Python.

### 1. Install required tools

```bash
brew install python@3.11 ffmpeg portaudio
````

### 2. Clone the project

```bash
git clone YOUR_GITHUB_REPO_LINK_HERE
cd YOUR_PROJECT_FOLDER_NAME
```

### 3. Create virtual environment

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-ml.txt
pip install -r requirements-voice.txt
```

### 5. Check model files

Make sure these files exist:

```text
models/ml/model.tflite
models/ml/model_meta.json
models/ml/symptom_vocab.json
```

### 6. Run the app

```bash
python main.py
```

## Test inputs

English:

```text
I have cough and fever
I have chest pain and breathing problem
I have headache and body pain
```

Kriol-style:

```text
Mi garr kof.
Mi garr fiba en bodi pein.
Mi garr jes pein en brithin trabul.
```

## Expected flow

```text
Choose language
→ Choose Type / Speak / Pictures
→ Enter or select symptoms
→ NLP detects symptoms
→ ML predicts severity
→ Follow-up questions appear
→ Final result page appears
```

Result meanings:

```text
Green  = Rest at home
Orange = Contact clinic soon
Red    = Emergency help
```

## Common fixes

If microphone does not work, allow microphone access:

```text
System Settings → Privacy & Security → Microphone
```

If ML model error appears, check the `models/ml/` folder.

If voice/Whisper error appears, run:

```bash
brew install ffmpeg portaudio
pip install -r requirements-voice.txt
```


```
```

