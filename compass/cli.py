import typer
import json
import time
from pathlib import Path
from rich.console import Console
import importlib.resources

# --- Main Application Objects & Constants ---
app = typer.Typer(
    name="compass",
    help="🧭 The open-source AI agent that automates incident response.",
    add_completion=False,
    rich_markup_mode="markdown",
)
console = Console()
CONFIG_DIR = Path.home() / ".compass"
DEFAULT_CONFIG_PATH = CONFIG_DIR / "config.yaml"

# This is a reusable Typer Option for commands that READ an existing config.
ConfigReadOption = typer.Option(
    DEFAULT_CONFIG_PATH,
    "--config",
    "-c",
    help="Path to the Compass config file.",
)

# Load prompt configurations from dedicated template files at startup
try:
    SECRET_PROMPTS = json.loads(
        importlib.resources.read_text("compass.templates", "secret_prompts.json")
    )
    NON_SECRET_PROMPTS = json.loads(
        importlib.resources.read_text("compass.templates", "non_secret_prompts.json")
    )
except Exception as e:
    console.print(
        f"[bold red]Error: A template file is missing or corrupted: {e}[/bold red]"
    )
    SECRET_PROMPTS, NON_SECRET_PROMPTS = {}, {}


# --- CLI Commands ---


@app.command()
def init(
    output_dir: Path = typer.Option(
        str(CONFIG_DIR),
        "--output-dir",
        "-o",
        help="Directory where the new config.yaml and .env files will be created.",
        file_okay=False,
        dir_okay=True,
        writable=True,
    ),
):
    """
    Creates new Compass configuration files with an interactive setup wizard.
    """
    console.print(
        "👋 Welcome to [bold cyan]Compass[/bold cyan]! Let's get you set up.",
        justify="center",
    )

    config_file_path = output_dir / "config.yaml"
    env_file_path = output_dir / ".env"

    if config_file_path.exists() or env_file_path.exists():
        if not typer.confirm(
            f"⚠️ Config files may already exist in {output_dir}. Overwrite?"
        ):
            console.print("Aborting initialization.")
            raise typer.Exit()

    output_dir.mkdir(parents=True, exist_ok=True)

    # --- Step 1: Gather Secrets ---
    console.print(
        f"\nI will ask for your secret API keys. They will be stored securely in:\n[bold yellow]{env_file_path}[/bold yellow]"
    )
    with open(env_file_path, "w") as f:
        for key, info in SECRET_PROMPTS.items():
            prompt_text = (
                f"\nTo get your [bold]{info['prompt']}[/bold], visit: "
                f"[link={info['url']}][cyan]{info['url']}[/link]"
            )
            console.print(prompt_text)
            secret_value = typer.prompt("Paste your key here", hide_input=True)
            f.write(f'{key}="{secret_value}"\n')

    # --- Step 2: Gather Non-Secrets & Prepare Replacements ---
    replacements = {}
    console.print(
        "\nNow, let's configure some default settings. Press Enter to accept the default."
    )
    for key, info in NON_SECRET_PROMPTS.items():
        user_value = typer.prompt(info["prompt"], default=info.get("default"))
        replacements[info["placeholder"]] = user_value

    # --- Step 3: Generate the Final config.yaml ---
    try:
        template_content = importlib.resources.read_text(
            "compass.templates", "config.template.yaml"
        )
        for placeholder, value in replacements.items():
            template_content = template_content.replace(str(placeholder), str(value))
        with open(config_file_path, "w") as f:
            f.write(template_content)

    except FileNotFoundError:
        console.print(
            "[bold red]Error: Could not find the config.template.yaml file.[/bold red]"
        )
        raise typer.Exit(code=1)

    console.print(
        f"\n✅ [bold green]Success![/bold green] Your fully configured files have been created in {output_dir}"
    )
    console.print(
        f"\nNext, run [bold cyan]compass doctor -c {config_file_path}[/bold cyan] to test your connections!"
    )


@app.command()
def doctor(
    config_path: Path = ConfigReadOption,
    retries: int = typer.Option(
        1, "--retries", help="Number of times to retry a failed connection test."
    ),
    retry_delay: int = typer.Option(
        2, "--retry-delay", help="Seconds to wait between retries."
    ),
):
    """
    Checks the configuration and validates all configured connections.
    """
    from compass.config import load_config
    from compass.orchestrator import Orchestrator

    console.print(
        "🩺 Running [bold cyan]Compass Doctor[/bold cyan]...", justify="center"
    )
    health_status = [True]

    try:
        if not config_path.is_file():
            console.print(
                f"❌ [bold red]Error:[/bold red] Configuration file not found at [yellow]{config_path}[/yellow]"
            )
            raise typer.Exit(code=1)

        config = load_config(config_path)
        orchestrator = Orchestrator(config, health_status)

        components_to_test = {
            f"{config.llm.provider} (LLM)": orchestrator.llm_provider,
            **orchestrator.connectors,
        }

        console.print("\n[bold]1. Testing Live Connections...[/bold]")
        if not any(components_to_test.values()):
            console.print(
                "[yellow]⚠️ No connectors or LLM providers configured.[/yellow]"
            )

        for name, component in components_to_test.items():
            if not component:
                continue

            success = False
            message = "Component initialization failed."

            for attempt in range(retries + 1):
                with console.status(
                    f"[bold green]Testing '{name}' (attempt {attempt + 1})...[/bold green]"
                ):
                    try:
                        # Only perform the test connection if initialization was successful
                        if name in orchestrator.connectors or "(LLM)" in name:
                            success, message = component.test_connection()
                        else:
                            # This handles the case where the component itself failed to load
                            success = False
                            # The error message was already printed during Orchestrator init
                            message = "Initialization failed. Check logs above."

                        if success:
                            break  # Exit retry loop on success
                    except Exception as e:
                        message = f"An unexpected exception occurred during test: {e}"
                        success = False

                if not success and attempt < retries:
                    time.sleep(retry_delay)

            if not success:
                health_status[0] = False

            # Final status print
            if success:
                console.print(f"✅ [green]{name}:[/green] {message}")
            else:
                console.print(f"❌ [red]{name}:[/red] {message}")

    except Exception as e:
        console.print(f"\n[bold red]An unexpected error occurred:[/bold red] {e}")
        health_status[0] = False

    all_healthy = health_status[0]
    console.print("---")
    if all_healthy:
        console.print(
            "🩺 [bold green]Doctor's report: All systems are healthy![/bold green]"
        )
    else:
        console.print(
            "🩺 [bold yellow]Doctor's report: Found 1 or more issues.[/bold yellow]"
        )
        raise typer.Exit(code=1)


@app.command()
def analyze(
    trigger_file: Path = typer.Argument(
        ..., help="Path to the trigger event YAML file."
    ),
    config_path: Path = ConfigReadOption,
):
    """
    (Placeholder) Analyzes an incident based on a trigger event file.
    """
    console.print(f"⚙️  Loading configuration from {config_path}...")
    console.print(f"⚡ Triggering analysis with event file: {trigger_file}...")
    console.print("[yellow]⚠️ The 'analyze' command is not yet implemented.[/yellow]")


if __name__ == "__main__":
    app()
