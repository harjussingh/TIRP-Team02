import json
import sys
import os

from nlp.preprocess import clean_text
from nlp.symptom_mapper import load_synonyms, map_synonyms
from nlp.symptom_extractor import load_symptoms, SymptomExtractor
from nlp.negation_detector import detect_negations, detect_negations_hybrid, build_result
from nlp.kriol_translator import load_kriol_dictionary
from nlp.neural_translator import hybrid_translate
from nlp.language_detector import detect_language
from nlp.bert_extractor import bert_extract_symptoms
from nlp.feature_engineer import engineer_features


def run_pipeline(user_input: str, source: str = "text") -> dict:
    # Load data first
    synonyms = load_synonyms("data/synonyms.json")
    symptoms = load_symptoms("data/symptoms.json")
    kriol_dict = load_kriol_dictionary("data/kriol_dictionary.json")
    
    # Common English function words that must never be spell-corrected
    COMMON_WORDS = {
        "i", "a", "an", "the", "my", "me", "we", "he", "she", "it", "they",
        "am", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would",
        "can", "could", "should", "may", "might", "shall",
        "and", "or", "but", "not", "no", "so", "if", "in", "on",
        "at", "to", "for", "of", "with", "as", "by", "from", "up",
        "that", "this", "what", "which", "who", "when", "where", "how",
        "feel", "feels", "feeling", "felt", "hurt", "hurts", "pain",
        "bad", "very", "some", "any", "also", "now", "still", "since",
        # negation words — must never be spell-corrected
        "never", "none", "neither", "nor", "without", "nothing", "nobody",
        "deny", "denies", "lack", "absent",
        # other common words that could be confused with symptoms
        "after", "before", "since", "about", "just", "only", "even",
        "then", "than", "into", "onto", "over", "under", "again",
        "there", "their", "these", "those", "every", "other", "each"
    }
    
    # Build known words: symptoms + synonym keys + common English words
    known_words = set(symptoms)
    for synonym_key in synonyms.keys():
        known_words.update(synonym_key.split())
    for symptom in symptoms:
        known_words.update(symptom.split())
    known_words.update(COMMON_WORDS)
    known_words = list(known_words)
    
    # Step 0a: Detect language
    detected_lang, lang_confidence = detect_language(user_input)

    # Step 0b: Hybrid translation (dict → MarianMT fallback)
    translation_result = hybrid_translate(user_input, kriol_dict, detected_lang)
    english_text = translation_result["text"]
    translation_method = translation_result["method"]
    oov_ratio = translation_result["oov_ratio"]
    
    # Step 1: preprocess with spell correction
    cleaned_text = clean_text(english_text, known_words=known_words)

    # Step 2: synonym mapping
    mapped_text = map_synonyms(cleaned_text, synonyms)

    # Step 3a: PhraseMatcher + fuzzy symptom extraction (primary)
    extractor = SymptomExtractor(symptoms)
    extracted_symptoms = extractor.extract_symptoms(mapped_text)

    # Step 3b: BioClinicalBERT semantic extraction (advisory layer)
    # Runs in parallel but does NOT feed into negation detection.
    # The base model needs fine-tuning before its output is reliable enough
    # to merge into the main pipeline. Results are exposed in bert_suggestions
    # for inspection and future fine-tuning data collection.
    bert_present, bert_negated = bert_extract_symptoms(
        text=english_text,          # pre-normalisation text preserves casing
        symptoms=symptoms,
        already_found=extracted_symptoms
    )

    # Step 4: hybrid negation detection (rules + Bi-LSTM override)
    present, negated = detect_negations_hybrid(mapped_text, extracted_symptoms)

    # Step 5: build structured result
    result = build_result(
        input_text=user_input,
        cleaned_text=cleaned_text,
        mapped_text=mapped_text,
        extracted_symptoms=extracted_symptoms,
        present=present,
        negated=negated
    )
    result["bert_suggestions"] = {
        "present": bert_present,
        "negated": bert_negated,
        "note": "Advisory only — base model requires fine-tuning for full reliability"
    }
    
    # Add translation info, source, and language detection
    result["translated_text"] = english_text
    result["translation_method"] = translation_method   # "passthrough" | "dict" | "dict+neural"
    result["oov_ratio"] = oov_ratio
    result["input_source"] = source  # "text" or "voice"
    result["detected_language"] = detected_lang
    result["language_confidence"] = round(lang_confidence, 4)

    # Step 6: feature engineering — flat ML-ready feature vector
    result["features"] = engineer_features(result)

    return result


def process_voice_input(audio_path: str) -> dict:
    """
    Process voice input from audio file with automatic Kriol/English detection.
    
    Args:
        audio_path: Path to audio file
    
    Returns:
        Result dictionary with symptoms and triage info
    """
    try:
        from nlp.voice_processor import VoiceProcessor
        
        print(f"\n🎤 Processing voice input: {audio_path}")
        
        # Initialize voice processor with improved 'small' model
        processor = VoiceProcessor(model_name='small')
        
        # Transcribe audio with bilingual support
        transcription = processor.transcribe_bilingual(audio_path)
        
        original_text = transcription['original_text']
        detected_lang = transcription['detected_language']
        translated_text = transcription['translated_text']
        is_translated = transcription['is_translated']
        
        print(f"✓ Original transcription: {original_text}")
        print(f"✓ Detected language: {detected_lang}")
        if is_translated:
            print(f"✓ Translated to English: {translated_text}")
        print()
        
        # Use translated text for symptom extraction
        text_to_process = translated_text
        
        # Run through symptom extraction pipeline
        result = run_pipeline(text_to_process, source="voice")
        result["voice_transcription_original"] = original_text
        result["voice_transcription_translated"] = translated_text
        result["detected_language"] = detected_lang
        result["was_translated"] = is_translated
        
        return result
        
    except ImportError:
        print("\n❌ Error: Whisper not installed.")
        print("Please install dependencies:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error processing voice input: {e}")
        sys.exit(1)


def main():
    print("=" * 60)
    print("SACA - Smart Adaptive Clinical Assistant")
    print("Symptom Extractor (with Kriol & Voice support)")
    print("=" * 60)
    
    # Check for command-line arguments (voice input)
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
        
        if not os.path.exists(audio_file):
            print(f"\n❌ Error: Audio file not found: {audio_file}")
            print("\nUsage:")
            print("  Text mode:  python main.py")
            print("  Voice mode: python main.py <audio_file.wav>")
            sys.exit(1)
        
        # Voice input mode
        result = process_voice_input(audio_file)
        print("\n" + "=" * 60)
        print("RESULT:")
        print("=" * 60)
        print(json.dumps(result, indent=2))
        return
    
    # Text input mode (interactive)
    print("\nModes:")
    print("  - Type symptoms in Kriol or English")
    print("  - Type 'exit' to quit")
    print("  - For voice: python main.py <audio_file>\n")

    while True:
        user_input = input("Enter text: ").strip()

        if user_input.lower() == "exit":
            print("Goodbye.")
            break

        result = run_pipeline(user_input, source="text")
        print("\nResult:")
        print(json.dumps(result, indent=2))
        print()


if __name__ == "__main__":
    main()