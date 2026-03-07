"""MongoDB vector search over ingested Star Wars articles."""

import logging
from typing import Any

import numpy as np

from starwars_agent.config import (
    ARTICLES_COLLECTION,
    EMBEDDING_DIMENSIONS,
    MONGO_DATABASE,
)
from starwars_agent.data_pipeline.embeddings import embed_query
from starwars_agent.data_pipeline.loader import get_collection, get_mongo_client
from starwars_agent.models import ArticleSearchResult

logger = logging.getLogger(__name__)


async def vector_search(
    query: str,
    *,
    category: str | None = None,
    top_k: int = 5,
) -> list[ArticleSearchResult]:
    """Search articles by semantic similarity to *query*.

    Uses ``$vectorSearch`` aggregation when a vector index exists,
    falling back to brute-force cosine scan otherwise.
    """
    query_vec = await embed_query(query)

    # Use untyped collection for aggregate since projection changes the document shape
    try:
        raw_col = get_mongo_client()[MONGO_DATABASE][ARTICLES_COLLECTION]
        pipeline: list[dict[str, Any]] = [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embedding",
                    "queryVector": query_vec,
                    "numCandidates": top_k * 10,
                    "limit": top_k,
                },
            },
            {
                "$project": {
                    "_id": 0,
                    "title": 1,
                    "category": 1,
                    "content": {"$substrBytes": ["$content", 0, 1000]},
                    "url": 1,
                    "score": {"$meta": "vectorSearchScore"},
                },
            },
        ]
        if category:
            pipeline[0]["$vectorSearch"]["filter"] = {"category": {"$eq": category}}
        cursor = await raw_col.aggregate(pipeline)
        raw_results: list[dict[str, Any]] = await cursor.to_list(top_k)
        if raw_results:
            return [
                ArticleSearchResult(
                    title=r["title"],
                    category=r["category"],
                    content=r["content"],
                    url=r["url"],
                    score=r["score"],
                )
                for r in raw_results
            ]
    except Exception:
        logger.debug("$vectorSearch not available, falling back to brute-force", exc_info=True)

    # Brute-force fallback: fetch all docs, compute cosine in Python
    return await _brute_force_search(query_vec, category=category, top_k=top_k)


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


async def _brute_force_search(
    query_vec: list[float],
    *,
    category: str | None = None,
    top_k: int = 5,
) -> list[ArticleSearchResult]:
    """Fallback cosine search when no vector index is available."""
    col = get_collection()
    query_filter: dict[str, Any] = {}
    if category:
        query_filter["category"] = category

    query_arr = np.asarray(query_vec, dtype=np.float64)
    scored: list[tuple[float, ArticleSearchResult]] = []
    async for doc in col.find(query_filter, {"embedding": 1, "title": 1, "category": 1, "content": 1, "url": 1}):
        emb = doc.get("embedding")
        if not emb or len(emb) != EMBEDDING_DIMENSIONS:
            continue
        score = _cosine_sim(query_arr, np.asarray(emb, dtype=np.float64))
        scored.append((score, ArticleSearchResult(
            title=doc["title"],
            category=doc["category"],
            content=doc["content"][:1000],
            url=doc["url"],
            score=score,
        )))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:top_k]]
