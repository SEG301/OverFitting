"""
Main CLI Entry Point for Crawlers
SEG301 - Milestone 1: Data Acquisition

Usage:
    python -m src.crawler.main --source masothue --limit 100
    python -m src.crawler.main --source all
    python -m src.crawler.main --resume
    python -m src.crawler.main --stats data/masothue_*.jsonl
"""

import asyncio
import click
import glob
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from .masothue_crawler import MasothueCrawler
from .hosocongty_crawler import HosocongyCrawler
from .reviewcongty_crawler import ReviewcongtyCrawler
from .utils import (
    load_jsonl_sync, deduplicate_file, merge_company_data,
    compute_statistics, generate_report
)

console = Console()


@click.group()
def cli():
    """SEG301 Enterprise Data Crawler"""
    pass


@cli.command()
@click.option('--source', '-s', multiple=True, 
              type=click.Choice(['masothue', 'hosocongty', 'reviewcongty', 'all']),
              default=['all'], help='Data source to crawl')
@click.option('--limit', '-l', type=int, default=None, help='Limit number of items to crawl')
@click.option('--output', '-o', default='data', help='Output directory')
@click.option('--resume/--no-resume', default=True, help='Resume from checkpoint')
@click.option('--industries', type=str, default=None, 
              help='Industry range for masothue (e.g., "1-25")')
@click.option('--concurrent', '-c', type=int, default=30, help='Max concurrent requests')
def crawl(source, limit, output, resume, industries, concurrent):
    """Run the crawler for specified sources"""
    
    console.print(f"[bold green]🚀 Starting crawler...[/bold green]")
    console.print(f"Sources: {source}")
    console.print(f"Output: {output}")
    console.print(f"Resume: {resume}")
    
    if 'all' in source:
        source = ['masothue', 'hosocongty', 'reviewcongty']
    
    # Parse industry range
    industry_range = None
    if industries:
        try:
            start, end = map(int, industries.split('-'))
            industry_range = (start, end)
            console.print(f"Industry range: {start} to {end}")
        except ValueError:
            console.print("[red]Invalid industry range format. Use 'start-end'[/red]")
            return
    
    async def run_crawlers():
        results = {}
        
        for src in source:
            console.print(f"\n[bold blue]📥 Crawling {src}...[/bold blue]")
            
            if src == 'masothue':
                crawler = MasothueCrawler(
                    output_dir=output,
                    industry_range=industry_range,
                    max_concurrent=concurrent
                )
            elif src == 'hosocongty':
                crawler = HosocongyCrawler(
                    output_dir=output,
                    max_concurrent=concurrent
                )
            elif src == 'reviewcongty':
                crawler = ReviewcongtyCrawler(
                    output_dir=output,
                    max_concurrent=concurrent
                )
            else:
                continue
            
            count = await crawler.run(limit=limit, resume=resume)
            results[src] = count
            
            console.print(f"[green]✓ {src}: {count:,} items crawled[/green]")
        
        return results
    
    results = asyncio.run(run_crawlers())
    
    # Summary
    console.print("\n[bold]📊 Crawl Summary[/bold]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Source")
    table.add_column("Items Crawled", justify="right")
    
    total = 0
    for src, count in results.items():
        table.add_row(src, f"{count:,}")
        total += count
    
    table.add_row("[bold]Total[/bold]", f"[bold]{total:,}[/bold]")
    console.print(table)


@cli.command()
@click.option('--input', '-i', required=True, help='Input JSONL file pattern (e.g., "data/*.jsonl")')
@click.option('--output', '-o', required=True, help='Output JSONL file')
@click.option('--key', '-k', default='tax_code', help='Deduplication key field')
def dedup(input, output, key):
    """Deduplicate JSONL files"""
    
    console.print(f"[bold]🔄 Deduplicating...[/bold]")
    
    # Load all matching files
    all_items = []
    for filepath in glob.glob(input):
        console.print(f"Loading: {filepath}")
        items = load_jsonl_sync(filepath)
        all_items.extend(items)
    
    console.print(f"Total items loaded: {len(all_items):,}")
    
    # Deduplicate
    from .utils import deduplicate
    unique_items = deduplicate(all_items, key_field=key)
    
    # Save
    import orjson
    with open(output, 'wb') as f:
        for item in unique_items:
            f.write(orjson.dumps(item) + b'\n')
    
    console.print(f"[green]✓ Saved {len(unique_items):,} unique items to {output}[/green]")


