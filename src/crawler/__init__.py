# SEG301-OverFitting Crawler Module
# Optimized for infodoanhnghiep.com

from .spider import start_spider
from .parser import parse_company_list, parse_company_detail, is_empty_page
from .utils import normalize_text, get_now_iso

__all__ = [
    'start_spider',
    'parse_company_list',
    'parse_company_detail',
    'is_empty_page',
    'normalize_text',
    'get_now_iso'
]
