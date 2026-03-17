import re
import unicodedata
import time
from typing import List, Dict, Any

try:
    from pyvi import ViTokenizer
except ImportError:
    ViTokenizer = None

# ============================================================================
# DICTIONARIES & MAPPINGS
# ============================================================================

# Common synonyms and abbreviations for query expansion
SYNONYMS_MAP = {
    "it": "công nghệ thông tin",
    "dev": "developer",
    "bđs": "bất động sản",
    "cty": "công ty",
    "tnhh": "trách nhiệm hữu hạn",
    "hcm": "hồ chí minh",
    "sg": "sài gòn",
    "hn": "hà nội",
    "ns": "nhân sự",
    "tmcp": "thương mại cổ phần",
    "mkt": "marketing",
    "software": "phần mềm"
}

# Common Vietnamese spelling mistakes / typos (for lightweight fast-correction)
# In a large-scale system, this can be swapped with SymSpell or a BK-Tree edit distance approach
TYPOS_MAP = {
    "cong ti": "công ty",
    "thanh pho": "thành phố",
    "pjat trien": "phát triển",
    "kinh doah": "kinh doanh",
    "san pham": "sản phẩm",
    "nha nuoc": "nhà nước"
}

# ============================================================================
# NLP QUERY PROCESSOR
# ============================================================================

class QueryProcessor:
    """
    Lightweight and fast NLP pipeline for Vietnamese Search Queries.
    Execution target: < 5ms per query.
    """
    def __init__(self, use_segmentation: bool = True):
        # Enable PyVi segmentation only if the library is successfully loaded
        self.use_segmentation = use_segmentation and (ViTokenizer is not None)
        
        # Precompile regex replacements for blazing fast correction
        self._typo_regexes = [
            (re.compile(r'\b' + re.escape(wrong) + r'\b'), correct)
            for wrong, correct in TYPOS_MAP.items()
        ]

    def normalize_text(self, text: str) -> str:
        """
        1. Formats Unicode strings to combined characters (NFC) resolving visual bugs.
        2. Lowercases text.
        3. Strips whitespace and ensures singular spaces.
        """
        if not text:
            return ""
        # 1. Unicode Normalization (critical for Vietnamese diacritics)
        text = unicodedata.normalize("NFC", text)
        
        # 2. Lowercase
        text = text.lower().strip()
        
        # 3. Remove redundant spaces
        text = re.sub(r'\s+', ' ', text)
        return text

    def correct_spelling(self, text: str) -> str:
        """
        Replaces common typographical errors utilizing regex word boundaries.
        Highly optimized for O(n) replacement.
        """
        for pattern, correct in self._typo_regexes:
            text = pattern.sub(correct, text)
        return text

    def expand_query(self, text: str) -> str:
        """
        Expands abbreviations and acronyms to their full forms.
        Appends synonyms back into the document context layout to increase Recall.
        """
        words = text.split()
        expanded_words = []
        for w in words:
            expanded_words.append(w)
            
            # If word has a synonym, add the synonym as well for better recall
            # (e.g. 'cty it' -> 'cty công ty it công nghệ thông tin')
            if w in SYNONYMS_MAP:
                expanded_words.append(SYNONYMS_MAP[w])
                
        return " ".join(expanded_words)

    def tokenize(self, text: str) -> List[str]:
        """
        Performs Vietnamese word segmentation. 
        Outputs merged compound words with underscores (e.g. công_ty).
        """
        if self.use_segmentation:
            # PyVi groups phrases: "trách nhiệm hữu hạn" -> "trách_nhiệm hữu_hạn"
            segmented = ViTokenizer.tokenize(text)
            return segmented.split()
        else:
            return text.split()

    def process(self, raw_query: str) -> Dict[str, Any]:
        """
        Executes the main pipeline:
        raw query -> normalize -> correct -> expand -> tokenize
        """
        t0 = time.perf_counter()
        
        # Step 1: Text Normalization
        norm_text = self.normalize_text(raw_query)
        
        # Step 2: Spell Check / Typos 
        corrected_text = self.correct_spelling(norm_text)
        
        # Step 3: Query Expansion (Synonyms mapping)
        expanded_text = self.expand_query(corrected_text)
        
        # Step 4: Vietnamese Tokenization
        tokens = self.tokenize(expanded_text)
        
        # Metadata wrap up
        final_query = " ".join(tokens)
        execution_time_ms = (time.perf_counter() - t0) * 1000
        
        return {
            "raw": raw_query,
            "normalized": norm_text,
            "corrected": corrected_text,
            "expanded": expanded_text,
            "tokens": tokens,
            "final_string": final_query,
            "time_ms": execution_time_ms
        }

# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("--- NLP Query Processor Initialization ---")
    processor = QueryProcessor()
    print(f"Vietnamese Segmenter Active: {processor.use_segmentation}\n")
    
    test_queries = [
        "      Cty     it   ở   HCM   ",
        "cong ti Pjat trien BĐS",
        "Tuyển dev TNHH MKT"
    ]
    
    for q in test_queries:
        res = processor.process(q)
        
        print(f"Raw Input: '{res['raw']}'")
        print(f"  ├─ 1. Norm: {res['normalized']}")
        print(f"  ├─ 2. Edit: {res['corrected']}")
        print(f"  ├─ 3. Exp:  {res['expanded']}")
        print(f"  ├─ 4. Toks: {res['tokens']}")
        print(f"  └─ ⏰ Execution Time: {res['time_ms']:.3f} ms\n")