@cli.command()
@click.option('--input', '-i', required=True, help='Input JSONL file pattern')
@click.option('--output', '-o', default='data_statistics.md', help='Output report file')
def stats(input, output):
    """Generate statistics report"""
    
    console.print(f"[bold]📊 Generating statistics...[/bold]")
    
    # Load all matching files
    all_items = []
    for filepath in glob.glob(input):
        console.print(f"Loading: {filepath}")
        items = load_jsonl_sync(filepath)
        all_items.extend(items)
    
    console.print(f"Total items: {len(all_items):,}")
    
    # Compute stats
    statistics = compute_statistics(all_items)
    
    # Display in console
    table = Table(title="Dataset Statistics", show_header=True, header_style="bold magenta")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    
    table.add_row("Total Documents", f"{statistics.get('total_documents', 0):,}")
    table.add_row("Vocabulary Size", f"{statistics.get('vocabulary_size', 0):,}")
    table.add_row("Avg Doc Length", f"{statistics.get('avg_doc_length', 0):.1f} words")
    table.add_row("With Tax Code", f"{statistics.get('has_tax_code', 0):,}")
    table.add_row("With Address", f"{statistics.get('has_address', 0):,}")
    table.add_row("With Reviews", f"{statistics.get('has_reviews', 0):,}")
    
    console.print(table)
    
    # Generate report file
    generate_report(statistics, output)
    console.print(f"[green]✓ Report saved to {output}[/green]")


@cli.command()
@click.option('--masothue', '-m', help='Masothue JSONL file')
@click.option('--hosocongty', '-h', help='Hosocongty JSONL file')
@click.option('--reviewcongty', '-r', help='Reviewcongty JSONL file')
@click.option('--output', '-o', required=True, help='Output merged JSONL file')
def merge(masothue, hosocongty, reviewcongty, output):
    """Merge data from multiple sources"""
    
    console.print(f"[bold]🔗 Merging data sources...[/bold]")
    
    masothue_data = load_jsonl_sync(masothue) if masothue else []
    hosocongty_data = load_jsonl_sync(hosocongty) if hosocongty else []
    reviewcongty_data = load_jsonl_sync(reviewcongty) if reviewcongty else []
    
    console.print(f"Masothue: {len(masothue_data):,} items")
    console.print(f"Hosocongty: {len(hosocongty_data):,} items")
    console.print(f"Reviewcongty: {len(reviewcongty_data):,} items")
    
    merged = merge_company_data(masothue_data, hosocongty_data, reviewcongty_data)
    
    # Save
    import orjson
    with open(output, 'wb') as f:
        for item in merged:
            f.write(orjson.dumps(item) + b'\n')
    
    console.print(f"[green]✓ Merged {len(merged):,} items to {output}[/green]")


@cli.command()
def sample():
    """Create sample data for testing"""
    
    output_dir = Path('data_sample')
    output_dir.mkdir(exist_ok=True)
    
    console.print(f"[bold]📝 Creating sample data...[/bold]")
    
    async def create_sample():
        # Crawl small sample from each source
        for src_name, crawler_class in [
            ('masothue', MasothueCrawler),
            ('hosocongty', HosocongyCrawler),
            ('reviewcongty', ReviewcongtyCrawler)
        ]:
            console.print(f"Sampling {src_name}...")
            crawler = crawler_class(output_dir=str(output_dir), max_concurrent=10)
            await crawler.run(limit=100, resume=False)
    
    asyncio.run(create_sample())
    console.print(f"[green]✓ Sample data created in {output_dir}[/green]")


def main():
    """Main entry point"""
    cli()


if __name__ == "__main__":
    main()
