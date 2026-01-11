"""
Data Parser - Text Cleaning & Vietnamese Word Segmentation
SEG301 - Milestone 1: Data Acquisition
"""

import re
import html
from typing import Optional
from functools import lru_cache

# Lazy import underthesea to speed up module loading
_word_tokenize = None


def get_word_tokenize():
    """Lazy load underthesea word_tokenize"""
    global _word_tokenize
    if _word_tokenize is None:
        try:
            from underthesea import word_tokenize
            _word_tokenize = word_tokenize
        except ImportError:
            print("Warning: underthesea not installed. Using simple tokenization.")
            _word_tokenize = lambda x: x
    return _word_tokenize


class DataParser:
    """
    Parser for cleaning HTML and segmenting Vietnamese text
    """
    
    # Regex patterns for cleaning
    HTML_TAG_PATTERN = re.compile(r'<[^>]+>')
    SCRIPT_PATTERN = re.compile(r'<script[^>]*>.*?</script>', re.DOTALL | re.IGNORECASE)
    STYLE_PATTERN = re.compile(r'<style[^>]*>.*?</style>', re.DOTALL | re.IGNORECASE)
    COMMENT_PATTERN = re.compile(r'<!--.*?-->', re.DOTALL)
    WHITESPACE_PATTERN = re.compile(r'\s+')
    SPECIAL_CHARS_PATTERN = re.compile(r'[^\w\s\u00C0-\u024F\u1E00-\u1EFF.,;:!?\-()@#]')
    
    def __init__(self, use_segmentation: bool = True):
        self.use_segmentation = use_segmentation
        self._tokenize = None
    
    @property
    def tokenize(self):
        """Get tokenize function lazily"""
        if self._tokenize is None and self.use_segmentation:
            self._tokenize = get_word_tokenize()
        return self._tokenize
    
    def clean_html(self, html_text: str) -> str:
        """Remove HTML tags, scripts, styles, and comments"""
        if not html_text:
            return ""
        
        # Decode HTML entities
        text = html.unescape(html_text)
        
        # Remove scripts, styles, comments
        text = self.SCRIPT_PATTERN.sub('', text)
        text = self.STYLE_PATTERN.sub('', text)
        text = self.COMMENT_PATTERN.sub('', text)
        
        # Remove HTML tags
        text = self.HTML_TAG_PATTERN.sub(' ', text)
        
        # Normalize whitespace
        text = self.WHITESPACE_PATTERN.sub(' ', text)
        
        return text.strip()
    
    def normalize_text(self, text: str) -> str:
        """Normalize Vietnamese text"""
        if not text:
            return ""
        
        # Basic normalization
        text = text.strip()
        
        # Remove excess whitespace
        text = self.WHITESPACE_PATTERN.sub(' ', text)
        
        # Remove special characters but keep Vietnamese diacritics
        # text = self.SPECIAL_CHARS_PATTERN.sub('', text)
        
        return text
    
    @lru_cache(maxsize=10000)
    def segment_text(self, text: str) -> str:
        """
        Segment Vietnamese text into words using underthesea
        Words are joined with underscores within compound words
        
        Example: "công ty cổ phần" -> "công_ty cổ_phần"
        """
        if not text or not self.use_segmentation:
            return text
        
        try:
            # Truncate very long text to avoid memory issues
            if len(text) > 5000:
                text = text[:5000]
            
            # Word tokenize with underthesea
            tokenized = self.tokenize(text)
            
            # tokenize returns string with spaces replaced by underscores in compound words
            if isinstance(tokenized, list):
                return ' '.join(tokenized)
            return tokenized
            
        except Exception as e:
            # Fallback to original text if tokenization fails
            print(f"Segmentation error: {e}")
            return text
    
    def extract_text_from_html(self, html_content: str) -> str:
        """Extract and clean text from HTML content"""
        text = self.clean_html(html_content)
        text = self.normalize_text(text)
        return text
    
    def process_company_name(self, name: str) -> dict:
        """Process company name and return both original and segmented versions"""
        name = self.normalize_text(name)
        return {
            'original': name,
            'segmented': self.segment_text(name)
        }
    
    def extract_phone_numbers(self, text: str) -> list:
        """Extract phone numbers from text"""
        pattern = r'(?:\+84|0)[\s.-]?\d{2,3}[\s.-]?\d{3}[\s.-]?\d{3,4}'
        matches = re.findall(pattern, text)
        return [re.sub(r'[\s.-]', '', m) for m in matches]
    
    def extract_email(self, text: str) -> Optional[str]:
        """Extract email from text"""
        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        match = re.search(pattern, text)
        return match.group(0) if match else None
    
    def extract_tax_code(self, text: str) -> Optional[str]:
        """Extract tax code (10-13 digits) from text"""
        pattern = r'\b(\d{10,13})\b'
        match = re.search(pattern, text)
        return match.group(1) if match else None


# Singleton instance for convenience
_parser_instance = None


def get_parser() -> DataParser:
    """Get singleton DataParser instance"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = DataParser()
    return _parser_instance


if __name__ == "__main__":
    # Test the parser
    parser = DataParser()
    
    # Test HTML cleaning
    html_test = """
    <html>
    <script>alert('test')</script>
    <style>.class { color: red; }</style>
    <p>CÔNG TY CỔ PHẦN FPT</p>
    <!-- comment -->
    <div>Địa chỉ: Tầng 22 Keangnam Tower</div>
    </html>
    """
    print("Cleaned HTML:", parser.clean_html(html_test))
    
    # Test word segmentation
    test_text = "Công ty cổ phần FPT hoạt động trong lĩnh vực công nghệ thông tin"
    print("Segmented:", parser.segment_text(test_text))
    
    # Test phone extraction
    phone_text = "Liên hệ: 0901234567 hoặc +84 28 1234 5678"
    print("Phones:", parser.extract_phone_numbers(phone_text))
