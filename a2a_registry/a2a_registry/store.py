"""In-memory registry store for agent information."""

import logging
from datetime import UTC, datetime
from typing import ClassVar

from a2a.types import AgentCard

from a2a_registry.models import AgentEntry

logger: logging.Logger = logging.getLogger(name=__name__)


class RegistryStore:
    """In-memory store for registered agents."""

    _instance: ClassVar["RegistryStore | None"] = None
    _agents: dict[str, AgentEntry]

    def __new__(cls) -> "RegistryStore":
        """Singleton pattern to ensure only one registry store exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._agents = {}
        return cls._instance

    def register(self, address: str, agent_card: AgentCard) -> AgentEntry:
        """Register an agent with the given address and card.

        Args:
            address: Base URL of the agent
            agent_card: Agent card metadata

        Returns:
            AgentEntry for the registered agent

        """
        normalized_address = self._normalize_address(address)

        entry = AgentEntry(
            address=normalized_address,
            agent_card=agent_card,
            registered_at=datetime.now(UTC).isoformat(),
        )

        self._agents[normalized_address] = entry
        logger.info(
            "Registered agent: %s at %s",
            agent_card.name,
            normalized_address,
        )
        return entry

    def unregister(self, address: str) -> bool:
        """Unregister an agent by address.

        Args:
            address: Base URL of the agent

        Returns:
            True if agent was unregistered, False if not found

        """
        normalized_address = self._normalize_address(address)

        if normalized_address in self._agents:
            agent_name = self._agents[normalized_address].agent_card.name
            del self._agents[normalized_address]
            logger.info(
                "Unregistered agent: %s from %s",
                agent_name,
                normalized_address,
            )
            return True

        logger.warning("Attempted to unregister unknown address: %s", address)
        return False

    def get_all(self) -> list[AgentEntry]:
        """Get all registered agents.

        Returns:
            List of all registered agent entries

        """
        return list(self._agents.values())

    def get_by_address(self, address: str) -> AgentEntry | None:
        """Get an agent by address.

        Args:
            address: Base URL of the agent

        Returns:
            AgentEntry if found, None otherwise

        """
        normalized_address = self._normalize_address(address)
        return self._agents.get(normalized_address)

    def count(self) -> int:
        """Get the number of registered agents.

        Returns:
            Count of registered agents

        """
        return len(self._agents)

    def clear(self) -> None:
        """Clear all registered agents (useful for testing)."""
        self._agents.clear()
        logger.info("Cleared all registered agents")

    @staticmethod
    def _normalize_address(address: str) -> str:
        """Normalize an address by stripping whitespace and trailing slashes.

        Args:
            address: Raw address string

        Returns:
            Normalized address

        """
        return address.strip().rstrip("/")


# Singleton instance
registry_store = RegistryStore()
