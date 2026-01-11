"""
Hosocongty.vn Crawler
SEG301 - Milestone 1: Data Acquisition

Crawl thông tin doanh nghiệp từ hosocongty.vn:
- Tên công ty
- Mã số thuế
- Địa chỉ
- Ngành nghề kinh doanh
- Vốn điều lệ
- Thông tin liên hệ
"""

import asyncio
import re
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup
from datetime import datetime
from .base_crawler import AsyncCrawler, logger
from .parser import DataParser


class HosocongyCrawler(AsyncCrawler):
    """Crawler for hosocongty.vn"""
    
    BASE_URL = "https://hosocongty.vn"
    
    # Các tỉnh/thành phố để crawl
    PROVINCES = [
        'ha-noi', 'ho-chi-minh', 'da-nang', 'hai-phong', 'can-tho',
        'an-giang', 'ba-ria-vung-tau', 'bac-giang', 'bac-kan', 'bac-lieu',
        'bac-ninh', 'ben-tre', 'binh-dinh', 'binh-duong', 'binh-phuoc',
        'binh-thuan', 'ca-mau', 'cao-bang', 'dak-lak', 'dak-nong',
        'dien-bien', 'dong-nai', 'dong-thap', 'gia-lai', 'ha-giang',
        'ha-nam', 'ha-tinh', 'hai-duong', 'hau-giang', 'hoa-binh',
        'hung-yen', 'khanh-hoa', 'kien-giang', 'kon-tum', 'lai-chau',
        'lam-dong', 'lang-son', 'lao-cai', 'long-an', 'nam-dinh',
        'nghe-an', 'ninh-binh', 'ninh-thuan', 'phu-tho', 'phu-yen',
        'quang-binh', 'quang-nam', 'quang-ngai', 'quang-ninh', 'quang-tri',
        'soc-trang', 'son-la', 'tay-ninh', 'thai-binh', 'thai-nguyen',
        'thanh-hoa', 'thua-thien-hue', 'tien-giang', 'tra-vinh', 'tuyen-quang',
        'vinh-long', 'vinh-phuc', 'yen-bai'
    ]
    
    def __init__(
        self,
        output_dir: str = "data",
        provinces: List[str] = None,
        max_pages_per_province: int = 1000,
        **kwargs
    ):
        super().__init__(name="hosocongty", output_dir=output_dir, **kwargs)
        self.provinces = provinces or self.PROVINCES
        self.max_pages_per_province = max_pages_per_province
        self.parser = DataParser()
        self.company_urls: List[str] = []
    
    async def get_company_urls_from_province(self, province: str) -> List[str]:
        """Lấy danh sách URL công ty từ một tỉnh/thành"""
        urls = []
        page = 1
        
        while page <= self.max_pages_per_province:
            page_url = f"{self.BASE_URL}/tinh-thanh/{province}?page={page}"
            html = await self.fetch(page_url)
            
            if not html:
                break
            
            soup = BeautifulSoup(html, 'lxml')
            
            # Find company links
            company_links = soup.select('a.company-link, div.company-item a[href*="/cong-ty/"]')
            
            if not company_links:
                # Try alternative selector
                company_links = soup.select('a[href*="/cong-ty/"]')
            
            if not company_links:
                break
            
            for link in company_links:
                href = link.get('href', '')
                if href and '/cong-ty/' in href:
                    full_url = href if href.startswith('http') else f"{self.BASE_URL}{href}"
                    urls.append(full_url)
            
            # Check for next page
            next_page = soup.select_one('a.next, .pagination a:contains("›")')
            if not next_page:
                break
            
            page += 1
        
        logger.info(f"{province}: {len(urls)} companies found")
        return urls
    
    async def get_urls_to_crawl(self) -> List[str]:
        """Lấy tất cả URL công ty cần crawl"""
        if self.company_urls:
            return self.company_urls
        
        for province in self.provinces:
            logger.info(f"Getting companies from province: {province}")
            urls = await self.get_company_urls_from_province(province)
            self.company_urls.extend(urls)
        
        # Loại bỏ duplicates
        self.company_urls = list(set(self.company_urls))
        logger.info(f"Total unique URLs: {len(self.company_urls)}")
        
        return self.company_urls
    
    async def parse_page(self, url: str, html: str) -> Optional[Dict[str, Any]]:
        """Parse trang chi tiết công ty"""
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Company name
            name_elem = soup.select_one('h1.company-name, h1')
            company_name = name_elem.get_text(strip=True) if name_elem else ""
            
            if not company_name:
                return None
            
            data = {
                'id': f"hsc_{hash(url) % 10**12}",
                'source': 'hosocongty',
                'url': url,
                'tax_code': '',
                'company_name': company_name,
                'company_name_segmented': self.parser.segment_text(company_name),
                'address': '',
                'representative': '',
                'phone': '',
                'email': '',
                'website': '',
                'industry': '',
                'capital': '',
                'employees': '',
                'registration_date': '',
                'status': '',
                'description': '',
                'crawled_at': datetime.now().isoformat()
            }
            
            # Extract info from table or divs
            info_items = soup.select('div.info-item, tr.info-row, dl.company-info dt, dl.company-info dd')
            
            current_label = ''
            for item in info_items:
                text = item.get_text(strip=True)
                
                # Try to find label-value pairs
                if ':' in text:
                    parts = text.split(':', 1)
                    label = parts[0].lower().strip()
                    value = parts[1].strip() if len(parts) > 1 else ''
                else:
                    label = text.lower()
                    value = ''
                
                if 'mã số thuế' in label or 'mst' in label:
                    data['tax_code'] = value or self._extract_next_value(item)
                elif 'địa chỉ' in label:
                    data['address'] = value or self._extract_next_value(item)
                elif 'đại diện' in label or 'giám đốc' in label:
                    data['representative'] = value or self._extract_next_value(item)
                elif 'điện thoại' in label:
                    data['phone'] = value or self._extract_next_value(item)
                elif 'email' in label:
                    data['email'] = value or self._extract_next_value(item)
                elif 'website' in label:
                    data['website'] = value or self._extract_next_value(item)
                elif 'ngành nghề' in label:
                    data['industry'] = value or self._extract_next_value(item)
                elif 'vốn điều lệ' in label:
                    data['capital'] = value or self._extract_next_value(item)
                elif 'nhân viên' in label:
                    data['employees'] = value or self._extract_next_value(item)
                elif 'ngày thành lập' in label or 'ngày đăng ký' in label:
                    data['registration_date'] = value or self._extract_next_value(item)
                elif 'trạng thái' in label:
                    data['status'] = value or self._extract_next_value(item)
            
            # Description
            desc_elem = soup.select_one('div.company-description, div.description')
            if desc_elem:
                data['description'] = desc_elem.get_text(strip=True)[:500]
                data['description_segmented'] = self.parser.segment_text(data['description'])
            
            # Add segmented address
            if data['address']:
                data['address_segmented'] = self.parser.segment_text(data['address'])
            
            # Generate proper ID if tax_code available
            if data['tax_code']:
                data['id'] = f"hsc_{data['tax_code']}"
            
            return data
            
        except Exception as e:
            logger.error(f"Error parsing {url}: {e}")
            return None
    
    def _extract_next_value(self, elem) -> str:
        """Extract value from next sibling element"""
        next_elem = elem.find_next_sibling()
        if next_elem:
            return next_elem.get_text(strip=True)
        return ''


async def crawl_hosocongty(
    output_dir: str = "data",
    provinces: List[str] = None,
    limit: int = None,
    resume: bool = True
):
    """Convenience function to run Hosocongty crawler"""
    crawler = HosocongyCrawler(
        output_dir=output_dir,
        provinces=provinces,
        max_concurrent=30,
        rate_limit=0.2
    )
    return await crawler.run(limit=limit, resume=resume)


if __name__ == "__main__":
    # Test crawl 100 companies
    asyncio.run(crawl_hosocongty(limit=100))
