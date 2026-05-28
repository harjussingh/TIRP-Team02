#!/usr/bin/env python3
"""
Demonstration of NLP Translation Flow

Shows how the system:
1. Displays original Kriol text to user
2. Translates via NLP pipeline
3. Extracts symptoms from English
"""

from main import run_pipeline

def demo_nlp_translation():
    print("=" * 70)
    print("NLP TRANSLATION FLOW DEMONSTRATION")
    print("=" * 70)
    
    test_cases = [
        {
            "description": "Simple Kriol symptoms",
            "input": "mi garr hedache en hot-bodi"
        },
        {
            "description": "Kriol with negation",
            "input": "mi garr hedache bat mi no garr kof"
        },
        {
            "description": "Complex Kriol expression",
            "input": "mi fel sik bat mi no garr no fever nomo"
        },
        {
            "description": "English input (no translation needed)",
            "input": "I have a headache and fever"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"TEST {i}: {test['description']}")
        print(f"{'='*70}")
        
        kriol_input = test['input']
        print(f"\n📝 ORIGINAL INPUT (shown to user in GUI):")
        print(f"   \"{kriol_input}\"")
        
        print(f"\n⚙️  PROCESSING THROUGH NLP PIPELINE...")
        result = run_pipeline(kriol_input, source="text")
        
        print(f"\n🔄 STEP 0 - Kriol Translation:")
        print(f"   \"{result['translated_text']}\"")
        
        print(f"\n🧹 STEP 1 - Preprocessing:")
        print(f"   \"{result['cleaned_text']}\"")
        
        print(f"\n🔍 STEP 3 - Extracted Symptoms:")
        print(f"   {result['extracted_symptoms']}")
        
        print(f"\n✅ FINAL RESULTS:")
        print(f"   Symptoms Present: {result['symptoms_present']}")
        print(f"   Symptoms Negated: {result['symptoms_negated']}")


def show_translation_mechanics():
    print("\n\n" + "=" * 70)
    print("HOW NLP TRANSLATION WORKS")
    print("=" * 70)
    
    from nlp.kriol_translator import load_kriol_dictionary, translate_kriol_to_english, tokenize_kriol
    
    kriol_dict = load_kriol_dictionary("data/kriol_dictionary.json")
    
    example = "mi garr hedache bat mi no garr kof"
    print(f"\nExample: \"{example}\"")
    
    # Show tokenization
    tokens = tokenize_kriol(example)
    print(f"\n1. TOKENIZE:")
    print(f"   {tokens}")
    
    # Show dictionary lookup
    print(f"\n2. DICTIONARY LOOKUP:")
    for token in tokens:
        english = kriol_dict.get(token, token)
        arrow = "→" if token in kriol_dict else "→ (not in dict, keep as-is)"
        print(f"   {token:10} {arrow} {english}")
    
    # Show translation
    english = translate_kriol_to_english(example, kriol_dict)
    print(f"\n3. RECONSTRUCTED ENGLISH:")
    print(f"   \"{english}\"")
    
    print(f"\n📚 Dictionary Stats:")
    print(f"   Total Kriol words: {len(kriol_dict)}")
    print(f"   Categories: pronouns, verbs, negation, conjunctions, medical_symptoms, etc.")


if __name__ == "__main__":
    demo_nlp_translation()
    show_translation_mechanics()
    
    print("\n\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("""
✅ GUI shows ORIGINAL Kriol text: "mi garr hedache bat mi no garr kof"
✅ NLP pipeline translates automatically (Step 0 in run_pipeline)
✅ Translation method: Dictionary-based word substitution
✅ Symptoms extracted from English translation
✅ Results display both original and translated text

The user sees their exact input while the system processes English behind the scenes!
""")
