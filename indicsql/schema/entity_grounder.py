"""
indicsql/schema/entity_grounder.py
Cross-Lingual Dynamic Entity Grounder for Pan-India Relational Databases.

Automatically introspects DuckDB / Parquet stores at initialization, caching
all distinct States (36), Districts (780+), Crops, and Commodities.
Provides sub-millisecond phonetic and transliteration grounding for Telugu,
Bengali, Tamil, Marathi, and Devanagari queries into exact database literals.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

try:
    import duckdb
    HAS_DUCKDB = True
except ImportError:
    HAS_DUCKDB = False

from indicsql.schema.phonetic import consonant_skeleton, transliterate_indic_to_latin

logger = logging.getLogger(__name__)

PARQUET_STORE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "parquet_stores"

# Direct phonetic and script normalization mapping for high-frequency regional entities
INDIC_SCRIPT_PHONETICS: Dict[str, str] = {   'अमृतसर': 'Amritsar',
    'असम': 'ASSAM',
    'आंध्र': 'ANDHRA PRADESH',
    'आंध्र प्रदेश': 'ANDHRA PRADESH',
    'आंध्र प्रदेशात': 'ANDHRA PRADESH',
    'आसाम': 'ASSAM',
    'आसाममध्ये': 'ASSAM',
    'इंदौर': 'Indore',
    'उत्तर प्रदेश': 'UTTAR PRADESH',
    'उत्तर प्रदेशात': 'UTTAR PRADESH',
    'उत्तराखंड': 'UTTARAKHAND',
    'ओडिशा': 'ODISHA',
    'ओडिशामध्ये': 'ODISHA',
    'औरंगाबाद': 'Aurangabad',
    'कर्नाटकात': 'KARNATAKA',
    'कानपुर': 'Kanpur',
    'कापूस': 'COTTON',
    'केरळमध्ये': 'KERALA',
    'कोईम्बतूर': 'Coimbatore',
    'कोयंबटूर': 'Coimbatore',
    'कोल्हापूर': 'Kolhapur',
    'गन्ना': 'SUGARCANE',
    'गव्हाचा': 'WHEAT',
    'गव्हाची': 'WHEAT',
    'गहू': 'WHEAT',
    'गुजरात': 'GUJARAT',
    'गुजरातमध्ये': 'GUJARAT',
    'गेहूं': 'WHEAT',
    'गोवा': 'GOA',
    'गोव्यात': 'GOA',
    'चंडीगढ़': 'CHANDIGARH',
    'चावल': 'RICE',
    'छत्तीसगढ़': 'CHHATTISGARH',
    'छत्रपती संभाजीनगर': 'Aurangabad',
    'जम्मू और कश्मीर': 'JAMMU AND KASHMIR',
    'जम्मू-कश्मीर': 'JAMMU AND KASHMIR',
    'जयपुर': 'Jaipur',
    'झारखंड': 'JHARKHAND',
    'झारखंडमध्ये': 'JHARKHAND',
    'ठाणे': 'Thane',
    'डीएपी': 'DAP',
    'तमिलनाडु': 'TAMIL NADU',
    'तामिळनाडू': 'TAMIL NADU',
    'तामिळनाडूमध्ये': 'TAMIL NADU',
    'तेलंगणामध्ये': 'TELANGANA',
    'तेलंगाना': 'TELANGANA',
    'तेलंगाना में': 'TELANGANA',
    'दिल्ली': 'DELHI',
    'नागपूर': 'Nagpur',
    'नाशिक': 'Nashik',
    'पंजाब': 'PUNJAB',
    'पंजाबमध्ये': 'PUNJAB',
    'पटना': 'Patna',
    'पश्चिम बंगाल': 'WEST BENGAL',
    'पश्चिम बंगालमध्ये': 'WEST BENGAL',
    'पुणे': 'Pune',
    'बिहार': 'BIHAR',
    'बिहारमध्ये': 'BIHAR',
    'भुईमूग': 'GROUNDNUT',
    'भोपाल': 'Bhopal',
    'मध्य प्रदेश': 'MADHYA PRADESH',
    'मध्य प्रदेशात': 'MADHYA PRADESH',
    'मध्यप्रদেশ': 'MADHYA PRADESH',
    'महाराष्ट्र': 'MAHARASHTRA',
    'महाराष्ट्रात': 'MAHARASHTRA',
    'राजस्थान': 'RAJASTHAN',
    'राजस्थानमध्ये': 'RAJASTHAN',
    'लखनऊ': 'Lucknow',
    'लद्दाख': 'LADAKH',
    'लुधियाना': 'Ludhiana',
    'वाराणसी': 'Varanasi',
    'सरसों': 'MUSTARD',
    'सोयाबीन': 'SOYBEAN',
    'सोलापूर': 'Solapur',
    'सয়াবিন': 'SOYBEAN',
    'हरियाणा': 'HARYANA',
    'हरियाणामध्ये': 'HARYANA',
    'हिमाचल प्रदेश': 'HIMACHAL PRADESH',
    'অন্ধ্রপ্রদেশ': 'ANDHRA PRADESH',
    'অন্ধ্রপ্রদেশে': 'ANDHRA PRADESH',
    'আসাম': 'ASSAM',
    'আসামে': 'ASSAM',
    'উত্তর প্রদেশ': 'UTTAR PRADESH',
    'উত্তর প্রদেশে': 'UTTAR PRADESH',
    'উত্তর ২৪ পরগনা': 'North 24 Parganas',
    'ওড়িশা': 'ODISHA',
    'ওড়িশায়': 'ODISHA',
    'কর্ণাটক': 'KARNATAKA',
    'কর্ণাটকে': 'KARNATAKA',
    'কলকাতা': 'Kolkata',
    'কেরালা': 'KERALA',
    'কেরালাতে': 'KERALA',
    'কোয়েম্বাটোর': 'Coimbatore',
    'গম': 'WHEAT',
    'গমের': 'WHEAT',
    'গুজরাট': 'GUJARAT',
    'গুজরাটে': 'GUJARAT',
    'ঝাড়খণ্ড': 'JHARKHAND',
    'ঝাড়খণ্ডে': 'JHARKHAND',
    'ডিএপি': 'DAP',
    'ডিএপি সারের': 'DAP',
    'তামিলনাড়ু': 'TAMIL NADU',
    'তামিলনাড়ুতে': 'TAMIL NADU',
    'তেলেঙ্গানা': 'TELANGANA',
    'তেলেঙ্গানায়': 'TELANGANA',
    'ত্রিপুরা': 'TRIPURA',
    'ত্রিপুরায়': 'TRIPURA',
    'দার্জিলিং': 'Darjeeling',
    'ধান': 'RICE',
    'নদিয়া': 'Nadia',
    'পশ্চিমবঙ্গ': 'WEST BENGAL',
    'পশ্চিমবঙ্গে': 'WEST BENGAL',
    'পাঞ্জাব': 'PUNJAB',
    'পাঞ্জাবে': 'PUNJAB',
    'পাট': 'JUTE',
    'পুনে': 'Pune',
    'বিহার': 'BIHAR',
    'বিহারে': 'BIHAR',
    'মধ্যপ্রদেশ': 'MADHYA PRADESH',
    'মধ্যপ্রদেশে': 'MADHYA PRADESH',
    'মহারাষ্ট্র': 'MAHARASHTRA',
    'মহারাষ্ট্রে': 'MAHARASHTRA',
    'মহারাষ্ট্রের': 'MAHARASHTRA',
    'মালদা': 'Malda',
    'মুর্শিদাবাদ': 'Murshidabad',
    'রাজস্থান': 'RAJASTHAN',
    'রাজস্থানে': 'RAJASTHAN',
    'সয়াবিন': 'SOYBEAN',
    'সয়াবিনের': 'SOYBEAN',
    'হরিয়ানা': 'HARYANA',
    'হরিয়ানায়': 'HARYANA',
    'হাওড়া': 'Howrah',
    'হুগলি': 'Hooghly',
    'হুগলী': 'Hooghly',
    'அசாமில்': 'ASSAM',
    'அசாம்': 'ASSAM',
    'ஆந்திரா': 'ANDHRA PRADESH',
    'ஆந்திராவில்': 'ANDHRA PRADESH',
    'ஈரோடு': 'Erode',
    'உத்தர பிரதேசம்': 'UTTAR PRADESH',
    'உத்தரபிரதேசத்தில்': 'UTTAR PRADESH',
    'உத்தரபிரதேசம்': 'UTTAR PRADESH',
    'ஒடிசா': 'ODISHA',
    'ஒடிசாவில்': 'ODISHA',
    'கரும்பு': 'SUGARCANE',
    'கர்நாடகா': 'KARNATAKA',
    'கர்நாடகாவில்': 'KARNATAKA',
    'குஜராத்': 'GUJARAT',
    'குஜராத்தில்': 'GUJARAT',
    'கேரளா': 'KERALA',
    'கேரளாவில்': 'KERALA',
    'கோதுமை': 'WHEAT',
    'கோதுமையின்': 'WHEAT',
    'கோயம்புத்தூர்': 'Coimbatore',
    'கோவை': 'Coimbatore',
    'சென்னை': 'Chennai',
    'சேலம்': 'Salem',
    'சோயாபீனின்': 'SOYBEAN',
    'சோயாபீன்': 'SOYBEAN',
    'ஜார்கண்டில்': 'JHARKHAND',
    'ஜார்கண்ட்': 'JHARKHAND',
    'டிஏபி': 'DAP',
    'டிஏபி உரத்தின்': 'DAP',
    'தமிழ்நாடு': 'TAMIL NADU',
    'தமிழ்நாட்ட': 'TAMIL NADU',
    'தமிழ்நாட்டின்': 'TAMIL NADU',
    'தமிழ்நாட்டில்': 'TAMIL NADU',
    'திருச்சிராப்பள்ளி': 'Tiruchirappalli',
    'திருநெல்வேலி': 'Tirunelveli',
    'தெலுங்கானா': 'TELANGANA',
    'தெலுங்கானாவில்': 'TELANGANA',
    'நெல்': 'RICE',
    'பஞ்சாபில்': 'PUNJAB',
    'பஞ்சாப்': 'PUNJAB',
    'பருத்தி': 'COTTON',
    'பீகாரில்': 'BIHAR',
    'பீகார்': 'BIHAR',
    'புதுச்சேரி': 'PUDUCHERRY',
    'புதுச்சேரியில்': 'PUDUCHERRY',
    'புனே': 'Pune',
    'மகாராஷ்டிரா': 'MAHARASHTRA',
    'மகாராஷ்டிராவில்': 'MAHARASHTRA',
    'மதுரை': 'Madurai',
    'மத்திய பிரதேசத்தில்': 'MADHYA PRADESH',
    'மத்திய பிரதேசம்': 'MADHYA PRADESH',
    'மத்தியப் பிரதேசத்தில்': 'MADHYA PRADESH',
    'மேற்கு வங்கத்தில்': 'WEST BENGAL',
    'மேற்கு வங்கம்': 'WEST BENGAL',
    'மேற்கு வங்காளம்': 'WEST BENGAL',
    'ராஜஸ்தானில்': 'RAJASTHAN',
    'ராஜஸ்தான்': 'RAJASTHAN',
    'வெங்காயம்': 'ONION',
    'ஹரியானா': 'HARYANA',
    'ஹரியானாவில்': 'HARYANA',
    'అస్సాం': 'ASSAM',
    'అస్సాంలో': 'ASSAM',
    'ఆంధ్రప్రదేశ్': 'ANDHRA PRADESH',
    'ఆంధ్రప్రదేశ్ లో': 'ANDHRA PRADESH',
    'ఆంధ్రప్రదేశ్\u200cలో': 'ANDHRA PRADESH',
    'ఉత్తర ప్రదేశ్': 'UTTAR PRADESH',
    'ఉత్తరప్రదేశ్': 'UTTAR PRADESH',
    'ఉత్తరప్రదేశ్ లో': 'UTTAR PRADESH',
    'ఉత్తరప్రదేశ్\u200cలో': 'UTTAR PRADESH',
    'ఒడిశా': 'ODISHA',
    'ఒడిశాలో': 'ODISHA',
    'కడప': 'Kadapa',
    'కర్ణాటక': 'KARNATAKA',
    'కర్ణాటకలో': 'KARNATAKA',
    'కర్నూలు': 'Kurnool',
    'కేరళ': 'KERALA',
    'కేరళలో': 'KERALA',
    'కోయంబత్తూర్': 'Coimbatore',
    'గుంటూరు': 'Guntur',
    'గుజరాత్': 'GUJARAT',
    'గుజరాత్ లో': 'GUJARAT',
    'గుజరాత్\u200cలో': 'GUJARAT',
    'గోధుమ': 'WHEAT',
    'గోధుమల': 'WHEAT',
    'గోధుమలు': 'WHEAT',
    'జార్ఖండ్': 'JHARKHAND',
    'జార్ఖండ్ లో': 'JHARKHAND',
    'జార్ఖండ్\u200cలో': 'JHARKHAND',
    'డీఏపీ': 'DAP',
    'డీఏపీ ఎరువుల': 'DAP',
    'తమిళనాడు': 'TAMIL NADU',
    'తమిళనాడులో': 'TAMIL NADU',
    'తమిళనాడులోని': 'TAMIL NADU',
    'తిరుపతి': 'Tirupati',
    'తెలంగాణ': 'TELANGANA',
    'తెలంగాణలో': 'TELANGANA',
    'నెల్లూరు': 'Nellore',
    'పంజాబ్': 'PUNJAB',
    'పంజాబ్ లో': 'PUNJAB',
    'పంజాబ్\u200cలో': 'PUNJAB',
    'పత్తి': 'COTTON',
    'పశ్చిమ బెంగాల్': 'WEST BENGAL',
    'పశ్చిమ బెంగాల్ లో': 'WEST BENGAL',
    'పశ్చిమ బెంగాల్\u200cలో': 'WEST BENGAL',
    'పుణే': 'Pune',
    'బీహార్': 'BIHAR',
    'బీహార్ లో': 'BIHAR',
    'బీహార్\u200cలో': 'BIHAR',
    'మధ్య ప్రదేశ్': 'MADHYA PRADESH',
    'మధ్యప్రదేశ్': 'MADHYA PRADESH',
    'మధ్యప్రదేశ్ లో': 'MADHYA PRADESH',
    'మధ్యప్రదేశ్\u200cలో': 'MADHYA PRADESH',
    'మహారాష్ట్ర': 'MAHARASHTRA',
    'మహారాష్ట్రలో': 'MAHARASHTRA',
    'మొక్కజొన్న': 'MAIZE',
    'యూరియా': 'UREA',
    'రాజస్థాన్': 'RAJASTHAN',
    'రాజస్థాన్ లో': 'RAJASTHAN',
    'రాజస్థాన్\u200cలో': 'RAJASTHAN',
    'వరి': 'RICE',
    'వరి పంట': 'RICE',
    'విజయవాడ': 'Vijayawada',
    'విశాఖపట్నం': 'Visakhapatnam',
    'వేరుశనగ': 'GROUNDNUT',
    'సోయాబీన్': 'SOYBEAN',
    'హర్యానా': 'HARYANA',
    'హర్యానాలో': 'HARYANA'}

# Standard Indian commodities to distinguish cleanly from administrative states
KNOWN_COMMODITIES: Set[str] = {
    "WHEAT", "RICE", "COTTON", "SOYBEAN", "SUGARCANE", "MUSTARD", "GROUNDNUT",
    "MAIZE", "JUTE", "ONION", "UREA", "DAP"
}

# State abbreviations recognized across natural and code-mixed queries
STATE_ABBREVIATIONS: Dict[str, str] = {
    "up": "UTTAR PRADESH",
    "mp": "MADHYA PRADESH",
    "ap": "ANDHRA PRADESH",
    "wb": "WEST BENGAL",
    "tn": "TAMIL NADU",
    "ts": "TELANGANA",
    "mh": "MAHARASHTRA",
    "pb": "PUNJAB",
    "hr": "HARYANA",
    "rj": "RAJASTHAN",
    "gj": "GUJARAT",
    "od": "ODISHA",
    "kl": "KERALA",
    "br": "BIHAR",
    "jh": "JHARKHAND",
    "cg": "CHHATTISGARH",
    "uk": "UTTARAKHAND",
    "hp": "HIMACHAL PRADESH",
    "dl": "DELHI",
    "jk": "JAMMU AND KASHMIR",
}


INDIC_STOPWORDS: Set[str] = {
    # Question words across Indian languages
    "kiti", "kitna", "kitne", "kitni", "enta", "entha", "enthamandi", "koyti", "koto", "kata",
    "ethanai", "yavathu", "what", "which", "where", "how", "many", "much", "kaha", "kidhar", "kon",
    # Total, Aggregation & Quantifiers
    "kul", "kula", "kool", "ekun", "mot", "mota", "mottam", "mothham", "motham", "mothathil", "moththa",
    "sarva", "pura", "pure", "sab", "sabhi", "total", "sum", "count", "avg", "average", "overall", "all",
    "highest", "lowest", "min", "max",
    # Market, Price, and Financial concepts
    "mandi", "mandis", "mamdi", "mamdiyom", "bhav", "dar", "dhara", "kimat", "vilai", "mulya",
    "price", "prices", "rate", "rates", "madhiri", "mathiri", "disbursement", "disbursed",
    # Agricultural and People terminology
    "kisan", "kisano", "raitu", "raitulu", "raitulaku", "krishak", "krishok", "shatkari", "labharthi",
    "farmer", "farmers", "beneficiary", "beneficiaries", "student", "students", "chatra", "chatrom",
    "vidyarthi", "stri", "mahila", "patient", "patients",
    # Units of Measurement
    "ton", "tons", "tonne", "tonnes", "tana", "hektar", "hectare", "hectares", "crore", "crores",
    "lakh", "lakhs", "rupees", "rs", "inr", "metrik", "metrika", "mandays", "din", "per", "amount", "number",
    # Administrative concepts and state tokens (to prevent false district collisions)
    "jilla", "jillalo", "jille", "jilhe", "zilla", "district", "districts", "state", "states", "rajya",
    "pradesh", "uttar", "uttara", "madhya", "andhra", "paschim", "pashchim", "bengal", "tamil", "nadu",
    "himachal", "arunachal", "jammu", "kashmir", "haveli", "daman", "diu", "shala", "paathashala",
    "vidyalaya", "hospital", "hospitals", "card", "cards", "yojana", "scheme", "gram", "panchayat",
    "village", "villages", "report", "road", "water", "pani", "stunted", "literacy", "shatamsha",
    # Prepositions, Auxiliaries, and Verbs
    "under", "over", "between", "during", "and", "the", "for", "from", "with", "into", "mein", "lo",
    "il", "te", "ye", "ahet", "unnavu", "unnaru", "hai", "hain", "gaye", "diye", "mila", "mili", "mile",
    "pedu", "aagi", "huye", "kiya", "kiye", "hona", "hoti", "hote", "dvara", "dwar", "edi"
}


def strip_indic_locative(word: str) -> str:
    """Strips common vernacular case markers and locatives (-त, -मध्ये, -లో, -இல், -তে)."""
    suffixes = [
        "मध्ये", "ात", "त", "ला", "वर",  # Marathi
        "లో", "లోను", "కు", "కి", "తో",    # Telugu
        "ে", "য়ে", "তে", "র", "দের",     # Bengali
        "ில்", "ல்", "க்கு", "ஐ",        # Tamil
        "में", "से", "को", "का", "की"    # Hindi
    ]
    for s in sorted(suffixes, key=len, reverse=True):
        if word.endswith(s) and len(word) > len(s) + 2:
            return word[:-len(s)]
    return word


class DynamicEntityGrounder:
    """
    In-memory cross-lingual grounder that dynamically maps natural language mentions
    to exact canonical database values across all 20 NDAP databases.
    """

    def __init__(self, parquet_dir: Optional[Path] = None):
        self.parquet_dir = parquet_dir or PARQUET_STORE_DIR
        self.known_states: Set[str] = set()
        self.known_districts: Set[str] = set()
        self.known_commodities: Set[str] = set()
        self.district_to_state: Dict[str, str] = {}
        self._is_initialized = False
        self._populate_database_entities()

    def _populate_database_entities(self) -> None:
        """Introspects parquet stores to load all distinct entity literals."""
        if not HAS_DUCKDB or not self.parquet_dir.exists():
            logger.warning("DuckDB or parquet directory not found; using fallback lexicons.")
            return

        parquet_files = list(self.parquet_dir.glob("*.parquet"))
        if not parquet_files:
            return

        try:
            con = duckdb.connect(database=":memory:")
            for p_file in parquet_files:
                table_name = p_file.stem
                con.execute(f"CREATE VIEW {table_name} AS SELECT * FROM read_parquet('{p_file.resolve()}');")

            # 1. Collect all distinct states (UPPERCASE)
            try:
                states = con.execute("""
                    SELECT DISTINCT UPPER(state_name) 
                    FROM ndap_pm_kisan_disbursement 
                    WHERE state_name IS NOT NULL
                """).fetchall()
                self.known_states = {s[0] for s in states if s[0]}
            except Exception:
                pass

            # 2. Collect all distinct districts (preserving Title Case) across all tables
            try:
                dist_state_rows = con.execute("""
                    SELECT DISTINCT district_name, UPPER(state_name)
                    FROM read_parquet('data/parquet_stores/*.parquet', union_by_name=true) 
                    WHERE district_name IS NOT NULL AND length(trim(district_name)) > 1
                """).fetchall()
                for d, s in dist_state_rows:
                    if d and len(d.strip()) > 1:
                        d_name = d.strip()
                        self.known_districts.add(d_name)
                        if s and s.strip():
                            self.district_to_state[d_name] = s.strip()
            except Exception:
                pass

            # Union comprehensive administrative districts
            try:
                from indicsql.training.dataset_curator import FALLBACK_STATES_AND_DISTRICTS
                for st, dlist in FALLBACK_STATES_AND_DISTRICTS.items():
                    for d in dlist:
                        if d and len(d.strip()) > 1:
                            d_name = d.strip()
                            self.known_districts.add(d_name)
                            if d_name not in self.district_to_state:
                                self.district_to_state[d_name] = st.strip()
            except Exception:
                pass

            # 3. Collect all distinct commodities, crops, and fertilizers (UPPERCASE)
            try:
                commodities = con.execute("""
                    SELECT DISTINCT UPPER(crop_name) FROM ndap_crop_production_census WHERE crop_name IS NOT NULL
                    UNION
                    SELECT DISTINCT UPPER(fertilizer_type) FROM ndap_fertilizer_distribution WHERE fertilizer_type IS NOT NULL
                    UNION
                    SELECT DISTINCT UPPER(commodity) FROM ndap_mandi_commodity_prices WHERE commodity IS NOT NULL
                """).fetchall()
                self.known_commodities = {c[0].strip() for c in commodities if c[0] and len(c[0].strip()) > 1}
            except Exception:
                pass

            con.close()
            self._is_initialized = True
            logger.info(
                f"DynamicEntityGrounder initialized: {len(self.known_states)} states, "
                f"{len(self.known_districts)} districts, {len(self.known_commodities)} commodities."
            )
        except Exception as e:
            logger.warning(f"Could not build dynamic entity index: {e}")

    def ground_entities(self, query: str) -> Dict[str, str]:
        """
        Extracts verified database literals from any vernacular query string.
        Uses algorithmic transliteration, priority-based state recognition,
        and guarded consonant skeleton matching to eliminate false collisions.
        Returns a dictionary with canonical keys: 'state_name', 'district_name', 'commodity'.
        """
        entities: Dict[str, str] = {}
        q_lower = query.lower()

        # Step 1: Direct native script phrase extraction (longest keys first)
        for indic_token, latin_value in sorted(INDIC_SCRIPT_PHONETICS.items(), key=lambda x: len(x[0]), reverse=True):
            if indic_token in query:
                if latin_value in KNOWN_COMMODITIES or latin_value in self.known_commodities:
                    if "commodity" not in entities:
                        entities["commodity"] = latin_value
                elif latin_value.isupper():
                    if "state_name" not in entities:
                        entities["state_name"] = latin_value
                else:
                    if "district_name" not in entities:
                        entities["district_name"] = latin_value

        # Step 2: Algorithmic Transliteration Bridge (Any Indic Script -> Latin ITRANS)
        stemmed_tokens = [strip_indic_locative(w) for w in query.split()]
        stemmed_query = " ".join(stemmed_tokens)
        latin_bridge = transliterate_indic_to_latin(query)
        latin_stemmed = transliterate_indic_to_latin(stemmed_query)
        combined_text = f"{query} {stemmed_query} {latin_bridge} {latin_stemmed}".lower()

        # Step 3: Match States FIRST (Multi-word full names first, then abbreviations)
        if "state_name" not in entities:
            # 3a. Exact state names sorted by length descending
            for state in sorted(self.known_states, key=len, reverse=True):
                pattern = r"\b" + re.escape(state.lower()) + r"\b"
                if re.search(pattern, combined_text):
                    entities["state_name"] = state
                    break

            # 3b. Standard state abbreviations (UP, MP, AP, WB, TN, etc.)
            if "state_name" not in entities:
                for abbr, canonical_state in STATE_ABBREVIATIONS.items():
                    pattern = r"\b" + re.escape(abbr) + r"\b"
                    if re.search(pattern, combined_text):
                        entities["state_name"] = canonical_state
                        break

        # Step 4: Mask matched state tokens from query so they cannot collide with districts
        clean_for_dist = combined_text
        if "state_name" in entities:
            for token in entities["state_name"].lower().split():
                if len(token) > 2:
                    clean_for_dist = re.sub(r"\b" + re.escape(token) + r"\b", " ", clean_for_dist)

        # Step 5: Match Districts against dynamic DuckDB catalog
        if "district_name" not in entities:
            # 5a. Direct exact word boundary match
            for district in sorted(self.known_districts, key=len, reverse=True):
                d_clean = district.lower()
                pattern = r"\b" + re.escape(d_clean) + r"\b"
                if re.search(pattern, clean_for_dist):
                    # Relational constraint: If state is known, district must belong to that state
                    if "state_name" in entities:
                        if self.district_to_state.get(district) == entities["state_name"]:
                            entities["district_name"] = district
                            break
                    else:
                        entities["district_name"] = district
                        break

            # 5b. Guarded Consonant Skeleton match (strict length, no 2-letter skeletons, relational check)
            if "district_name" not in entities:
                dist_words = [
                    w for w in re.findall(r"[a-zA-Z0-9]+", clean_for_dist)
                    if w not in INDIC_STOPWORDS and len(w) >= 3
                ]
                for w in dist_words:
                    w_sk = consonant_skeleton(w)
                    if len(w_sk) < 3:
                        continue  # Strictly disallow 2-letter skeleton matching (kl, tr, nd, tn, etc.)

                    for district in self.known_districts:
                        d_sk = consonant_skeleton(district)
                        # Require exact skeleton match and word-length proximity <= 2
                        if len(d_sk) >= 3 and d_sk == w_sk and abs(len(w) - len(district)) <= 2:
                            if "state_name" in entities:
                                if self.district_to_state.get(district) == entities["state_name"]:
                                    entities["district_name"] = district
                                    break
                            else:
                                entities["district_name"] = district
                                break
                    if "district_name" in entities:
                        break

        # Step 6: Match Commodities & Fertilizers (e.g. WHEAT, DAP, UREA, RICE, COTTON)
        if "commodity" not in entities:
            for comm in self.known_commodities:
                c_clean = comm.lower()
                pattern = r"\b" + re.escape(c_clean) + r"\b"
                if re.search(pattern, combined_text):
                    entities["commodity"] = comm
                    break

        # Step 7: Automatically infer state if district is grounded but state is omitted
        if "district_name" in entities and "state_name" not in entities:
            dist = entities["district_name"]
            if dist in self.district_to_state:
                entities["state_name"] = self.district_to_state[dist]

        return entities


# Singleton instance for high-speed sub-millisecond reuse
dynamic_entity_grounder = DynamicEntityGrounder()

