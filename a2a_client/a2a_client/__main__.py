"""Command-line interface for A2A SSE Client."""

from typing import Annotated, Optional

import typer
from rich.console import Console

from a2a_client.client import A2ASSEClient

app = typer.Typer(
    name="a2a-client",
    help="A2A SSE Client for testing agent streaming",
    add_completion=False,
)
console = Console()


@app.command()
def send(
    agent_url: Annotated[
        str,
        typer.Option(
            "--agent-url",
            "-a",
            help="URL of the A2A agent",
            envvar="A2A_AGENT_URL",
        ),
    ] = "http://localhost:8016",
    message: Annotated[
        str,
        typer.Option(
            "--message",
            "-m",
            help="Message to send to the agent",
        ),
    ] = "fire and injuries at 170 London Road",
    context_id: Annotated[
        Optional[str],
        typer.Option(
            "--context-id",
            "-c",
            help="Context ID for conversation continuity",
        ),
    ] = None,
    timeout: Annotated[
        int,
        typer.Option(
            "--timeout",
            "-t",
            help="Request timeout in seconds",
        ),
    ] = 300,
) -> None:
    """Send a message to an A2A agent and stream SSE responses."""
    client = A2ASSEClient(base_url=agent_url, timeout=timeout)

    try:
        client.send_message(message=message, context_id=context_id)
        client.print_summary()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        raise typer.Exit(code=130) from None
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1) from None


if __name__ == "__main__":
    app()
