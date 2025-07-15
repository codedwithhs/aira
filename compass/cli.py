import typer
import json
import webbrowser
from pathlib import Path
from rich.console import Console
import importlib.resources

# --- Main Application Objects & Constants ---
app = typer.Typer(
    name="compass",
    help="🧭 The open-source AI agent that automates incident response.",
    add_completion=False,
    rich_markup_mode="markdown"
)
console = Console()
CONFIG_DIR = Path.home() / ".compass"
DEFAULT_CONFIG_PATH = CONFIG_DIR / "config.yaml"

# Reusable Typer Option for commands that READ an existing config.
ConfigReadOption = typer.Option(
    DEFAULT_CONFIG_PATH,
    "--config",
    "-c",
    help="Path to the Compass config file.",
    show_default=f"Default: {DEFAULT_CONFIG_PATH}",
)

# Load prompt configurations from dedicated template files at startup
try:
    SECRET_PROMPTS = json.loads(importlib.resources.read_text("compass.templates", "secret_prompts.json"))
    NON_SECRET_PROMPTS = json.loads(importlib.resources.read_text("compass.templates", "non_secret_prompts.json"))
except Exception as e:
    console.print(f"[bold red]Error: A template file is missing or corrupted: {e}[/bold red]")
    SECRET_PROMPTS, NON_SECRET_PROMPTS = {}, {}


# --- CLI Commands ---

@app.command()
def init(
    output_dir: Path = typer.Option(
        str(CONFIG_DIR),
        "--output-dir",
        "-o",
        help="Directory where the new config.yaml and .env files will be created.",
        show_default=f"Default: {CONFIG_DIR}",
        file_okay=False,
        dir_okay=True,
        writable=True,
    )
):
    """
    Creates new Compass configuration files with an interactive setup wizard.
    """
    console.print("👋 Welcome to [bold cyan]Compass[/bold cyan]! Let's get you set up.", justify="center")

    config_file_path = output_dir / "config.yaml"
    env_file_path = output_dir / ".env"

    if config_file_path.exists() or env_file_path.exists():
        overwrite = typer.confirm(f"⚠️ Configuration files may already exist in {output_dir}. Do you want to proceed and potentially overwrite them?")
        if not overwrite:
            console.print("Aborting initialization.")
            raise typer.Exit()

    output_dir.mkdir(parents=True, exist_ok=True)
    
    # --- Step 1: Gather Secrets ---
    console.print(f"\nI will ask for your secret API keys. They will be stored securely in:\n[bold yellow]{env_file_path}[/bold yellow]")
    with open(env_file_path, "w") as f:
        for key, info in SECRET_PROMPTS.items():
            console.print(f"\n🔗 To get your [bold]{info['prompt']}[/bold], visit this URL:")
            console.print(f"[cyan]{info['url']}[/cyan]")
            if typer.confirm("Open this URL in your browser?", default=True):
                webbrowser.open(info['url'])
            secret_value = typer.prompt("Paste your key here", hide_input=True)
            f.write(f"{key}=\"{secret_value}\"\n")
    
    # --- Step 2: Gather Non-Secrets for Template Substitution ---
    replacements = {}
    console.print("\nNow, let's configure some default settings.")
    for key, info in NON_SECRET_PROMPTS.items():
        user_value = typer.prompt(info['prompt'])
        replacements[info['placeholder']] = user_value

    # --- Step 3: Generate the Final config.yaml ---
    try:
        template_content = importlib.resources.read_text("compass.templates", "config.template.yaml")
        for placeholder, value in replacements.items():
            template_content = template_content.replace(placeholder, value)
        with open(config_file_path, "w") as f:
            f.write(template_content)
            
    except FileNotFoundError:
        console.print("[bold red]Error: Could not find the config.template.yaml file.[/bold red]")
        raise typer.Exit(code=1)

    console.print(f"\n✅ [bold green]Success![/bold green] Your fully configured files have been created in {output_dir}")
    console.print(f"\nNext, run [bold cyan]compass doctor -c {config_file_path}[/bold cyan] to test your new connections!")


@app.command()
def doctor(config_path: Path = ConfigReadOption):
    """
    Checks the configuration and validates all configured connections.
    """
    from compass.config import load_config
    from compass.orchestrator import Orchestrator

    console.print("🩺 Running [bold cyan]Compass Doctor[/bold cyan]...", justify="center")
    health_status = [True] 
    
    try:
        # Check for file existence manually for a better error message
        if not config_path.exists():
            console.print(f"❌ [bold red]Error:[/bold red] Configuration file not found at {config_path}")
            raise typer.Exit(code=1)

        config = load_config(config_path)
        orchestrator = Orchestrator(config, health_status)
        
        console.print("\n[bold]1. Testing LLM Provider...[/bold]")
        if orchestrator.llm_provider:
            success, message = orchestrator.llm_provider.test_connection()
            if not success: health_status[0] = False
            console.print(f"[green]✅ {config.llm.provider}:[/green] {message}" if success else f"[red]❌ {config.llm.provider}:[/red] {message}")
        
        console.print("\n[bold]2. Testing Connectors...[/bold]")
        if not orchestrator.connectors:
            console.print("[yellow]⚠️ No connections or actions configured.[/yellow]")
        
        for name, connector in orchestrator.connectors.items():
            with console.status(f"[bold green]Testing '{name}'...[/bold green]"):
                success, message = connector.test_connection()
            
            if not success: health_status[0] = False
            console.print(f"[green]✅ {name} ({connector.config.get('type')}):[/green] {message}" if success else f"[red]❌ {name} ({connector.config.get('type')}):[/red] {message}")
    
    except Exception as e:
        console.print(f"\n[bold red]An unexpected error occurred:[/bold red] {e}")
        health_status[0] = False
    
    all_healthy = health_status[0]
    console.print("---")
    if all_healthy:
        console.print("🩺 [bold green]Doctor's report: All systems are healthy![/bold green]")
    else:
        console.print("🩺 [bold yellow]Doctor's report: Found 1 or more issues.[/bold yellow]")
        raise typer.Exit(code=1)


@app.command()
def analyze(config_path: Path = ConfigReadOption):
    """
    (Placeholder) Analyzes an incident based on a trigger event file.
    """
    console.print(f"⚙️  Loading configuration from {config_path}...")
    console.print("[yellow]⚠️ The 'analyze' command is not yet implemented.[/yellow]")


if __name__ == "__main__":
    app()