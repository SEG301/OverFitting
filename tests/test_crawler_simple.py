"""
Simple Test for Crawler Module
SEG301 - Milestone 1
"""

import pytest
from src.crawler.parser import parse_company_list, parse_company_detail, is_empty_page
from src.crawler.utils import normalize_text, get_now_iso


class TestUtils:
    """Test utility functions"""
    
    def test_normalize_text(self):
        """Test text normalization"""
        # Test whitespace removal
        assert normalize_text("  Hello   World  ") == "Hello World"
        
        # Test empty string
        assert normalize_text("") == ""
        
        # Test Vietnamese text
        text = "Công  ty   TNHH"
        assert normalize_text(text) == "Công ty TNHH"
    
    def test_get_now_iso(self):
        """Test ISO timestamp generation"""
        timestamp = get_now_iso()
        assert timestamp is not None
        assert "T" in timestamp  # ISO format contains T
        assert len(timestamp) > 10


class TestParser:
    """Test parser functions"""
    
    def test_is_empty_page(self):
        """Test empty page detection"""
        # Empty page
        html = "<html><body>Không tìm thấy kết quả</body></html>"
        assert is_empty_page(html) == True
        
        # Non-empty page
        html = "<html><body>Có dữ liệu</body></html>"
        assert is_empty_page(html) == False
    
    def test_parse_company_list_empty(self):
        """Test parsing empty company list"""
        html = "<html><body></body></html>"
        result = parse_company_list(html)
        assert result == []
    
    def test_parse_company_list_with_data(self):
        """Test parsing company list with valid data"""
        html = """
        <html>
        <body>
            <div class="company-item">
                <h3 class="company-name">
                    <a href="/company/123">CÔNG TY TNHH TEST</a>
                </h3>
                <div>Mã số thuế: 0123456789</div>
                <div>Địa chỉ: Hà Nội</div>
            </div>
        </body>
        </html>
        """
        result = parse_company_list(html, base_url="https://example.com")
        
        assert len(result) == 1
        assert result[0]['company_name'] == "CÔNG TY TNHH TEST"
        assert result[0]['tax_code'] == "0123456789"
        assert result[0]['address'] == "Hà Nội"
        assert 'url' in result[0]
        assert 'crawled_at' in result[0]
    
    def test_parse_company_list_invalid_tax_code(self):
        """Test that companies with invalid tax codes are filtered"""
        html = """
        <html>
        <body>
            <div class="company-item">
                <h3 class="company-name">
                    <a href="/company/123">CÔNG TY TEST</a>
                </h3>
                <div>Mã số thuế: 123</div>
            </div>
        </body>
        </html>
        """
        result = parse_company_list(html)
        # Should be empty because tax code is too short
        assert len(result) == 0
    
    def test_parse_company_detail(self):
        """Test parsing company detail page"""
        html = """
        <html>
        <body>
            <div itemprop="founder">
                <span itemprop="name">Nguyễn Văn A</span>
            </div>
            <div itemprop="telephone">0901234567</div>
            <div class="responsive-table-cell-head">Tình trạng hoạt động</div>
            <div class="responsive-table-cell">Đang hoạt động</div>
        </body>
        </html>
        """
        result = parse_company_detail(html)
        
        assert 'representative' in result
        assert result['representative'] == "Nguyễn Văn A"
        assert 'phone' in result
        assert result['phone'] == "0901234567"
        assert 'status' in result
        assert result['status'] == "Đang hoạt động"


class TestIntegration:
    """Integration tests"""
    
    def test_full_workflow(self):
        """Test complete parsing workflow"""
        # Sample HTML from listing page
        listing_html = """
        <html>
        <body>
            <div class="company-item">
                <h3 class="company-name">
                    <a href="/company/test">CÔNG TY CỔ PHẦN ABC</a>
                </h3>
                <div>Mã số thuế: 0111222333</div>
                <div>Địa chỉ: 123 Đường ABC, Hà Nội</div>
            </div>
        </body>
        </html>
        """
        
        companies = parse_company_list(listing_html, base_url="https://test.com")
        
        assert len(companies) == 1
        company = companies[0]
        
        # Check all required fields
        assert company['company_name'] == "CÔNG TY CỔ PHẦN ABC"
        assert company['tax_code'] == "0111222333"
        assert company['address'] == "123 Đường ABC, Hà Nội"
        assert company['source'] == "InfoDoanhNghiep"
        assert company['url'].startswith("https://test.com")
        
        # Check word segmentation fields exist
        assert 'company_name_seg' in company
        assert 'address_seg' in company


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
