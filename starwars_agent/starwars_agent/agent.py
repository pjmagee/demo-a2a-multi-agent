"""Strands SDK agent for answering Star Wars questions via vector search."""

import logging

from strands import Agent, tool
from strands.models.openai import OpenAIModel

from starwars_agent.config import AGENT_MODEL_ID, DEFAULT_CATEGORIES, OPENAI_API_KEY
from starwars_agent.models import ArticleSearchResult
from starwars_agent.search import vector_search

logger = logging.getLogger(__name__)


# ── Tools ────────────────────────────────────────────────────────────────────

@tool
async def search_articles(query: str, category: str = "") -> str:
    """Search the Star Wars knowledge base for articles matching a query.

    Args:
        query: The search query describing what you want to find.
        category: Optional wiki category to filter by (e.g. 'Saga_films'). Leave empty to search all.
    """
    logger.info("Tool search_articles: query=%r category=%r", query, category)
    results: list[ArticleSearchResult] = await vector_search(
        query, category=category or None, top_k=5,
    )
    if not results:
        return "No matching articles found."

    parts: list[str] = []
    for i, r in enumerate(results, 1):
        score = r.get("score", 0)
        parts.append(
            f"[{i}] {r['title']} (score: {score:.3f})\n"
            f"    Category: {r['category']}\n"
            f"    URL: {r['url']}\n"
            f"    Excerpt: {r['content'][:500]}...\n"
        )
    return "\n".join(parts)


@tool
def list_categories() -> str:
    """List the available Star Wars article categories that have been ingested."""
    return "Available categories: " + ", ".join(DEFAULT_CATEGORIES)


# ── Agent ────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a Star Wars knowledge expert. You answer questions about Star Wars \
by searching a curated database of articles from Wookieepedia (the Star Wars Fandom wiki).

When answering:
1. Always use the search_articles tool to find relevant information.
2. Cite your sources — include the article title and URL for each fact.
3. If the information isn't in the database, say so honestly.
4. You can use list_categories to see which categories are available.
5. Be thorough but concise in your answers.
"""


def build_strands_agent() -> Agent:
    """Create and return a configured Strands agent."""
    model = OpenAIModel(
        client_args={"api_key": OPENAI_API_KEY},
        model_id=AGENT_MODEL_ID,
    )
    return Agent(
        model=model,
        tools=[search_articles, list_categories],
        system_prompt=SYSTEM_PROMPT,
    )


class StarWarsAgent:
    """Wrapper around the Strands agent for A2A integration."""

    def __init__(self) -> None:
        self._agent = build_strands_agent()

    async def invoke(self, user_input: str) -> str:
        """Run the agent with user input and return the response text."""
        result = await self._agent.invoke_async(user_input)
        return str(result)
