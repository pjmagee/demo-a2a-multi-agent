"""Generate OpenAI embeddings for text chunks."""

import logging

from openai import AsyncOpenAI

from starwars_agent.config import EMBEDDING_DIMENSIONS, EMBEDDING_MODEL, OPENAI_API_KEY

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client  # noqa: PLW0603
    if _client is None:
        _client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    return _client


async def embed_texts(texts: list[str], *, batch_size: int = 64) -> list[list[float]]:
    """Return embedding vectors for *texts* using the configured model.

    Batches requests to stay within API limits.
    """
    client = _get_client()
    all_embeddings: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        resp = await client.embeddings.create(
            input=batch,
            model=EMBEDDING_MODEL,
            dimensions=EMBEDDING_DIMENSIONS,
        )
        all_embeddings.extend(item.embedding for item in resp.data)
    logger.info("Embedded %d texts (%d batches)", len(texts), -(-len(texts) // batch_size))
    return all_embeddings


async def embed_query(text: str) -> list[float]:
    """Embed a single query string."""
    vecs = await embed_texts([text])
    return vecs[0]
