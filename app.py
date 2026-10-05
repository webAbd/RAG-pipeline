import sys
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from src.config import settings
from src.logger import setup_logger, logger
from src.processing.rag_chain import build_rag_chain, query_chain
from src.prompts.prompt_router import route_prompt

console = Console()

def start():
    setup_logger(log_level=settings.log_level, log_file=settings.log_file)
    console.print(Panel("[bold cyan]🎓 Grade 9 English AI Tutor[/bold cyan]\nType 'help' for examples, 'exit' to quit", border_style="cyan"))
    console.print("[yellow]Loading knowledge base...[/yellow]")
    try:
        from src.vectordb.vector_store import load_vector_store
        load_vector_store()
        console.print("[green]✅ Ready![/green]\n")
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]"); sys.exit(1)

    while True:
        try: q = Prompt.ask("[bold cyan]Your question[/bold cyan]").strip()
        except (KeyboardInterrupt, EOFError): console.print("\n[yellow]Goodbye![/yellow]"); break
        if not q: continue
        if q.lower() in ("exit","quit"): console.print("[yellow]Goodbye![/yellow]"); break
        try:
            chain = build_rag_chain(prompt_template=route_prompt(q))
            result = query_chain(chain, q)
            console.print(Panel(result["answer"], title="[green]Answer[/green]", border_style="green"))
            if result["sources"]: console.print(f"[dim]Sources: {', '.join(result['sources'])}[/dim]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__": start()
