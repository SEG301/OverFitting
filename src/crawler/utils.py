"""
Utility Functions for Crawler
SEG301 - Milestone 1: Data Acquisition
"""

import os
import hashlib
import orjson
import aiofiles
from pathlib import Path
from typing import List, Dict, Any, Set, Optional
from datetime import datetime
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


# ============== Checkpoint Management ==============

async def save_checkpoint(filepath: str, data: dict):
    """Save checkpoint data to file"""
    async with aiofiles.open(filepath, 'wb') as f:
        await f.write(orjson.dumps(data))


async def load_checkpoint(filepath: str) -> Optional[dict]:
    """Load checkpoint data from file"""
    if not os.path.exists(filepath):
        return None
    try:
        async with aiofiles.open(filepath, 'rb') as f:
            content = await f.read()
            return orjson.loads(content)
    except Exception as e:
        logger.error(f"Error loading checkpoint: {e}")
        return None


# ============== JSONL Operations ==============

async def save_jsonl(filepath: str, items: List[dict], mode: str = 'ab'):
    """Save items to JSONL file"""
    async with aiofiles.open(filepath, mode) as f:
        for item in items:
            line = orjson.dumps(item) + b'\n'
            await f.write(line)


async def load_jsonl(filepath: str) -> List[dict]:
    """Load items from JSONL file"""
    items = []
    if not os.path.exists(filepath):
        return items
    
    async with aiofiles.open(filepath, 'rb') as f:
        async for line in f:
            if line.strip():
                items.append(orjson.loads(line))
    return items


def load_jsonl_sync(filepath: str) -> List[dict]:
    """Synchronous version of load_jsonl"""
    items = []
    if not os.path.exists(filepath):
        return items
    
    with open(filepath, 'rb') as f:
        for line in f:
            if line.strip():
                items.append(orjson.loads(line))
    return items


# ============== Deduplication ==============

def compute_content_hash(content: str) -> str:
    """Compute MD5 hash of content for deduplication"""
    return hashlib.md5(content.encode('utf-8')).hexdigest()


def deduplicate(items: List[dict], key_field: str = 'tax_code') -> List[dict]:
    """
    Remove duplicate items based on key field
    If key_field is empty, use content hash
    """
    seen: Set[str] = set()
    unique_items = []
    duplicates = 0
    
    for item in items:
        # Get key for deduplication
        key = item.get(key_field, '')
        
        if not key:
            # Use content hash if no key field
            content = item.get('company_name', '') + item.get('address', '')
            key = compute_content_hash(content)
        
        if key not in seen:
            seen.add(key)
            unique_items.append(item)
        else:
            duplicates += 1
    
    logger.info(f"Deduplication: {len(items)} -> {len(unique_items)} ({duplicates} duplicates removed)")
    return unique_items


def deduplicate_file(input_file: str, output_file: str, key_field: str = 'tax_code'):
    """Deduplicate a JSONL file"""
    items = load_jsonl_sync(input_file)
    unique_items = deduplicate(items, key_field)
    
    with open(output_file, 'wb') as f:
        for item in unique_items:
            f.write(orjson.dumps(item) + b'\n')
    
    return len(unique_items)


# ============== Data Merging ==============

def merge_company_data(
    masothue_data: List[dict],
    hosocongty_data: List[dict],
    reviewcongty_data: List[dict]
) -> List[dict]:
    """
    Merge data from different sources based on tax_code or company_name
    Priority: masothue (official) > hosocongty > reviewcongty
    """
    merged = {}
    
    # Index by tax_code
    for item in masothue_data:
        tax_code = item.get('tax_code', '')
        if tax_code:
            merged[tax_code] = item.copy()
            merged[tax_code]['sources'] = ['masothue']
    
    # Merge hosocongty data
    for item in hosocongty_data:
        tax_code = item.get('tax_code', '')
        if tax_code and tax_code in merged:
            # Add new fields only
            for key, value in item.items():
                if key not in merged[tax_code] or not merged[tax_code][key]:
                    merged[tax_code][key] = value
            merged[tax_code]['sources'].append('hosocongty')
        elif tax_code:
            merged[tax_code] = item.copy()
            merged[tax_code]['sources'] = ['hosocongty']
    
    # Merge reviewcongty data
    for item in reviewcongty_data:
        company_name = item.get('company_name', '').upper()
        
        # Try to find matching company by name
        matched = False
        for tax_code, data in merged.items():
            if company_name and company_name in data.get('company_name', '').upper():
                # Add review data
                data['reviews'] = item.get('reviews', [])
                data['overall_rating'] = item.get('overall_rating', 0)
                data['salary_rating'] = item.get('salary_rating', 0)
                data['culture_rating'] = item.get('culture_rating', 0)
                data['sources'].append('reviewcongty')
                matched = True
                break
        
        if not matched:
            # Add as new item
            key = compute_content_hash(company_name)
            merged[key] = item.copy()
            merged[key]['sources'] = ['reviewcongty']
    
    return list(merged.values())


