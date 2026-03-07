"""Pipeline loader — fetch articles from Fandom, embed, and store in MongoDB."""

import logging
from typing import Any, cast

from pymongo import AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection

from starwars_agent.config import (
    ARTICLES_COLLECTION,
    DEFAULT_CATEGORIES,
    EMBEDDING_DIMENSIONS,
    MONGO_DATABASE,
    MONGO_URI,
)
from starwars_agent.data_pipeline.embeddings import embed_texts
from starwars_agent.data_pipeline.fandom_client import (
    fetch_category_members,
    fetch_page_content,
)
from starwars_agent.models import StarWarsArticle

logger = logging.getLogger(__name__)

# ── MongoDB helpers ──────────────────────────────────────────────────────────

MongoClient = AsyncMongoClient[dict[str, Any]]

_mongo: MongoClient | None = None


def get_mongo_client() -> MongoClient:
    """Return (or create) a module-level async Mongo client."""
    global _mongo  # noqa: PLW0603
    if _mongo is None:
        _mongo = AsyncMongoClient(MONGO_URI, document_class=dict)
    return _mongo


def get_collection(client: MongoClient | None = None) -> AsyncCollection[StarWarsArticle]:
    """Return the typed articles collection handle."""
    c = client or get_mongo_client()
    return cast("AsyncCollection[StarWarsArticle]", c[MONGO_DATABASE][ARTICLES_COLLECTION])


async def ensure_search_index(client: MongoClient | None = None) -> None:
    """Create the vector search index if it doesn't already exist.

    MongoDB 8.0 Community supports $vectorSearch with Atlas-style indexes
    created via ``createSearchIndex`` command if supported, otherwise we
    fall back to a regular index on the embedding field for $nearSphere
    compatibility.
    """
    col = get_collection(client)
    try:
        existing = await (await col.list_search_indexes()).to_list()
        if any(idx.get("name") == "vector_index" for idx in existing):
            logger.info("Vector search index already exists")
            return
    except Exception:
        logger.info("list_search_indexes not supported — attempting to create index anyway")
    try:
        await col.create_search_index(
            model={
                "name": "vector_index",
                "type": "vectorSearch",
                "definition": {
                    "fields": [
                        {
                            "type": "vector",
                            "path": "embedding",
                            "numDimensions": EMBEDDING_DIMENSIONS,
                            "similarity": "cosine",
                        },
                    ],
                },
            },
        )
        logger.info("Created vector search index")
    except Exception:
        logger.warning(
            "Could not create Atlas vector search index (may not be supported). "
            "Falling back to no explicit vector index — cosine search will use brute-force scan.",
            exc_info=True,
        )


# ── Ingestion ────────────────────────────────────────────────────────────────

async def collection_is_empty(client: MongoClient | None = None) -> bool:
    """Return True when the articles collection has no documents."""
    col = get_collection(client)
    doc = await col.find_one({}, {"_id": 1})
    return doc is None


async def ingest_categories(
    categories: list[str] | None = None,
    *,
    client: MongoClient | None = None,
) -> int:
    """Fetch, embed, and store all articles for the given categories.

    Returns the number of documents inserted.
    """
    categories = categories or DEFAULT_CATEGORIES
    col = get_collection(client)
    total = 0

    for category in categories:
        logger.info("Ingesting category: %s", category)
        members = await fetch_category_members(category)
        if not members:
            logger.warning("No pages found for category '%s'", category)
            continue

        # Check which pages we already have
        existing_ids = set()
        cursor = col.find(
            {"pageid": {"$in": [m["pageid"] for m in members]}},
            {"pageid": 1},
        )
        async for doc in cursor:
            existing_ids.add(doc["pageid"])

        new_members = [m for m in members if m["pageid"] not in existing_ids]
        if not new_members:
            logger.info("All %d pages from '%s' already ingested", len(members), category)
            continue

        logger.info("Fetching content for %d new pages in '%s'", len(new_members), category)
        contents: list[str] = []
        docs: list[StarWarsArticle] = []
        for member in new_members:
            title = str(member["title"])
            content = await fetch_page_content(title)
            if not content.strip():
                logger.debug("Skipping empty page: %s", title)
                continue
            # Truncate very long articles to keep embedding quality reasonable
            if len(content) > 15_000:
                content = content[:15_000]
            contents.append(content)
            docs.append(StarWarsArticle(
                pageid=int(member["pageid"]),
                title=title,
                category=category,
                content=content,
                url=f"https://starwars.fandom.com/wiki/{title.replace(' ', '_')}",
                embedding=[],
            ))

        if not docs:
            continue

        # Embed all contents in one go
        logger.info("Generating embeddings for %d documents", len(docs))
        embeddings = await embed_texts(contents)
        for doc, emb in zip(docs, embeddings, strict=True):
            doc["embedding"] = emb

        result = await col.insert_many(docs)
        total += len(result.inserted_ids)
        logger.info(
            "Inserted %d documents for category '%s'",
            len(result.inserted_ids),
            category,
        )

    return total


async def run_pipeline(categories: list[str] | None = None) -> None:
    """Run the ingestion pipeline for any missing categories/pages."""
    client = get_mongo_client()
    logger.info("Running ingestion pipeline for configured categories")
    count = await ingest_categories(categories, client=client)
    if count:
        logger.info("Pipeline complete — inserted %d new documents", count)
    else:
        logger.info("Pipeline complete — no new documents to insert")
    await ensure_search_index(client)
