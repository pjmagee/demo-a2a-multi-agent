"""A2A SSE Client with streaming support."""

import json
import sys
from typing import Any
from uuid import uuid4

import httpx
from httpx_sse import connect_sse
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

console = Console()


class A2ASSEClient:
    """Custom A2A client that properly handles SSE streaming."""

    def __init__(self, base_url: str, timeout: int = 300) -> None:
        """Initialize the A2A SSE client.

        Args:
            base_url: Base URL of the A2A agent
            timeout: Request timeout in seconds

        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.events: list[dict[str, Any]] = []

    def send_message(self, message: str, context_id: str | None = None) -> None:
        """Send a message to the agent and stream SSE responses.

        Args:
            message: Message to send to the agent
            context_id: Optional context ID for conversation continuity

        """
        context_id = context_id or str(uuid4())
        task_id = str(uuid4())

        console.print(
            Panel(
                f"[bold cyan]Sending to:[/bold cyan] {self.base_url}\n"
                f"[bold cyan]Message:[/bold cyan] {message}\n"
                f"[bold cyan]Context ID:[/bold cyan] {context_id}\n"
                f"[bold cyan]Task ID:[/bold cyan] {task_id}",
                title="[bold green]A2A Request",
                border_style="green",
            ),
        )

        request_data = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "id": task_id,
            "params": {
                "contextId": context_id,
                "message": {
                    "role": "user",
                    "parts": [{"type": "text", "text": message}],
                },
            },
        }

        # Create event table for live updates
        table = Table(title="SSE Events Stream", show_header=True, header_style="bold")
        table.add_column("Type", style="cyan", width=15)
        table.add_column("Content", style="white", width=80)
        table.add_column("Timestamp", style="dim", width=20)

        try:
            with httpx.Client(timeout=self.timeout) as client:
                console.print("\n[yellow]Opening SSE connection...[/yellow]")

                with connect_sse(
                    client,
                    "POST",
                    f"{self.base_url}/message/send",
                    json=request_data,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "text/event-stream",
                    },
                ) as event_source:
                    console.print("[green]✓ SSE connection established[/green]\n")

                    with Live(table, refresh_per_second=4, console=console) as live:
                        for sse_event in event_source.iter_sse():
                            # Parse the SSE event
                            event_type = sse_event.event or "message"
                            event_data = sse_event.data

                            # Store event
                            event_record = {
                                "type": event_type,
                                "data": event_data,
                                "id": sse_event.id,
                            }
                            self.events.append(event_record)

                            # Try to parse as JSON for better display
                            try:
                                parsed_data = json.loads(event_data)
                                display_data = json.dumps(parsed_data, indent=2)
                            except (json.JSONDecodeError, TypeError):
                                display_data = event_data

                            # Color-code based on event type
                            if event_type == "status":
                                row_style = "yellow"
                            elif event_type == "message":
                                row_style = "green"
                            elif event_type == "error":
                                row_style = "red"
                            else:
                                row_style = "white"

                            # Add row to table
                            table.add_row(
                                f"[{row_style}]{event_type}[/{row_style}]",
                                display_data[:200] + "..." if len(display_data) > 200 else display_data,
                                sse_event.id or "",
                            )
                            live.update(table)

                console.print(
                    f"\n[green]✓ Stream completed. Received {len(self.events)} events[/green]",
                )

        except httpx.TimeoutException:
            console.print("[red]✗ Request timed out[/red]", file=sys.stderr)
            raise
        except httpx.ConnectError as e:
            console.print(
                f"[red]✗ Connection error: {e}[/red]",
                file=sys.stderr,
            )
            raise
        except Exception as e:
            console.print(
                f"[red]✗ Unexpected error: {e}[/red]",
                file=sys.stderr,
            )
            raise

    def get_events(self) -> list[dict[str, Any]]:
        """Get all received events.

        Returns:
            List of event dictionaries

        """
        return self.events

    def print_summary(self) -> None:
        """Print a summary of received events."""
        if not self.events:
            console.print("[yellow]No events received[/yellow]")
            return

        summary_table = Table(
            title="Event Summary",
            show_header=True,
            header_style="bold magenta",
        )
        summary_table.add_column("Event Type", style="cyan")
        summary_table.add_column("Count", style="green", justify="right")

        # Count events by type
        event_counts: dict[str, int] = {}
        for event in self.events:
            event_type = event["type"]
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

        for event_type, count in event_counts.items():
            summary_table.add_row(event_type, str(count))

        console.print("\n")
        console.print(summary_table)
