"""Typed document models for MongoDB collections."""

from typing import TypedDict


class StarWarsArticle(TypedDict):
    """Schema for documents in the ``articles`` collection."""

    pageid: int
    title: str
    category: str
    content: str
    url: str
    embedding: list[float]


class ArticleSearchResult(TypedDict):
    """Projected fields returned from vector / brute-force search."""

    title: str
    category: str
    content: str
    url: str
    score: float
