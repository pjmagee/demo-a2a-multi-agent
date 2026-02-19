"""Interactive REPL for testing Game News Agent."""

import asyncio
import json
import logging
from datetime import date, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Run the REPL for testing."""
    print("=" * 80)
    print("Game News Agent - Interactive REPL")
    print("=" * 80)
    print("\nThis REPL allows you to test the gaming report agent.")
    print("The agent will generate reports based on game genres, dates, and modes.\n")

    print("NOTE: This is a simplified REPL.")
    print("For full A2A testing, use the FastAPI server and A2A client.\n")

    # Sample requests
    print("Sample requests you can try:\n")
    print("1. Recent RPG games (last 2 weeks)")
    print("2. Upcoming action games (next 2 weeks)")
    print("3. Poorly received indie games (last month)")
    print("4. Exit\n")

    while True:
        choice = input("Select option (1-4): ").strip()

        if choice == "4":
            print("Exiting REPL. Goodbye!")
            break

        # Build request based on choice
        today = date.today()
        request_data = {}

        if choice == "1":
            request_data = {
                "game_genres": ["rpg"],
                "date_from": (today - timedelta(days=14)).isoformat(),
                "date_to": today.isoformat(),
                "game_modes": ["single_player", "offline"],
            }
        elif choice == "2":
            request_data = {
                "game_genres": ["action", "shooter"],
                "date_from": today.isoformat(),
                "date_to": (today + timedelta(days=14)).isoformat(),
                "game_modes": ["multi_player", "online"],
            }
        elif choice == "3":
            request_data = {
                "game_genres": ["indie"],
                "date_from": (today - timedelta(days=30)).isoformat(),
                "date_to": today.isoformat(),
                "game_modes": ["single_player", "offline"],
            }
        else:
            print("Invalid choice. Please select 1-4.")
            continue

        # Display request
        request_json = json.dumps(request_data, indent=2)
        print(f"\nRequest:\n{request_json}\n")

        print("=" * 80)
        print("To test this agent, start the FastAPI server:")
        print("  uv run python -m game_news_agent.app")
        print("\nThen use the A2A client or web interface to send the request.")
        print("=" * 80)
        print()

        print("\nPress Enter to continue...")
        input()


if __name__ == "__main__":
    asyncio.run(main())
