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


UNICODE_TO_SCHEME = [
    (0x0900, 0x097F, "DEVANAGARI"),
    (0x0980, 0x09FF, "BENGALI"),
    (0x0B80, 0x0BFF, "TAMIL"),
    (0x0C00, 0x0C7F, "TELUGU"),
    (0x0A80, 0x0AFF, "GUJARATI"),
    (0x0A00, 0x0A7F, "GURMUKHI"),
    (0x0C80, 0x0CFF, "KANNADA"),
    (0x0D00, 0x0D7F, "MALAYALAM"),
    (0x0B00, 0x0B7F, "ORIYA"),
]


def detect_indic_script_scheme(text: str) -> str | None:
    """Detects the Brahmic script scheme of the given text for sanscript."""
    for ch in text:
        cp = ord(ch)
        for start, end, scheme in UNICODE_TO_SCHEME:
            if start <= cp <= end:
                return scheme
    return None


def transliterate_indic_to_latin(text: str) -> str:
    """
    Algorithmically transliterates any native Indic script into Roman/Latin phonetics.
    Converts word-by-word to handle multi-lingual or mixed inputs gracefully.
    """
    if not HAS_SANSCRIPT or not text:
        return text

    words = text.split()
    out = []
    for w in words:
        scheme = detect_indic_script_scheme(w)
        if scheme:
            src = getattr(sanscript, scheme, None)
            if src:
                try:
                    w = sanscript.transliterate(w, src, sanscript.ITRANS)
                except Exception:
                    pass
        out.append(w)
    res = " ".join(out)
    return re.sub(r"[\.\^~_]", "", res)


def deaspirate(w: str) -> str:
    """Standardizes aspirated consonants and phonetic clusters in Indian names."""
    w = w.lower()
    w = re.sub(r"dh", "d", w)
    w = re.sub(r"th", "t", w)
    w = re.sub(r"bh", "b", w)
    w = re.sub(r"kh", "k", w)
    w = re.sub(r"gh", "g", w)
    w = re.sub(r"ph", "p", w)
    w = re.sub(r"ch", "c", w)
    w = re.sub(r"sh|zh", "s", w)
    w = re.sub(r"v|w", "b", w)
    w = re.sub(r"m(?=[kgcjtdpbnsr])", "n", w)
    w = re.sub(r"(.)\1+", r"\1", w)
    return w


def consonant_skeleton(word: str) -> str:
    """
    Extracts phonetic consonant skeleton to match Anglicized revenue spellings
    (e.g., 'Nelluru' <-> 'Nellore', 'Karnulu' <-> 'Kurnool', 'Madhurai' <-> 'Madurai', 'Malada' <-> 'Malda').
    """
    w = deaspirate(word)
    # Strip vowels
    cons = re.sub(r"[aeiou]", "", w)
    return cons


def normalize_indic_phonetics(text: str, target_lang: str = "hi") -> str:
    """
    Normalizes phonetic variations and replaces colloquial Romanized keywords
    with canonical concepts to aid schema linking.

    Bidirectional:
    - If Latin characters are present, transliterates into target Indic script.
    - If native Indic script is present, appends algorithmic Latin bridge.
    """
    normalized = text.lower()
    for roman_token, canonical in TRANSLITERATION_MAP.items():
        pattern = rf"\b{roman_token}\b"
        normalized = re.sub(pattern, f"{roman_token} ({canonical})", normalized)

    # 1. Indic -> Latin Transliteration Bridge (Always active when Indic chars present)
    if HAS_SANSCRIPT and any(ord(c) >= 0x0900 for c in text):
        latin_bridge = transliterate_indic_to_latin(text)
        if latin_bridge and latin_bridge.lower() != text.lower():
            normalized = f"{normalized} {latin_bridge.lower()}"

    # 2. Latin -> Indic Transliteration (When primarily ASCII)
    if HAS_SANSCRIPT and target_lang in LANG_TO_SCHEME:
        scheme_name = LANG_TO_SCHEME[target_lang].upper()
        scheme = getattr(sanscript, scheme_name, None)

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
