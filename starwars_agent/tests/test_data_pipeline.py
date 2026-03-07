"""Integration tests for data pipeline with a real MongoDB instance via testcontainers."""

import random
from typing import Any
from unittest.mock import AsyncMock, patch

import numpy as np
import pytest
import pytest_asyncio
from pymongo import AsyncMongoClient
from testcontainers.mongodb import MongoDbContainer

from starwars_agent.data_pipeline.loader import (
    collection_is_empty,
    ingest_categories,
)
from starwars_agent.models import StarWarsArticle
from starwars_agent.search import _brute_force_search, _cosine_sim

# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def mongodb_container():
    """Start a MongoDB container for the test session."""
    with MongoDbContainer("mongodb/mongodb-community-server:latest") as container:
        yield container


@pytest_asyncio.fixture
async def mongo_client(mongodb_container):
    """Create an async Mongo client connected to the test container."""
    url = mongodb_container.get_connection_url()
    client: AsyncMongoClient[dict[str, Any]] = AsyncMongoClient(url, document_class=dict)
    yield client
    await client.close()


DIMENSIONS = 8  # small embedding dimension for tests


def _random_embedding(dim: int = DIMENSIONS) -> list[float]:
    return [random.uniform(-1, 1) for _ in range(dim)]


def _make_article(
    pageid: int,
    title: str,
    category: str = "Saga_films",
    content: str = "Some content",
    embedding: list[float] | None = None,
) -> dict[str, Any]:
    return dict(StarWarsArticle(
        pageid=pageid,
        title=title,
        category=category,
        content=content,
        url=f"https://starwars.fandom.com/wiki/{title.replace(' ', '_')}",
        embedding=embedding or _random_embedding(),
    ))


# ── Loader tests ─────────────────────────────────────────────────────────────

class TestCollectionIsEmpty:
    @pytest.mark.asyncio
    async def test_empty_collection(self, mongo_client: AsyncMongoClient[dict[str, Any]]):
        col = mongo_client["test_empty"]["articles"]
        await col.drop()

        with patch("starwars_agent.data_pipeline.loader.get_collection", return_value=col):
            assert await collection_is_empty() is True

    @pytest.mark.asyncio
    async def test_non_empty_collection(self, mongo_client: AsyncMongoClient[dict[str, Any]]):
        col = mongo_client["test_nonempty"]["articles"]
        await col.drop()
        await col.insert_one(_make_article(1, "A New Hope"))

        with patch("starwars_agent.data_pipeline.loader.get_collection", return_value=col):
            assert await collection_is_empty() is False


class TestInsertAndRetrieve:
    @pytest.mark.asyncio
    async def test_insert_typed_article(self, mongo_client: AsyncMongoClient[dict[str, Any]]):
        """Verify StarWarsArticle documents round-trip through MongoDB."""
        col = mongo_client["test_roundtrip"]["articles"]
        await col.drop()

        article = _make_article(42, "Return of the Jedi", content="Luke saves Vader")
        await col.insert_one(article)

        doc = await col.find_one({"pageid": 42})
        assert doc is not None
        assert doc["title"] == "Return of the Jedi"
        assert doc["content"] == "Luke saves Vader"
        assert doc["category"] == "Saga_films"
        assert len(doc["embedding"]) == DIMENSIONS

    @pytest.mark.asyncio
    async def test_insert_multiple_articles(self, mongo_client: AsyncMongoClient[dict[str, Any]]):
        col = mongo_client["test_multi"]["articles"]
        await col.drop()

        articles = [
            _make_article(1, "A New Hope"),
            _make_article(2, "The Empire Strikes Back"),
            _make_article(3, "Return of the Jedi"),
        ]
        result = await col.insert_many(articles)
        assert len(result.inserted_ids) == 3

        count = await col.count_documents({})
        assert count == 3

    @pytest.mark.asyncio
    async def test_duplicate_pageid_handling(self, mongo_client: AsyncMongoClient[dict[str, Any]]):
        """Verify we can query by pageid to detect existing articles."""
        col = mongo_client["test_dedup"]["articles"]
        await col.drop()

        await col.insert_one(_make_article(1, "A New Hope"))

        existing_ids = set()
        async for doc in col.find({"pageid": {"$in": [1, 2]}}, {"pageid": 1}):
            existing_ids.add(doc["pageid"])

        assert existing_ids == {1}

    @pytest.mark.asyncio
    async def test_category_filter(self, mongo_client: AsyncMongoClient[dict[str, Any]]):
        col = mongo_client["test_category"]["articles"]
        await col.drop()

        await col.insert_many([
            _make_article(1, "A New Hope", category="Saga_films"),
            _make_article(2, "Rogue One", category="Anthology_films"),
            _make_article(3, "The Empire Strikes Back", category="Saga_films"),
        ])

        saga = [doc["title"] async for doc in col.find({"category": "Saga_films"})]

        assert len(saga) == 2
        assert "A New Hope" in saga
        assert "The Empire Strikes Back" in saga


