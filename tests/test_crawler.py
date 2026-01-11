"""
Test Crawler Module
SEG301 - Milestone 1
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock


class TestBaseCrawler:
    """Tests for AsyncCrawler base class"""
    
    def test_import(self):
        """Test that modules can be imported"""
        from src.crawler.base_crawler import AsyncCrawler
        assert AsyncCrawler is not None
    
    @pytest.mark.asyncio
    async def test_checkpoint_save_load(self):
        """Test checkpoint save and load functionality"""
        from src.crawler.utils import save_checkpoint, load_checkpoint
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            checkpoint_file = f.name
        
        try:
            # Save checkpoint
            test_data = {
                'crawled_urls': ['url1', 'url2'],
                'total_crawled': 2
            }
            await save_checkpoint(checkpoint_file, test_data)
            
            # Load checkpoint
            loaded = await load_checkpoint(checkpoint_file)
            assert loaded is not None
            assert loaded['total_crawled'] == 2
            assert len(loaded['crawled_urls']) == 2
        finally:
            os.unlink(checkpoint_file)


class TestParser:
    """Tests for DataParser"""
    
    def test_clean_html(self):
        """Test HTML cleaning"""
        from src.crawler.parser import DataParser
        
        parser = DataParser(use_segmentation=False)
        
        html = "<p>Hello <script>alert('x')</script> World</p>"
        cleaned = parser.clean_html(html)
        
        assert 'script' not in cleaned.lower()
        assert 'Hello' in cleaned
        assert 'World' in cleaned
    
    def test_extract_phone(self):
        """Test phone number extraction"""
        from src.crawler.parser import DataParser
        
        parser = DataParser(use_segmentation=False)
        
        text = "Liên hệ: 0901234567 hoặc 028-1234-5678"
        phones = parser.extract_phone_numbers(text)
        
        assert len(phones) >= 1
    
    def test_extract_tax_code(self):
        """Test tax code extraction"""
        from src.crawler.parser import DataParser
        
        parser = DataParser(use_segmentation=False)
        
        text = "Mã số thuế: 0100109106"
        tax_code = parser.extract_tax_code(text)
        
        assert tax_code == "0100109106"


class TestUtils:
    """Tests for utility functions"""
    
    def test_deduplicate(self):
        """Test deduplication"""
        from src.crawler.utils import deduplicate
        
        items = [
            {'tax_code': '123', 'name': 'A'},
            {'tax_code': '123', 'name': 'A copy'},  # Duplicate
            {'tax_code': '456', 'name': 'B'},
        ]
        
        unique = deduplicate(items, key_field='tax_code')
        assert len(unique) == 2
    
    def test_compute_statistics(self):
        """Test statistics computation"""
        from src.crawler.utils import compute_statistics
        
        items = [
            {'source': 'masothue', 'tax_code': '123', 'company_name': 'Test Company', 'address': 'Hà Nội'},
            {'source': 'masothue', 'tax_code': '456', 'company_name': 'Another', 'address': ''},
        ]
        
        stats = compute_statistics(items)
        
        assert stats['total_documents'] == 2
        assert stats['has_tax_code'] == 2
        assert stats['has_address'] == 1


class TestMasothueCrawler:
    """Tests for Masothue crawler"""
    
    def test_import(self):
        """Test import"""
        from src.crawler.masothue_crawler import MasothueCrawler
        assert MasothueCrawler is not None
    
    @pytest.mark.asyncio
    async def test_parse_page(self):
        """Test parsing company page"""
        from src.crawler.masothue_crawler import MasothueCrawler
        
        crawler = MasothueCrawler(output_dir='test_data')
        
        mock_html = """
        <html>
        <h1>0100109106 - CÔNG TY CỔ PHẦN FPT</h1>
        <table class="table-taxinfo">
            <tr><td>Địa chỉ</td><td>Tầng 22 Keangnam</td></tr>
            <tr><td>Trạng thái</td><td>Đang hoạt động</td></tr>
        </table>
        </html>
        """
        
        result = await crawler.parse_page('https://masothue.com/0100109106-fpt', mock_html)
        
        assert result is not None
        assert result['tax_code'] == '0100109106'
        assert 'FPT' in result['company_name']


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
