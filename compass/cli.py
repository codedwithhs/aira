import typer
from pathlib import Path
from rich.console import Console
from compass.config import load_config
from compass.orchestrator import Orchestrator

# Create a Typer app instance and a Rich Console for beautiful output
app = typer.Typer(
    name="compass",
    help="🧭 The open-source AI agent that automates incident response.",
    add_completion=False,
    rich_markup_mode="markdown"
)

console = Console()

# Define the default config path, but allow it to be overridden.
DEFAULT_CONFIG_PATH = Path.home() / ".compass" / "config.yaml"

# Create a reusable Typer Option for the config path.
ConfigPathOption = typer.Option(
    DEFAULT_CONFIG_PATH,
    "--config",
    "-c",
    help="Path to the Compass config file.",
    show_default=f"Default: {DEFAULT_CONFIG_PATH}",
    exists=True,
    file_okay=True,
    dir_okay=False,
    readable=True,
)


@app.command()
def doctor(config_path: Path = ConfigPathOption):
    """
    Checks the configuration file and validates all configured connections.
    """
    console.print("🩺 Running [bold cyan]Compass Doctor[/bold cyan]...", justify="center")
    
    all_healthy = True

    try:
        # Step 1: Load and validate the configuration file itself
        console.print("\n[bold]1. Loading Configuration...[/bold]")
        config = load_config(config_path)
        console.print("[green]✅ Configuration file found and parsed successfully.[/green]")

        # Step 2: Initialize the Orchestrator, which initializes all connectors
        console.print("\n[bold]2. Initializing Connectors...[/bold]")
        orchestrator = Orchestrator(config)
        console.print("[green]✅ All configured connectors initialized.[/green]")

        # Step 3: Test LLM Provider Connection
        console.print("\n[bold]3. Testing LLM Provider...[/bold]")
        if orchestrator.llm_provider:
            success, message = orchestrator.llm_provider.test_connection()
            if success:
                console.print(f"[green]✅ {config.llm.provider}:[/green] {message}")
            else:
                console.print(f"[red]❌ {config.llm.provider}:[/red] {message}")
                all_healthy = False
        else:
            console.print("[yellow]⚠️ No LLM provider configured.[/yellow]")

        # Step 4: Test Data Source & Action Connections
        console.print("\n[bold]4. Testing Connectors...[/bold]")
        all_connectors = orchestrator.connectors
        if not all_connectors:
            console.print("[yellow]⚠️ No connections or actions configured.[/yellow]")
        
        for name, connector in all_connectors.items():
            success, message = connector.test_connection()
            if success:
                console.print(f"[green]✅ {name} ({connector.config.get('type')}):[/green] {message}")
            else:
                console.print(f"[red]❌ {name} ({connector.config.get('type')}):[/red] {message}")
                all_healthy = False
    
    except (FileNotFoundError, ValueError) as e:
        console.print(f"\n[bold red]ERROR:[/bold red] {e}")
        all_healthy = False
        raise typer.Exit(code=1)
    
    except Exception as e:
        console.print(f"\n[bold red]An unexpected error occurred:[/bold red] {e}")
        all_healthy = False
        raise typer.Exit(code=1)

    # Final Summary Report
    console.print("---")
    if all_healthy:
        console.print("🩺 [bold green]Doctor's report: All systems are healthy![/bold green]")
    else:
        console.print("🩺 [bold yellow]Doctor's report: Found 1 or more issues. Please check your configuration.[/bold yellow]")
        raise typer.Exit(code=1)

@app.command()
def analyze():
    """
    (Placeholder) Analyzes an incident based on a trigger event file.
    """
    console.print("[yellow]⚠️ The 'analyze' command is not yet implemented.[/yellow]")


if __name__ == "__main__":
    app()