class TestIngestCategories:
    """Test the full ingest pipeline with mocked Fandom API and embeddings."""

    @pytest.mark.asyncio
    async def test_ingests_articles_into_mongodb(self, mongo_client: AsyncMongoClient[dict[str, Any]]):
        col = mongo_client["test_ingest"]["articles"]
        await col.drop()

        mock_members = [
            {"pageid": 1, "title": "A New Hope"},
            {"pageid": 2, "title": "The Empire Strikes Back"},
        ]

        fake_embeddings = [_random_embedding(), _random_embedding()]

        with (
            patch("starwars_agent.data_pipeline.loader.get_collection", return_value=col),
            patch("starwars_agent.data_pipeline.loader.fetch_category_members", new_callable=AsyncMock, return_value=mock_members),
            patch("starwars_agent.data_pipeline.loader.fetch_page_content", new_callable=AsyncMock, side_effect=["Content for ANH", "Content for ESB"]),
            patch("starwars_agent.data_pipeline.loader.embed_texts", new_callable=AsyncMock, return_value=fake_embeddings),
        ):
            count = await ingest_categories(["Saga_films"], client=mongo_client)

        assert count == 2
        assert await col.count_documents({}) == 2

        doc = await col.find_one({"title": "A New Hope"})
        assert doc is not None
        assert doc["content"] == "Content for ANH"
        assert doc["embedding"] == fake_embeddings[0]

    @pytest.mark.asyncio
    async def test_skips_already_ingested_articles(self, mongo_client: AsyncMongoClient[dict[str, Any]]):
        col = mongo_client["test_skip"]["articles"]
        await col.drop()

        # Pre-insert one article
        await col.insert_one(_make_article(1, "A New Hope"))

        mock_members = [
            {"pageid": 1, "title": "A New Hope"},
            {"pageid": 2, "title": "The Empire Strikes Back"},
        ]

        with (
            patch("starwars_agent.data_pipeline.loader.get_collection", return_value=col),
            patch("starwars_agent.data_pipeline.loader.fetch_category_members", new_callable=AsyncMock, return_value=mock_members),
            patch("starwars_agent.data_pipeline.loader.fetch_page_content", new_callable=AsyncMock, return_value="ESB content"),
            patch("starwars_agent.data_pipeline.loader.embed_texts", new_callable=AsyncMock, return_value=[_random_embedding()]),
        ):
            count = await ingest_categories(["Saga_films"], client=mongo_client)

        # Only the new article should be inserted
        assert count == 1
        assert await col.count_documents({}) == 2

    @pytest.mark.asyncio
    async def test_skips_empty_page_content(self, mongo_client: AsyncMongoClient[dict[str, Any]]):
        col = mongo_client["test_empty_content"]["articles"]
        await col.drop()

        mock_members = [{"pageid": 1, "title": "Empty Page"}]

        with (
            patch("starwars_agent.data_pipeline.loader.get_collection", return_value=col),
            patch("starwars_agent.data_pipeline.loader.fetch_category_members", new_callable=AsyncMock, return_value=mock_members),
            patch("starwars_agent.data_pipeline.loader.fetch_page_content", new_callable=AsyncMock, return_value="   "),
            patch("starwars_agent.data_pipeline.loader.embed_texts", new_callable=AsyncMock, return_value=[]),
        ):
            count = await ingest_categories(["Saga_films"], client=mongo_client)

        assert count == 0
        assert await col.count_documents({}) == 0


# ── Search tests ─────────────────────────────────────────────────────────────

