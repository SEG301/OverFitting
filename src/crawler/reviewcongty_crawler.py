"""
Reviewcongty.com Crawler
SEG301 - Milestone 1: Data Acquisition

Crawl thông tin review công ty từ reviewcongty.com:
- Tên công ty
- Rating
- Nội dung review
- Thông tin salary
- Culture
"""

import asyncio
import re
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup
from datetime import datetime
from .base_crawler import AsyncCrawler, logger
from .parser import DataParser


class ReviewcongtyCrawler(AsyncCrawler):
    """Crawler for reviewcongty.com"""
    
    BASE_URL = "https://reviewcongty.com"
    LISTING_URL = "https://reviewcongty.com/cong-ty"
    
    def __init__(
        self,
        output_dir: str = "data",
        max_listing_pages: int = 5000,
        **kwargs
    ):
        super().__init__(name="reviewcongty", output_dir=output_dir, **kwargs)
        self.max_listing_pages = max_listing_pages
        self.parser = DataParser()
        self.company_urls: List[str] = []
    
    async def get_urls_to_crawl(self) -> List[str]:
        """Lấy tất cả URL công ty cần crawl"""
        if self.company_urls:
            return self.company_urls
        
        page = 1
        while page <= self.max_listing_pages:
            page_url = f"{self.LISTING_URL}?page={page}"
            html = await self.fetch(page_url)
            
            if not html:
                break
            
            soup = BeautifulSoup(html, 'lxml')
            
            # Find company links
            company_links = soup.select('a[href*="/review/"], div.company-card a')
            
            if not company_links:
                # Alternative selectors
                company_links = soup.select('a.company-link, div.list-item a')
            
            if not company_links:
                break
            
            found_new = False
            for link in company_links:
                href = link.get('href', '')
                if href and '/review/' in href:
                    full_url = href if href.startswith('http') else f"{self.BASE_URL}{href}"
                    if full_url not in self.company_urls:
                        self.company_urls.append(full_url)
                        found_new = True
            
            if not found_new:
                break
            
            page += 1
            
            if page % 50 == 0:
                logger.info(f"Listing page {page}: {len(self.company_urls)} companies found")
        
        logger.info(f"Total company URLs: {len(self.company_urls)}")
        return self.company_urls
    
    async def parse_page(self, url: str, html: str) -> Optional[Dict[str, Any]]:
        """Parse trang chi tiết công ty và reviews"""
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Company name
            name_elem = soup.select_one('h1.company-name, h1')
            company_name = name_elem.get_text(strip=True) if name_elem else ""
            
            if not company_name:
                return None
            
            data = {
                'id': f"rcty_{hash(url) % 10**12}",
                'source': 'reviewcongty',
                'url': url,
                'company_name': company_name,
                'company_name_segmented': self.parser.segment_text(company_name),
                'overall_rating': 0.0,
                'total_reviews': 0,
                'salary_rating': 0.0,
                'culture_rating': 0.0,
                'management_rating': 0.0,
                'address': '',
                'industry': '',
                'company_size': '',
                'reviews': [],
                'pros': [],
                'cons': [],
                'crawled_at': datetime.now().isoformat()
            }
            
            # Overall rating
            rating_elem = soup.select_one('div.rating-score, span.rating-value')
            if rating_elem:
                try:
                    data['overall_rating'] = float(rating_elem.get_text(strip=True))
                except ValueError:
                    pass
            
            # Company info
            info_items = soup.select('div.company-info-item, div.info-row')
            for item in info_items:
                text = item.get_text(strip=True).lower()
                if 'địa chỉ' in text:
                    data['address'] = text.replace('địa chỉ:', '').strip()
                elif 'ngành' in text:
                    data['industry'] = text.replace('ngành nghề:', '').replace('ngành:', '').strip()
                elif 'quy mô' in text or 'nhân viên' in text:
                    data['company_size'] = text
            
            # Sub-ratings
            rating_categories = soup.select('div.rating-category, div.sub-rating')
            for cat in rating_categories:
                label = cat.get_text(strip=True).lower()
                value_elem = cat.select_one('span.value, span.score')
                if value_elem:
                    try:
                        value = float(value_elem.get_text(strip=True))
                        if 'lương' in label or 'salary' in label:
                            data['salary_rating'] = value
                        elif 'văn hóa' in label or 'culture' in label:
                            data['culture_rating'] = value
                        elif 'quản lý' in label or 'management' in label:
                            data['management_rating'] = value
                    except ValueError:
                        pass
            
            # Reviews
            review_items = soup.select('div.review-item, div.review-card')
            for review in review_items[:10]:  # Limit to 10 reviews per company
                review_data = {
                    'title': '',
                    'content': '',
                    'rating': 0.0,
                    'position': '',
                    'date': ''
                }
                
                title_elem = review.select_one('h3.review-title, div.title')
                if title_elem:
                    review_data['title'] = title_elem.get_text(strip=True)
                
                content_elem = review.select_one('div.review-content, p.content')
                if content_elem:
                    review_data['content'] = content_elem.get_text(strip=True)
                    review_data['content_segmented'] = self.parser.segment_text(review_data['content'])
                
                rating_elem = review.select_one('span.rating, div.stars')
                if rating_elem:
                    try:
                        review_data['rating'] = float(rating_elem.get_text(strip=True))
                    except ValueError:
                        # Try counting stars
                        stars = rating_elem.select('.star.filled, .fa-star')
                        review_data['rating'] = len(stars)
                
                position_elem = review.select_one('span.position, div.job-title')
                if position_elem:
                    review_data['position'] = position_elem.get_text(strip=True)
                
                date_elem = review.select_one('span.date, time')
                if date_elem:
                    review_data['date'] = date_elem.get_text(strip=True)
                
                if review_data['content']:
                    data['reviews'].append(review_data)
            
            data['total_reviews'] = len(data['reviews'])
            
            # Pros and Cons
            pros_section = soup.select('div.pros li, ul.pros li')
            data['pros'] = [p.get_text(strip=True) for p in pros_section]
            
            cons_section = soup.select('div.cons li, ul.cons li')
            data['cons'] = [c.get_text(strip=True) for c in cons_section]
            
            return data
            
        except Exception as e:
            logger.error(f"Error parsing {url}: {e}")
            return None


async def crawl_reviewcongty(
    output_dir: str = "data",
    limit: int = None,
    resume: bool = True
):
    """Convenience function to run Reviewcongty crawler"""
    crawler = ReviewcongtyCrawler(
        output_dir=output_dir,
        max_concurrent=20,  # Lower concurrency for review site
        rate_limit=0.3
    )
    return await crawler.run(limit=limit, resume=resume)


if __name__ == "__main__":
    # Test crawl 50 companies
    asyncio.run(crawl_reviewcongty(limit=50))
