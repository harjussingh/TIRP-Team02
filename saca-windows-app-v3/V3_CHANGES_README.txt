SACA Windows App - V2 Update

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
