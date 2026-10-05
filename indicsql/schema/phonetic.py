"""
IndicSQL Phonetic Transliteration Module
Handles conversion of Latin/Hinglish/Code-mixed inputs to standard Indic Scripts.
"""

import re
from typing import Dict

try:
    from indic_transliteration import sanscript
    from indic_transliteration.sanscript import transliterate

    HAS_SANSCRIPT = True
except ImportError:
    HAS_SANSCRIPT = False

# Mapping from language code to sanscript output scheme
LANG_TO_SCHEME: Dict[str, str] = (
    {
        "hi": "devanagari",
        "mr": "devanagari",
        "bn": "bengali",
        "ta": "tamil",
        "te": "telugu",
        "gu": "gujarati",
    }
    if HAS_SANSCRIPT
    else {}
)

# Common Latin-to-canonical mappings for Indian administrative terms
TRANSLITERATION_MAP: Dict[str, str] = {
    "kisan": "farmer",
    "kisano": "farmer",
    "shatkari": "farmer",
    "shala": "school",
    "vidyarthi": "student",
    "rojgar": "employment",
    "mandays": "mandays",
    "yojana": "scheme",
    "saksharta": "literacy",
    "pichle": "previous",
    "saal": "year",
    "rajya": "state",
    "jila": "district",
    "jile": "district",
    "manrega": "mgnrega",
}


def normalize_indic_phonetics(text: str, target_lang: str = "hi") -> str:
    """
    Normalizes phonetic variations and replaces colloquial Romanized keywords
    with canonical concepts to aid schema linking.

    If target_lang is provided and Latin characters are present, performs
    transliteration into the target Indic script when indic-transliteration is installed.
    """
    normalized = text.lower()
    for roman_token, canonical in TRANSLITERATION_MAP.items():
        pattern = rf"\b{roman_token}\b"
        normalized = re.sub(pattern, f"{roman_token} ({canonical})", normalized)

    if target_lang not in LANG_TO_SCHEME:
        return normalized

    # If sanscript is available, transliterate Latin phonetic tokens to Indic script
    if HAS_SANSCRIPT and target_lang in LANG_TO_SCHEME:
        scheme_name = LANG_TO_SCHEME[target_lang].upper()
        scheme = getattr(sanscript, scheme_name, None)

        # Transliterate only if we have primarily Latin characters
        if scheme and any(c.isascii() and c.isalpha() for c in text):
            try:
                xlit = transliterate(text, sanscript.ITRANS, scheme)
                return f"{normalized} {xlit}".strip()
            except Exception:
                return normalized

    return normalized


def test_transliteration() -> None:
    print(normalize_indic_phonetics("vidyarthi", "hi"))  # Should print student + विद्यार्थी
    print(normalize_indic_phonetics("kisano", "hi"))  # Should print farmer + किसानों
    print(normalize_indic_phonetics("shala", "mr"))  # Should print school + शाळा


if __name__ == "__main__":
    test_transliteration()
