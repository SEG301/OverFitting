import re
from bs4 import BeautifulSoup
from .utils import normalize_text, get_now_iso

# Try import pyvi for Word Segmentation
try:
    from pyvi import ViTokenizer
except ImportError:
    ViTokenizer = None

def parse_company_list(html_content, base_url=""):
    """
    Parses the infodoanhnghiep.com listing page and extracts company details.
    Includes data cleaning and word segmentation.
    """
    soup = BeautifulSoup(html_content, 'lxml')
    items = soup.select('div.company-item')
    
    if not items:
        return []

    results = []
    for div in items:
        h3 = div.select_one('h3.company-name a')
        if not h3:
            continue
        
        name_raw = h3.get_text(strip=True)
        name_norm = normalize_text(name_raw)
        
        link = h3.get('href', '')
        text = div.get_text(separator=' ', strip=True)
        
        # Extract Tax Code (Clean: Regex)
        tax_code = ''
        mst_match = re.search(r'Mã số thuế:\s*(\d+)', text)
        if mst_match:
            tax_code = mst_match.group(1)
        
        # Validation: Tax code must be at least 10 digits (or 13 for branches)
        if not tax_code or len(tax_code) < 9:
            continue

        # Extract Address
        addr_norm = ""
        addr_match = re.search(r'Địa chỉ:\s*(.*?)(?:$|Mã số thuế|Đại diện)', text)
        if addr_match:
             addr_norm = normalize_text(addr_match.group(1))
        elif "Địa chỉ:" in text:
             addr_norm = normalize_text(text.split("Địa chỉ:")[-1])

        # Construct Document
        item = {
            'company_name': name_norm,
            'tax_code': tax_code,
            'address': addr_norm,
            'company_name_seg': '',
            'address_seg': '',
            'source': 'InfoDoanhNghiep',
            'url': link if link.startswith('http') else (base_url + link) if link.startswith('/') else (base_url + "/" + link), 
            'crawled_at': get_now_iso()
        }
        
        # Word Segmentation (Milestone 1 requirement)
        if ViTokenizer:
            try:
                item['company_name_seg'] = ViTokenizer.tokenize(item['company_name'])
                item['address_seg'] = ViTokenizer.tokenize(item['address'])
            except:
                pass
        else:
            # Fallback for simple cleaning if pyvi is missing
            item['company_name_seg'] = item['company_name'].replace(" ", "_")

        results.append(item)
            
    return results

def is_empty_page(html_content):
    """Detects if the page has no data based on site-specific markers."""
    return "Không tìm thấy" in html_content