class TestCosineSimilarity:
    def test_identical_vectors(self):
        a = np.array([1.0, 0.0, 0.0])
        assert _cosine_sim(a, a) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        a = np.array([1.0, 0.0])
        b = np.array([0.0, 1.0])
        assert _cosine_sim(a, b) == pytest.approx(0.0)

    def test_opposite_vectors(self):
        a = np.array([1.0, 0.0])
        b = np.array([-1.0, 0.0])
        assert _cosine_sim(a, b) == pytest.approx(-1.0)

    def test_zero_vector_returns_zero(self):
        a = np.array([0.0, 0.0])
        b = np.array([1.0, 1.0])
        assert _cosine_sim(a, b) == 0.0


class TestBruteForceSearch:
    """Test the brute-force fallback search against a real MongoDB collection."""

    @pytest.mark.asyncio
    async def test_returns_top_k_results(self, mongo_client: AsyncMongoClient[dict[str, Any]]):
        col = mongo_client["test_brute_search"]["articles"]
        await col.drop()

        # Create a known query vector and articles with known similarity ordering
        query_vec = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        # Most similar: aligned with query
        await col.insert_many([
            _make_article(1, "Best Match", embedding=[1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
            _make_article(2, "Partial Match", embedding=[0.7, 0.7, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
            _make_article(3, "Weak Match", embedding=[0.1, 0.9, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        ])

        with (
            patch("starwars_agent.search.get_collection", return_value=col),
            patch("starwars_agent.search.EMBEDDING_DIMENSIONS", DIMENSIONS),
        ):
            results = await _brute_force_search(query_vec, top_k=2)

        assert len(results) == 2
        assert results[0]["title"] == "Best Match"
        assert results[1]["title"] == "Partial Match"
        assert results[0]["score"] > results[1]["score"]

    @pytest.mark.asyncio
    async def test_filters_by_category(self, mongo_client: AsyncMongoClient[dict[str, Any]]):
        col = mongo_client["test_brute_category"]["articles"]
        await col.drop()

        query_vec = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        await col.insert_many([
            _make_article(1, "Saga Hit", category="Saga_films", embedding=[1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
            _make_article(2, "Anthology Hit", category="Anthology_films", embedding=[0.9, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        ])

        with (
            patch("starwars_agent.search.get_collection", return_value=col),
            patch("starwars_agent.search.EMBEDDING_DIMENSIONS", DIMENSIONS),
        ):
            results = await _brute_force_search(query_vec, category="Saga_films", top_k=5)

        assert len(results) == 1
        assert results[0]["title"] == "Saga Hit"

    @pytest.mark.asyncio
    async def test_skips_documents_with_wrong_embedding_dimensions(self, mongo_client: AsyncMongoClient[dict[str, Any]]):
        col = mongo_client["test_brute_bad_dims"]["articles"]
        await col.drop()

        query_vec = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        await col.insert_many([
            _make_article(1, "Good Embedding", embedding=[1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
            _make_article(2, "Bad Embedding", embedding=[1.0, 0.0]),  # wrong dim
        ])

        with (
            patch("starwars_agent.search.get_collection", return_value=col),
            patch("starwars_agent.search.EMBEDDING_DIMENSIONS", DIMENSIONS),
        ):
            results = await _brute_force_search(query_vec, top_k=5)

        assert len(results) == 1
        assert results[0]["title"] == "Good Embedding"

    @pytest.mark.asyncio
    async def test_returns_article_search_result_type(self, mongo_client: AsyncMongoClient[dict[str, Any]]):
        col = mongo_client["test_brute_type"]["articles"]
        await col.drop()

        query_vec = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        await col.insert_one(
            _make_article(1, "A New Hope", content="Long content " * 200, embedding=[0.9, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        )

        with (
            patch("starwars_agent.search.get_collection", return_value=col),
            patch("starwars_agent.search.EMBEDDING_DIMENSIONS", DIMENSIONS),
        ):
            results = await _brute_force_search(query_vec, top_k=1)

        assert len(results) == 1
        result = results[0]
        assert "title" in result
        assert "category" in result
        assert "content" in result
        assert "url" in result
        assert "score" in result
        # Content should be truncated to 1000 chars
        assert len(result["content"]) <= 1000
