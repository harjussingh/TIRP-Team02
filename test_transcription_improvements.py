#!/usr/bin/env python3
"""
Test script to demonstrate transcription improvements.

Tests common misrecognitions in medical context:
- "feeding" vs "feeling" 
- "while you have" vs "now I have"
- Medical term standardization
"""

from nlp.voice_processor import VoiceProcessor

def test_medical_corrections():
    """Test the medical transcription error correction."""
    processor = VoiceProcessor(model_name='base')  # Using base for testing
    
    test_cases = [
        # Original misrecognition -> Expected correction
        ("hello i started feeding pain in my stomach", 
         "hello i started feeling pain in my stomach"),
        
        ("then i started getting fever now while you have a pain in my throat",
         "then i started getting fever now now I have a pain in my throat"),
        
        ("i have stomach ache and throat pain",
         "i have stomach pain and sore throat"),
        
        ("feeding dizzy and have high temperature",
         "feeling dizzy and have fever"),
        
        ("while you have pain in the throat but i don't have any cough",
         "now I have sore throat but i don't have any cough"),
    ]
    
    print("=" * 70)
    print("Medical Transcription Error Correction Tests")
    print("=" * 70)
    
    for raw_text, expected in test_cases:
        corrected = processor._fix_medical_transcription_errors(raw_text)
        
        print(f"\nRaw:       {raw_text}")
        print(f"Corrected: {corrected}")
        print(f"Match: {'✓' if corrected.lower() == expected.lower() else '✗ Expected: ' + expected}")
        print("-" * 70)

if __name__ == "__main__":
    test_medical_corrections()
