"""Agent card builder for the Greetings agent."""

from a2a.types import AgentCapabilities, AgentCard, AgentSkill


def build_agent_card(base_url: str) -> AgentCard:
    """Return the agent card describing the Greetings agent's capabilities."""
    agent_capabilities = AgentCapabilities(
        push_notifications=False,
        state_transition_history=False,
        streaming=False,
    )
    agent_skills: list[AgentSkill] = [
        AgentSkill(
            id="greeting",
            description="Returns a friendly greeting in the caller's language.",
            examples=[
                "Hello!",
                "Aloha!",
                "Bonjour!",
                "Hola!",
                "Ciao!",
                "Hallo!",
                "Hej!",
                "Konnichiwa!",
                "Namaste!",
                "Olá!",
                "Salaam!",
                "Zdravstvuyte!",
            ],
            name="Greeting",
            input_modes=["text"],
            output_modes=["text"],
            security=None,
            tags=["greeting"],
        ),
        AgentSkill(
            id="weather",
            description="Shares a simple weather condition in the caller's language.",
            examples=[
                "It's sunny!",
                "Está nublado!",
                "Il pleut!",
                "¡Está lloviendo!",
                "Fa caldo!",
                "Es ist heiß!",
                "Det är soligt!",
                "今日は晴れています!",
                "今日は暑いです!",
                "Está frio!",
                "Сейчас холодно!",
                "Сейчас тепло!",
            ],
            name="Weather",
            input_modes=["text"],
            output_modes=["text"],
            security=None,
            tags=["weather"],
        ),
    ]
    return AgentCard(
        name="Greetings Agent",
        capabilities=agent_capabilities,
        description="A friendly agent that provides multilingual greetings and casual weather updates.",
        version="0.1.0",
        preferred_transport="JSONRPC",
        default_input_modes=["text"],
        default_output_modes=["text"],
        skills=agent_skills,
        url=base_url,
        supports_authenticated_extended_card=False,
    )
