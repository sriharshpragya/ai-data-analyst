"""
CLI entry point for AI Data Analyst.
Provides interactive chat mode and single-query execution.
"""
import sys
import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box

from app.config import Config
from app.agent import DataAnalystAgent
from app.tools import register_all_tools


console = Console()


def print_banner():
    """Print welcome banner."""
    console.print(Panel.fit(
        "[bold cyan]🤖 AI Data Analyst[/bold cyan]\n"
        "[dim]Talk to your database in plain English[/dim]",
        border_style="cyan",
    ))


def print_trace(trace):
    """Print reasoning trace in a nice format."""
    table = Table(
        title=f"Query completed in {trace.total_duration_ms:.0f}ms",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Iteration", style="dim")
    table.add_column("Tool", style="green")
    table.add_column("Duration", style="yellow")
    table.add_column("Result", style="white")
    
    for tc in trace.tool_calls:
        if isinstance(tc.result, dict):
            if "error" in tc.result:
                result_text = f"[red]❌ {tc.result.get('error')}[/red]"
            elif "row_count" in tc.result:
                result_text = f"[green]✅ {tc.result['row_count']} rows[/green]"
            elif "success" in tc.result and tc.result["success"]:
                result_text = f"[green]✅ Chart: {tc.result.get('title', '')}[/green]"
            elif "table_count" in tc.result:
                result_text = f"[green]✅ {tc.result['table_count']} tables[/green]"
            elif "columns" in tc.result:
                result_text = f"[green]✅ {len(tc.result['columns'])} columns[/green]"
            else:
                result_text = "[green]✅ Success[/green]"
        else:
            result_text = "❓ Unknown"
        
        table.add_row(
            str(tc.iteration),
            tc.tool_name,
            f"{tc.duration_ms:.0f}ms",
            result_text,
        )
    
    if trace.tool_calls:
        console.print(table)


def interactive_mode(agent):
    """Interactive chat mode."""
    print_banner()
    
    console.print("\n[dim]Type your question, 'exit' to quit, or 'help' for examples[/dim]\n")
    
    while True:
        try:
            query = console.input("[bold cyan]You:[/bold cyan] ").strip()
            
            if not query:
                continue
            
            if query.lower() in ("exit", "quit", "bye"):
                console.print("\n[cyan]👋 Goodbye![/cyan]\n")
                break
            
            if query.lower() == "help":
                show_help()
                continue
            
            if query.lower() == "reset":
                agent.reset_conversation()
                console.print("[dim]Conversation reset.[/dim]\n")
                continue
            
            # Show thinking indicator
            with console.status("[cyan]Thinking...[/cyan]", spinner="dots"):
                trace = agent.run(query)
            
            # Show trace
            console.print()
            print_trace(trace)
            
            # Show response
            console.print()
            console.print(Panel(
                Markdown(trace.final_response),
                title="🤖 Analyst",
                border_style="green",
            ))
            
            # Show generated charts
            chart_calls = [tc for tc in trace.tool_calls if tc.tool_name == "create_chart"]
            if chart_calls:
                console.print("\n[dim]📊 Charts generated:[/dim]")
                for tc in chart_calls:
                    if isinstance(tc.result, dict) and tc.result.get("success"):
                        console.print(f"   [green]➜[/green] {tc.result.get('file_path')}")
            
            console.print()
        
        except KeyboardInterrupt:
            console.print("\n\n[yellow]Interrupted. Type 'exit' to quit.[/yellow]\n")
            continue
        
        except Exception as e:
            console.print(f"\n[red]❌ Error: {type(e).__name__}: {e}[/red]\n")


def show_help():
    """Show help and examples."""
    console.print(Panel(
        """[bold]Example Queries:[/bold]

[cyan]Simple Analytics:[/cyan]
  • How many customers do we have?
  • What's our total revenue?
  • Show me all product categories

[cyan]With Charts:[/cyan]
  • Show top 5 products by revenue as a bar chart
  • Monthly revenue trend for last 6 months as a line chart
  • Sales distribution by category as a pie chart

[cyan]Business Insights:[/cyan]
  • Which customer segment brings the most revenue?
  • Compare this month's sales to last month
  • What are our best selling products?

[bold]Commands:[/bold]
  • [green]help[/green]   - Show this help
  • [green]reset[/green]  - Reset conversation
  • [green]exit[/green]   - Quit
""",
        title="📖 Help",
        border_style="cyan",
    ))


# ============================================
# CLI COMMANDS
# ============================================

@click.group()
@click.version_option(version="1.0.0")
def cli():
    """🤖 AI Data Analyst - Talk to your database in plain English."""
    pass


@cli.command()
def chat():
    """Start interactive chat mode."""
    try:
        agent = DataAnalystAgent()
        register_all_tools(agent)
        interactive_mode(agent)
    except Exception as e:
        console.print(f"[red]Failed to start: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("query")
def query(query):
    """Run a single query."""
    try:
        agent = DataAnalystAgent()
        register_all_tools(agent)
        
        with console.status("[cyan]Analyzing...[/cyan]", spinner="dots"):
            trace = agent.run(query)
        
        print_trace(trace)
        console.print()
        console.print(Panel(
            Markdown(trace.final_response),
            title="🤖 Analyst",
            border_style="green",
        ))
        
        chart_calls = [tc for tc in trace.tool_calls if tc.tool_name == "create_chart"]
        if chart_calls:
            console.print("\n[dim]Charts:[/dim]")
            for tc in chart_calls:
                if isinstance(tc.result, dict) and tc.result.get("success"):
                    console.print(f"   {tc.result.get('file_path')}")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
def serve():
    """Start the API server."""
    import uvicorn
    console.print("[cyan]🚀 Starting API server...[/cyan]")
    console.print(f"[dim]API docs: http://localhost:{Config.APP_PORT}/docs[/dim]")
    console.print(f"[dim]Web UI:   http://localhost:{Config.APP_PORT}[/dim]\n")
    
    uvicorn.run(
        "app.api:app",
        host=Config.APP_HOST,
        port=Config.APP_PORT,
        reload=not Config.is_production(),
    )


@cli.command()
def info():
    """Show configuration and status."""
    console.print(Panel.fit(
        f"""[bold]Configuration:[/bold]
  Model:         {Config.LLM_MODEL}
  Database:      {Config.DATABASE_URL.split('@')[-1] if '@' in Config.DATABASE_URL else 'not set'}
  Environment:   {Config.ENVIRONMENT}
  API Host:      {Config.APP_HOST}:{Config.APP_PORT}
  Charts Dir:    {Config.CHARTS_DIR}

[bold]Safety:[/bold]
  Query Timeout: {Config.QUERY_TIMEOUT_SECONDS}s
  Max Query Cost: {Config.MAX_QUERY_COST}
  Max Rows:      {Config.MAX_ROWS_PER_QUERY}
  Default Rows:  {Config.DEFAULT_ROWS_PER_QUERY}

[bold]Agent:[/bold]
  Max Iterations: {Config.MAX_ITERATIONS}
""",
        title="ℹ️  System Info",
        border_style="cyan",
    ))


if __name__ == "__main__":
    cli()
