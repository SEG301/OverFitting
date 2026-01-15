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

def parse_company_detail(html_content):
    """
    Parses the company detail page.
    Extracts: Representative, Phone, Status, Founded Date, Detailed Industry List.
    """
    soup = BeautifulSoup(html_content, 'lxml')
    data = {}
    
    # Representative
    founder = soup.select_one('[itemprop="founder"] [itemprop="name"]')
    if founder:
        data['representative'] = normalize_text(founder.get_text(strip=True))
    
    # Phone
    phone = soup.find(itemprop="telephone")
    if phone:
        data['phone'] = normalize_text(phone.get_text(strip=True))
    
    # Table Info (Status, Founded Date)
    cells = soup.select('.responsive-table-cell-head')
    for cell in cells:
        label = cell.get_text(strip=True)
        value_cell = cell.find_next_sibling(class_="responsive-table-cell")
        if not value_cell:
            continue
        
        value = normalize_text(value_cell.get_text(strip=True))
        if "Tình trạng hoạt động" in label:
            data['status'] = value
        elif "Ngày cấp" in label:
            data['founded_date'] = value

    # Detailed Industries (Robust flat structure)
    industries = []
    ind_table = soup.select_one('.nnkd-table')
    if ind_table:
        # Find all code cells (they have the head class)
        code_cells = ind_table.select('.responsive-table-cell.responsive-table-cell-head')
        for code_cell in code_cells:
            code_text = normalize_text(code_cell.get_text(strip=True))
            if code_text == "Mã" or not code_text: 
                continue # Skip header or empty
                
            # The name cell is the next sibling div with the basic class
            name_cell = code_cell.find_next_sibling('div', class_='responsive-table-cell')
            if name_cell:
                name_text = normalize_text(name_cell.get_text(strip=True))
                industries.append({
                    'code': code_text,
                    'name': name_text
                })
    data['industries_detail'] = industries
    
    return data

def is_empty_page(html_content):
    """Detects if the page has no data based on site-specific markers."""
    return "Không tìm thấy" in html_content
