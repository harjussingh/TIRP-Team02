#!/usr/bin/env python3
"""
Test script for Kriol-English bilingual transcription support.

Demonstrates:
1. Language detection (Kriol vs English)
2. Automatic translation from Kriol to English
3. Bilingual medical vocabulary recognition
"""

from nlp.voice_processor import VoiceProcessor

def test_language_detection():
    """Test the language detection algorithm"""
    processor = VoiceProcessor(model_name='base')  # Using base for faster testing
    
    test_cases = [
        # (text, expected_language)
        ("I have a headache and fever", "english"),
        ("mi garr hedache en hot-bodi", "kriol"),
        ("mi fel sik bat mi no garr kof", "kriol"),
        ("I am feeling pain in my stomach", "english"),
        ("mi garr pein long mi belly", "kriol"),
        ("yu garr fever or what", "kriol"),
        ("do you have a cough", "english"),
        ("mi no garr no sik-bodi nomo", "kriol"),
    ]
    
    print("=" * 70)
    print("Language Detection Tests")
    print("=" * 70)
    
    correct = 0
    for text, expected in test_cases:
        detected = processor._detect_language(text)
        is_correct = detected == expected
        correct += is_correct
        
        status = "✓" if is_correct else "✗"
        print(f"\n{status} Text: {text}")
        print(f"  Expected: {expected} | Detected: {detected}")
    
    print("\n" + "=" * 70)
    print(f"Accuracy: {correct}/{len(test_cases)} ({100*correct/len(test_cases):.1f}%)")
    print("=" * 70)


def test_kriol_vocabulary():
    """Test Kriol vocabulary in prompts"""
    processor = VoiceProcessor(model_name='base')
    
    print("\n" + "=" * 70)
    print("Kriol Vocabulary Loaded")
    print("=" * 70)
    
    print(f"\nMedical Prompt (English):")
    print(f"  {processor.medical_prompt[:100]}...")
    
    print(f"\nKriol Prompt:")
    print(f"  {processor.kriol_prompt[:100]}...")
    
    print(f"\nBilingual Prompt (Combined):")
    print(f"  {processor.bilingual_prompt[:150]}...")
    
    print(f"\nKriol Dictionary Loaded: {len(processor.kriol_dict)} words")
    
    # Show some example Kriol words
    print("\nSample Kriol Vocabulary:")
    sample_words = list(processor.kriol_dict.items())[:10]
    for kriol, english in sample_words:
        print(f"  {kriol:15} → {english}")


def demo_bilingual_workflow():
    """Demonstrate the bilingual transcription workflow"""
    print("\n" + "=" * 70)
    print("Bilingual Transcription Workflow")
    print("=" * 70)
    
    print("""
WORKFLOW STEPS:
1. Record/upload audio (Kriol or English)
2. Whisper transcribes using bilingual prompt (English base + Kriol vocab hints)
3. Language detection analyzes the transcribed text
4. If Kriol detected → translate to English using dictionary
5. Apply medical term corrections
6. Extract symptoms from English text
7. Display results with language indicator

EXAMPLE FLOW:

Audio Input (Kriol): "mi garr hedache en hot-bodi bat mi no garr kof"
                     ↓
Whisper Transcription: "mi garr hedache en hot-bodi bat mi no garr kof"
                     ↓
Language Detection: KRIOL detected (keywords: mi, garr, bat, hedache, kof)
                     ↓
Kriol→English Translation: "i have headache and fever but i not have cough"
                     ↓
Post-processing: "i have headache and fever but i do not have cough"
                     ↓
Symptom Extraction: headache, fever, cough (negated)
                     ↓
Results Display:
  - Input Language: Kriol
  - Original: "mi garr hedache en hot-bodi bat mi no garr kof"
  - Translated: "i have headache and fever but i do not have cough"
  - Symptoms Present: headache, fever
  - Symptoms Negated: cough
""")


if __name__ == "__main__":
    print("\n🔬 KRIOL-WHISPER INTEGRATION TEST SUITE\n")
    
    test_language_detection()
    test_kriol_vocabulary()
    demo_bilingual_workflow()
    
    print("\n✅ All tests completed!\n")
    print("To test with actual audio:")
    print("  python gui.py          # Launch GUI and record voice")
    print("  python main.py audio.wav  # Process audio file via CLI\n")
