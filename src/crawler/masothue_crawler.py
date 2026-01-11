"""
Masothue.com Crawler
SEG301 - Milestone 1: Data Acquisition

Crawl thông tin doanh nghiệp từ masothue.com:
- Mã số thuế
- Tên công ty  
- Địa chỉ
- Ngành nghề
- Ngày đăng ký
- Trạng thái hoạt động
"""

import asyncio
import re
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup
from datetime import datetime
from .base_crawler import AsyncCrawler, logger
from .parser import DataParser


class MasothueCrawler(AsyncCrawler):
    """Crawler for masothue.com"""
    
    BASE_URL = "https://masothue.com"
    
    # Danh sách các ngành nghề để crawl
    # Mỗi ngành có nhiều trang, mỗi trang ~20 công ty
    INDUSTRY_PAGES_URL = "https://masothue.com/tra-cuu-ma-so-thue-theo-nganh-nghe"
    
    def __init__(
        self,
        output_dir: str = "data",
        industry_range: tuple = None,  # (start, end) để chia cho team
        max_pages_per_industry: int = 500,
        **kwargs
    ):
        super().__init__(name="masothue", output_dir=output_dir, **kwargs)
        self.industry_range = industry_range
        self.max_pages_per_industry = max_pages_per_industry
        self.parser = DataParser()
        self.industries: List[Dict[str, str]] = []
        self.company_urls: List[str] = []
    
    async def get_industries(self) -> List[Dict[str, str]]:
        """Lấy danh sách các ngành nghề"""
        if self.industries:
            return self.industries
        
        html = await self.fetch(self.INDUSTRY_PAGES_URL)
        if not html:
            logger.error("Failed to fetch industry list")
            return []
        
        soup = BeautifulSoup(html, 'lxml')
        
        # Find all industry links - use the correct selector from website analysis
        industry_links = soup.select('a[href*="/tra-cuu-ma-so-thue-theo-nganh-nghe/"]')
        
        for i, link in enumerate(industry_links, 1):
            href = link.get('href', '')
            name = link.get_text(strip=True)
            
            # Skip if it's the main page link or empty
            if href and name and href != '/tra-cuu-ma-so-thue-theo-nganh-nghe':
                full_url = href if href.startswith('http') else f"{self.BASE_URL}{href}"
                if full_url not in [ind['url'] for ind in self.industries]:
                    self.industries.append({
                        'id': i,
                        'name': name,
                        'url': full_url
                    })
        
        logger.info(f"Found {len(self.industries)} industries")
        return self.industries
    
    async def get_company_urls_from_industry(self, industry_url: str) -> List[str]:
        """Lấy danh sách URL công ty từ một ngành nghề"""
        urls = []
        page = 1
        
        while page <= self.max_pages_per_industry:
            page_url = f"{industry_url}?page={page}" if page > 1 else industry_url
            html = await self.fetch(page_url)
            
            if not html:
                break
            
            soup = BeautifulSoup(html, 'lxml')
            
            # Find company links - they start with tax code (10-13 digits)
            # Pattern: /0312012138-cong-ty-tnhh-xxx
            all_links = soup.select('a[href^="/"]')
            
            found_companies = 0
            for link in all_links:
                href = link.get('href', '')
                # Check if URL starts with tax code pattern
                if href and re.match(r'^/\d{10,13}-', href):
                    full_url = f"{self.BASE_URL}{href}"
                    if full_url not in urls:
                        urls.append(full_url)
                        found_companies += 1
            
            if found_companies == 0:
                break
            
            # Check for next page - look for pagination
            has_next = soup.select_one('a[rel="next"], .pagination a:contains("»"), a.page-link[aria-label="Next"]')
            if not has_next and page > 1:
                # Also check if we got fewer results than expected
                break
            
            page += 1
            
            if page % 10 == 0:
                logger.info(f"Industry page {page}: {len(urls)} companies found")
        
        return urls
    
    async def get_urls_to_crawl(self) -> List[str]:
        """Lấy tất cả URL công ty cần crawl"""
        if self.company_urls:
            return self.company_urls
        
        # Lấy danh sách ngành
        industries = await self.get_industries()
        
        # Áp dụng filter theo range nếu có (để chia cho team)
        if self.industry_range:
            start, end = self.industry_range
            industries = industries[start-1:end]
            logger.info(f"Processing industries {start} to {end}")
        
        # Crawl company URLs từ từng ngành
        for industry in industries:
            logger.info(f"Getting companies from: {industry['name']}")
            urls = await self.get_company_urls_from_industry(industry['url'])
            self.company_urls.extend(urls)
            logger.info(f"Total URLs so far: {len(self.company_urls)}")
        
        # Loại bỏ duplicates
        self.company_urls = list(set(self.company_urls))
        logger.info(f"Total unique URLs: {len(self.company_urls)}")
        
        return self.company_urls
    
    async def parse_page(self, url: str, html: str) -> Optional[Dict[str, Any]]:
        """Parse trang chi tiết công ty"""
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Extract tax code from URL
            tax_code_match = re.search(r'/(\d{10,13})', url)
            tax_code = tax_code_match.group(1) if tax_code_match else None
            
            if not tax_code:
                return None
            
            # Company name
            name_elem = soup.select_one('h1.tax-title, h1')
            company_name = name_elem.get_text(strip=True) if name_elem else ""
            
            # Clean up company name (remove tax code prefix)
            company_name = re.sub(r'^\d{10,13}\s*[-–]\s*', '', company_name)
            
            # Table with company info
            info_table = soup.select_one('table.table-taxinfo, table.tax-info')
            
            data = {
                'id': f"mst_{tax_code}",
                'source': 'masothue',
                'url': url,
                'tax_code': tax_code,
                'company_name': company_name,
                'company_name_segmented': self.parser.segment_text(company_name),
                'address': '',
                'representative': '',
                'phone': '',
                'industry': '',
                'registration_date': '',
                'status': '',
                'crawled_at': datetime.now().isoformat()
            }
            
            if info_table:
                rows = info_table.select('tr')
                for row in rows:
                    label_elem = row.select_one('td:first-child, th')
                    value_elem = row.select_one('td:last-child')
                    
                    if label_elem and value_elem:
                        label = label_elem.get_text(strip=True).lower()
                        value = value_elem.get_text(strip=True)
                        
                        if 'địa chỉ' in label:
                            data['address'] = value
                        elif 'đại diện' in label or 'giám đốc' in label:
                            data['representative'] = value
                        elif 'điện thoại' in label:
                            data['phone'] = value
                        elif 'ngành nghề' in label:
                            data['industry'] = value
                        elif 'ngày cấp' in label or 'ngày đăng ký' in label:
                            data['registration_date'] = value
                        elif 'trạng thái' in label or 'tình trạng' in label:
                            data['status'] = value
            
            # Also check for info in div elements
            info_divs = soup.select('div.tax-info-item, div[class*="info"]')
            for div in info_divs:
                text = div.get_text(strip=True)
                if 'Địa chỉ:' in text and not data['address']:
                    data['address'] = text.replace('Địa chỉ:', '').strip()
            
            # Add segmented address
            if data['address']:
                data['address_segmented'] = self.parser.segment_text(data['address'])
            
            return data
            
        except Exception as e:
            logger.error(f"Error parsing {url}: {e}")
            return None


async def crawl_masothue(
    output_dir: str = "data",
    industry_range: tuple = None,
    limit: int = None,
    resume: bool = True
):
    """Convenience function to run Masothue crawler"""
    crawler = MasothueCrawler(
        output_dir=output_dir,
        industry_range=industry_range,
        max_concurrent=10,  # Very conservative to avoid rate limiting
        rate_limit=1.0  # 1 second between requests
    )
    return await crawler.run(limit=limit, resume=resume)


if __name__ == "__main__":
    # Test crawl 100 companies
    asyncio.run(crawl_masothue(limit=100))
