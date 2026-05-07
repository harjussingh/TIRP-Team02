"""
Voice Processor Module - Speech to Text using OpenAI Whisper

This module handles:
1. Audio file transcription (speech-to-text)
2. Language detection (English/Kriol - to be implemented)
3. Audio preprocessing
"""

import os
from typing import Tuple, Optional


class VoiceProcessor:
    """
    Process voice input and convert to text using Whisper.
    
    Usage:
        processor = VoiceProcessor()
        text = processor.transcribe_audio('path/to/audio.wav')
    """
    
    def __init__(self, model_name: str = 'small'):
        """
        Initialize the Voice Processor with Whisper model.
        
        Args:
            model_name: Whisper model size
                - 'tiny': Fastest, least accurate (~1GB RAM)
                - 'base': Fast, decent accuracy (~1GB RAM)
                - 'small': Better accuracy (recommended) (~2GB RAM)
                - 'medium': High accuracy (~5GB RAM)
                - 'large': Best accuracy (~10GB RAM)
        """
        self.model_name = model_name
        self.model = None
        self.kriol_dict = None
        
        # Medical vocabulary hints for better recognition (English)
        self.medical_prompt = (
            "Medical symptoms: fever, cough, headache, stomach pain, throat pain, "
            "nausea, vomiting, diarrhea, dizziness, chest pain, shortness of breath, "
            "abdominal pain, sore throat, feeling unwell."
        )
        
        # Kriol vocabulary hints (phonetically similar to English for Whisper)
        self.kriol_prompt = (
            "Kriol medical words: mi garr hedache, mi garr hot-bodi, mi garr kof, "
            "mi garr sik-bodi, mi garr pein, belly-pein, throat-pein, mi fel sik, "
            "mi fel bad, mi no garr, bat, en, o, nomo, bin, gat, fel."
        )
        
        # Combined prompt for bilingual support
        self.bilingual_prompt = f"{self.medical_prompt} {self.kriol_prompt}"
        
        self._load_model()
        self._load_kriol_dictionary()
    
    def _load_model(self):
        """Load Whisper model (lazy loading)"""
        try:
            import whisper
            print(f"Loading Whisper model '{self.model_name}'...")
            self.model = whisper.load_model(self.model_name)
            print(f"✓ Whisper model '{self.model_name}' loaded successfully")
        except ImportError:
            raise ImportError(
                "Whisper not installed. Please run: pip install openai-whisper"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load Whisper model: {e}")
    
    def _load_kriol_dictionary(self):
        """Load Kriol-to-English dictionary for post-processing"""
        try:
            from nlp.kriol_translator import load_kriol_dictionary
            self.kriol_dict = load_kriol_dictionary("data/kriol_dictionary.json")
            print("✓ Kriol dictionary loaded")
        except Exception as e:
            print(f"⚠ Warning: Could not load Kriol dictionary: {e}")
            self.kriol_dict = {}
    
    def transcribe_audio(
        self, 
        audio_path: str, 
        language: Optional[str] = 'en'
    ) -> str:
        """
        Transcribe audio file to text.
        
        Args:
            audio_path: Path to audio file (mp3, wav, m4a, etc.)
            language: Language hint ('en' for English)
        
        Returns:
            Transcribed text string
        
        Raises:
            FileNotFoundError: If audio file doesn't exist
            RuntimeError: If transcription fails
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        try:
            print(f"Transcribing audio: {audio_path}")
            
            # Use bilingual prompt to support both English and Kriol
            prompt = self.bilingual_prompt if language == 'en' else self.medical_prompt
            
            # Transcribe with Whisper using bilingual domain hints
            result = self.model.transcribe(
                audio_path,
                language='en',  # Use English as base (Kriol is English-based creole)
                fp16=False,  # Use FP32 for CPU compatibility
                initial_prompt=prompt,  # Guide recognition to medical + Kriol terms
                temperature=0.0,  # Use greedy decoding for more consistent results
                compression_ratio_threshold=2.4,  # Filter out nonsensical outputs
                logprob_threshold=-1.0,  # Filter low-confidence segments
                no_speech_threshold=0.6,  # Detect silence more accurately
                condition_on_previous_text=True  # Use context from previous segments
            )
            
            text = result['text'].strip()
            
            # Detect if transcription is Kriol or English
            detected_lang = self._detect_language(text)
            print(f"✓ Detected language: {detected_lang}")
            
            # Post-process: Fix common medical transcription errors
            text = self._fix_medical_transcription_errors(text)
            
            print(f"✓ Transcription: {text}")
            
            return text
            
        except Exception as e:
            raise RuntimeError(f"Transcription failed: {e}")
    
    def _detect_language(self, text: str) -> str:
        """
        Detect if transcribed text is likely Kriol or English.
        
        Uses keyword frequency analysis to determine language.
        
        Args:
            text: Transcribed text
        
        Returns:
            'kriol' or 'english'
        """
        if not self.kriol_dict:
            return 'english'
        
        text_lower = text.lower()
        words = text_lower.split()
        
        # Count Kriol-specific words
        kriol_keywords = {
            'mi', 'garr', 'gat', 'bat', 'bikaj', 'bikos', 'bin',
            'hedache', 'hot-bodi', 'kof', 'sik-bodi', 'pein',
            'nomo', 'nating', 'neba', 'yu', 'dei', 'yumi',
            'fel', 'feld', 'wok', 'kam', 'tok'
        }
        
        kriol_word_count = sum(1 for word in words if word in kriol_keywords)
        total_words = len(words)
        
        if total_words == 0:
            return 'english'
        
        # If more than 15% of words are Kriol-specific, classify as Kriol
        kriol_ratio = kriol_word_count / total_words
        
        if kriol_ratio > 0.15:
            return 'kriol'
        
        # Check for common Kriol patterns
        kriol_patterns = ['mi garr', 'mi gat', 'mi fel', 'no garr', 'bat mi']
        if any(pattern in text_lower for pattern in kriol_patterns):
            return 'kriol'
        
        return 'english'
    
    def _fix_medical_transcription_errors(self, text: str) -> str:
        """
        Fix common medical transcription errors using pattern matching.
        
        Args:
            text: Raw transcribed text
        
        Returns:
            Corrected text
        """
        import re
        
        # Common misrecognitions in medical context
        corrections = [
            # "feeding" often misheard for "feeling"
            (r'\bfeeding\s+(pain|sick|unwell|dizzy|nauseous)', r'feeling \1'),
            (r'\bfed\s+(pain|sick|unwell|dizzy)', r'feel \1'),
            
            # "while you" often misheard for "now I"
            (r'\bwhile\s+you\s+have', r'now I have'),
            (r'\bwhile\s+I\s+have', r'now I have'),
            
            # "stomach" variations
            (r'\bstomach\s+pain', r'stomach pain'),
            (r'\bstomach\s+ache', r'stomach pain'),
            (r'\bbellyache', r'stomach pain'),
            
            # "throat" variations
            (r'\bthroat\s+pain', r'sore throat'),
            (r'\bpain\s+in\s+(my|the)\s+throat', r'sore throat'),
            
            # "fever" variations
            (r'\bhigh\s+temperature', r'fever'),
            (r'\bfeeling\s+hot', r'fever'),
            
            # Fix common word boundary issues
            (r'\s+([.,!?])', r'\1'),  # Remove space before punctuation
            (r'([.,!?])([A-Za-z])', r'\1 \2'),  # Add space after punctuation
        ]
        
        corrected = text
        for pattern, replacement in corrections:
            corrected = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE)
        
        return corrected
    
    def transcribe_with_info(
        self, 
        audio_path: str, 
        language: Optional[str] = 'en'
    ) -> dict:
        """
        Transcribe audio and return detailed information.
        
        Args:
            audio_path: Path to audio file
            language: Language hint
        
        Returns:
            Dictionary with:
                - text: Transcribed text
                - language: Detected language
                - segments: Timestamped segments (if available)
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        try:
            result = self.model.transcribe(
                audio_path,
                language=language,
                fp16=False,
                verbose=False,
                initial_prompt=self.medical_prompt,
                temperature=0.0,
                compression_ratio_threshold=2.4,
                logprob_threshold=-1.0,
                no_speech_threshold=0.6,
                condition_on_previous_text=True
            )
            
            text = result['text'].strip()
            text = self._fix_medical_transcription_errors(text)
            
            return {
                'text': text,
                'language': result.get('language', language),
                'segments': result.get('segments', [])
            }
            
        except Exception as e:
            raise RuntimeError(f"Transcription failed: {e}")
    
    def transcribe_bilingual(self, audio_path: str) -> dict:
        """
        Transcribe audio with automatic language detection and translation.
        
        Supports both English and Kriol input. If Kriol is detected,
        automatically translates to English.
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            Dictionary with:
                - original_text: Raw transcription
                - detected_language: 'english' or 'kriol'
                - translated_text: English translation (same as original if English)
                - is_translated: Boolean indicating if translation occurred
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        try:
            # Transcribe using bilingual prompt
            original_text = self.transcribe_audio(audio_path, language='en')
            
            # Detect language
            detected_lang = self._detect_language(original_text)
            
            # Translate if Kriol
            translated_text = original_text
            is_translated = False
            
            if detected_lang == 'kriol' and self.kriol_dict:
                try:
                    from nlp.kriol_translator import translate_kriol_to_english, post_process_translation
                    translated_text = translate_kriol_to_english(original_text, self.kriol_dict)
                    translated_text = post_process_translation(translated_text)
                    is_translated = True
                    print(f"✓ Translated from Kriol: {translated_text}")
                except Exception as e:
                    print(f"⚠ Warning: Kriol translation failed: {e}")
                    translated_text = original_text
            
            return {
                'original_text': original_text,
                'detected_language': detected_lang,
                'translated_text': translated_text,
                'is_translated': is_translated
            }
            
        except Exception as e:
            raise RuntimeError(f"Bilingual transcription failed: {e}")
    
    def detect_language(self, text: str) -> str:
        """
        Detect if text is in Kriol or English.
        
        (To be implemented in Phase 2)
        
        Args:
            text: Transcribed text
        
        Returns:
            'english' or 'kriol'
        """
        # Placeholder - always return 'english' for now
        # Will implement Kriol detection in Phase 2
        return 'english'
    
    def process_voice_input(
        self, 
        audio_path: str
    ) -> Tuple[str, str]:
        """
        Complete voice processing pipeline.
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            Tuple of (detected_language, transcribed_text)
        """
        # Step 1: Transcribe audio to text
        text = self.transcribe_audio(audio_path)
        
        # Step 2: Detect language (placeholder for now)
        language = self.detect_language(text)
        
        return language, text


# Utility function for easy usage
def transcribe_file(audio_path: str, model: str = 'base') -> str:
    """
    Quick utility to transcribe an audio file.
    
    Args:
        audio_path: Path to audio file
        model: Whisper model size
    
    Returns:
        Transcribed text
    """
    processor = VoiceProcessor(model_name=model)
    return processor.transcribe_audio(audio_path)


if __name__ == "__main__":
    # Test the voice processor
    import sys
    
    print("=== Voice Processor Test ===\n")
    
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
        print(f"Testing with audio file: {audio_file}\n")
        
        processor = VoiceProcessor(model_name='base')
        language, text = processor.process_voice_input(audio_file)
        
        print(f"\nResults:")
        print(f"  Language: {language}")
        print(f"  Text: {text}")
    else:
        print("Usage: python voice_processor.py <audio_file_path>")
        print("\nExample:")
        print("  python voice_processor.py test_audio.wav")
