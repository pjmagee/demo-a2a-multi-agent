"""A2A SSE Client with streaming support."""

from typing import Any
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    Message,
    MessageSendParams,
    Part,
    Role,
    SendStreamingMessageRequest,
    SendStreamingMessageSuccessResponse,
    TaskStatusUpdateEvent,
    TextPart,
)
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


class A2ASSEClient:
    """A2A client using the official A2A SDK."""

    MAX_CONTENT_LENGTH = 100

    def __init__(self, base_url: str, timeout: int = 300, verify_ssl: bool = True) -> None:
        """Initialize the A2A SSE client.

        Args:
            base_url: Base URL of the A2A agent
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates

        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.events: list[dict[str, Any]] = []

    def _extract_event_content(self, event: Any) -> str:
        """Extract content from event using pattern matching.

        Args:
            event: Event object from SSE stream

        Returns:
            Extracted content string

        """
        # Try to access the root if wrapped
        unwrapped = getattr(event, "root", event)

        match unwrapped:
            case SendStreamingMessageSuccessResponse(result=Message(parts=parts)):
                # Message with text parts
                return " ".join(
                    part.root.text
                    for part in parts
                    if isinstance(part.root, TextPart)
                )
            case SendStreamingMessageSuccessResponse(
                result=TaskStatusUpdateEvent(status=task_status),
            ):
                # Task status update
                state_text = f"[{task_status.state.value.upper()}]"
                if task_status.message and task_status.message.parts:
                    msg = " ".join(
                        p.root.text
                        for p in task_status.message.parts
                        if isinstance(p.root, TextPart)
                    )
                    return f"{state_text} {msg}"
                return state_text
            case _:
                # Fallback for unknown event types
                return str(event)

    async def send_message(self, message: str, context_id: str | None = None) -> None:
        """Send a message to the agent and stream SSE responses.

        Args:
            message: Message to send to the agent
            context_id: Optional context ID for conversation continuity

        """
        context_id = context_id or uuid4().hex

        console.print(
            Panel(
                f"[bold cyan]Sending to:[/bold cyan] {self.base_url}\n"
                f"[bold cyan]Message:[/bold cyan] {message}\n"
                f"[bold cyan]Context ID:[/bold cyan] {context_id}",
                title="[bold green]A2A Request",
                border_style="green",
            ),
        )

        # Create event table for live updates
        table = Table(title="SSE Events Stream", show_header=True, header_style="bold")
        table.add_column("#", style="dim", width=5)
        table.add_column("Event Type", style="cyan", width=20)
        table.add_column("Content", style="white", width=80)

        async with httpx.AsyncClient(
            timeout=self.timeout,
            verify=self.verify_ssl,
        ) as httpx_client:
            console.print("\n[yellow]Resolving agent card...[/yellow]")

            resolver = A2ACardResolver(
                httpx_client=httpx_client,
                base_url=self.base_url,
            )
            agent_card = await resolver.get_agent_card()

            console.print(f"[green]✓ Connected to: {agent_card.name}[/green]")
            streaming_status = agent_card.capabilities.streaming
            console.print(
                f"[dim]Streaming supported: {streaming_status}[/dim]\n",
            )

            client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)

            request = SendStreamingMessageRequest(
                id=uuid4().hex,
                jsonrpc="2.0",
                method="message/stream",
                params=MessageSendParams(
                    message=Message(
                        context_id=context_id,
                        role=Role.user,
                        message_id=uuid4().hex,
                        parts=[Part(root=TextPart(kind="text", text=message))],
                    ),
                ),
            )

            console.print("[yellow]Streaming events...[/yellow]\n")

            event_count = 0
            async for event in client.send_message_streaming(request=request):
                event_count += 1

                # Store event
                event_record = {"event": event}
                self.events.append(event_record)

                # Debug: Print raw event structure
                console.print(f"\n[dim]--- RAW EVENT {event_count} ---[/dim]")
                console.print(f"[dim]{event}[/dim]")
                console.print(f"[dim]--- END RAW EVENT {event_count} ---[/dim]\n")

                # Extract content and determine display properties
                event_type = type(event).__name__
                content = self._extract_event_content(event)

                # Determine row styling based on event type using pattern matching
                unwrapped = getattr(event, "root", event)
                match unwrapped:
                    case SendStreamingMessageSuccessResponse(
                        result=TaskStatusUpdateEvent(),
                    ):
                        row_style = "yellow"
                    case SendStreamingMessageSuccessResponse(result=Message()):
                        row_style = "green"
                    case _:
                        row_style = "white"

                # Truncate content if too long
                display_content = (
                    f"{content[:self.MAX_CONTENT_LENGTH]}..."
                    if len(content) > self.MAX_CONTENT_LENGTH
                    else content
                )

                # Add row to table
                table.add_row(
                    str(event_count),
                    f"[{row_style}]{event_type}[/{row_style}]",
                    display_content,
                )
                console.print(table)

            event_count_msg = (
                f"\n[green]✓ Stream completed. "
                f"Received {len(self.events)} events[/green]"
            )
            console.print(event_count_msg)

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
        for event_record in self.events:
            event = event_record["event"]
            event_type = type(event).__name__
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

        for event_type, count in event_counts.items():
            summary_table.add_row(event_type, str(count))

        console.print("\n")
        console.print(summary_table)
