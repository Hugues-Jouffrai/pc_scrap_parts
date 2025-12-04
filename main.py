import asyncio
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from scraper import AntigravityScraper
from analyzer import AntigravityAnalyzer

console = Console()

async def main():
    console.print(Panel.fit("[bold cyan]LBC-Arbitrage: The Antigravity Tool[/bold cyan]", border_style="cyan"))
    
    # Get URL from args or input
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
    else:
        target_url = console.input("[bold yellow]🔗 Enter Leboncoin URL: [/bold yellow]")

    if not target_url:
        rprint("[bold red]❌ No URL provided. Exiting.[/bold red]")
        return

    scraper = AntigravityScraper()
    analyzer = AntigravityAnalyzer()
    
    # 1. Scrape
    with console.status("[bold green]Scraping Leboncoin...[/bold green]", spinner="dots"):
        data = await scraper.get_listing_data(target_url)
    
    if data:
        # 2. Analyze
        with console.status("[bold purple]Analyzing with GPT-4o...[/bold purple]", spinner="earth"):
            analysis = analyzer.analyze_profitability(data)
        
        # 3. Output Results
        listing_price = analysis.get('listing_price', 0)
        total_estimated = analysis.get('total_estimated_value', 0)
        profit = analysis.get('profit_potential', 0)
        margin = analysis.get('profit_percentage', 0)
        verdict = analysis.get('verdict', 'UNKNOWN')

        # Color code the verdict
        verdict_color = "green" if verdict == "BUY" else "red"
        if verdict == "TRASH": verdict_color = "black on red"

        # Create Summary Table
        table = Table(title=f"Analysis Results: {data['title'][:50]}...")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bold white")

        table.add_row("Listing Price", f"{listing_price}€")
        table.add_row("Estimated Value", f"{total_estimated}€")
        table.add_row("Profit", f"{profit}€")
        table.add_row("Margin", f"{margin}%")
        table.add_row("Verdict", f"[{verdict_color}]{verdict}[/{verdict_color}]")

        console.print(table)
        
        # Parts Breakdown
        rprint("\n[bold]🛠️  PARTS BREAKDOWN:[/bold]")
        parts_table = Table(show_header=True, header_style="bold magenta")
        parts_table.add_column("Component")
        parts_table.add_column("Est. Price", justify="right")
        parts_table.add_column("Notes")

        for part in analysis.get('parts', []):
            parts_table.add_row(
                part['component'], 
                f"{part['estimated_price']}€", 
                part.get('notes', '')
            )
        
        console.print(parts_table)
        
        rprint(f"\n[bold]📝 Reasoning:[/bold] {analysis.get('reasoning', 'No reasoning provided.')}")
        rprint(f"[dim]URL: {data['url']}[/dim]")

    else:
        rprint("[bold red]❌ Failed to retrieve data.[/bold red]")

if __name__ == "__main__":
    asyncio.run(main())