# ============== Statistics ==============

def compute_statistics(items: List[dict]) -> dict:
    """Compute statistics about the dataset"""
    if not items:
        return {}
    
    stats = {
        'total_documents': len(items),
        'sources': defaultdict(int),
        'has_tax_code': 0,
        'has_address': 0,
        'has_reviews': 0,
        'total_words': 0,
        'avg_doc_length': 0,
        'vocabulary': set(),
        'industries': defaultdict(int),
        'provinces': defaultdict(int),
    }
    
    doc_lengths = []
    
    for item in items:
        # Source counts
        source = item.get('source', 'unknown')
        stats['sources'][source] += 1
        
        # Field presence
        if item.get('tax_code'):
            stats['has_tax_code'] += 1
        if item.get('address'):
            stats['has_address'] += 1
        if item.get('reviews'):
            stats['has_reviews'] += 1
        
        # Document length (word count)
        text = ' '.join([
            str(item.get('company_name', '')),
            str(item.get('address', '')),
            str(item.get('industry', '')),
            str(item.get('description', ''))
        ])
        words = text.split()
        doc_lengths.append(len(words))
        stats['total_words'] += len(words)
        stats['vocabulary'].update(words)
        
        # Industry distribution
        industry = item.get('industry', 'Không xác định')
        if industry:
            stats['industries'][industry[:50]] += 1  # Truncate long industry names
        
        # Province distribution (extract from address)
        address = item.get('address', '')
        for province in ['Hà Nội', 'TP.HCM', 'Hồ Chí Minh', 'Đà Nẵng', 'Hải Phòng', 'Cần Thơ']:
            if province.lower() in address.lower():
                stats['provinces'][province] += 1
                break
    
    # Calculate averages
    stats['avg_doc_length'] = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 0
    stats['vocabulary_size'] = len(stats['vocabulary'])
    
    # Clean up non-serializable fields
    stats['vocabulary'] = None  # Too large to include
    stats['sources'] = dict(stats['sources'])
    stats['industries'] = dict(sorted(stats['industries'].items(), key=lambda x: -x[1])[:20])  # Top 20
    stats['provinces'] = dict(stats['provinces'])
    
    return stats


def generate_report(stats: dict, output_file: str = 'data_statistics.md'):
    """Generate statistics report in Markdown format"""
    report = f"""# Data Statistics Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview
- **Total Documents**: {stats.get('total_documents', 0):,}
- **Vocabulary Size**: {stats.get('vocabulary_size', 0):,} unique words
- **Average Document Length**: {stats.get('avg_doc_length', 0):.1f} words

## Data Quality
- Documents with Tax Code: {stats.get('has_tax_code', 0):,} ({stats.get('has_tax_code', 0) / max(stats.get('total_documents', 1), 1) * 100:.1f}%)
- Documents with Address: {stats.get('has_address', 0):,} ({stats.get('has_address', 0) / max(stats.get('total_documents', 1), 1) * 100:.1f}%)
- Documents with Reviews: {stats.get('has_reviews', 0):,}

## Source Distribution
| Source | Count | Percentage |
|--------|-------|------------|
"""
    
    total = stats.get('total_documents', 1)
    for source, count in stats.get('sources', {}).items():
        report += f"| {source} | {count:,} | {count/total*100:.1f}% |\n"
    
    report += """
## Top Industries
| Industry | Count |
|----------|-------|
"""
    for industry, count in stats.get('industries', {}).items():
        report += f"| {industry[:40]} | {count:,} |\n"
    
    report += """
## Geographic Distribution
| Province | Count |
|----------|-------|
"""
    for province, count in stats.get('provinces', {}).items():
        report += f"| {province} | {count:,} |\n"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"Report generated: {output_file}")
    return report


if __name__ == "__main__":
    # Test functions
    import asyncio
    
    # Test JSONL
    test_items = [
        {'tax_code': '0100109106', 'company_name': 'FPT'},
        {'tax_code': '0100109106', 'company_name': 'FPT'},  # Duplicate
        {'tax_code': '0101234567', 'company_name': 'VNG'},
    ]
    
    # Test deduplication
    unique = deduplicate(test_items)
    print(f"Dedup result: {len(unique)} items")
    
    # Test statistics
    stats = compute_statistics(test_items)
    print(f"Stats: {stats}")
