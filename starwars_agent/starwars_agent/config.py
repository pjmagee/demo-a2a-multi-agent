"""Configuration for the Star Wars agent and data pipeline."""

import os

# ── Fandom wiki ───────────────────────────────────────────────────────────────
FANDOM_WIKI = "starwars"
FANDOM_API_URL = f"https://{FANDOM_WIKI}.fandom.com/api.php"

# Categories to ingest (MediaWiki "Category:" prefix is added automatically).
DEFAULT_CATEGORIES: list[str] = os.getenv(
    "STARWARS_CATEGORIES",
    "Saga_films,Type_I_atmosphere_planets,Type_II_atmosphere_planets,Type_III_atmosphere_planets,Type_IV_atmosphere_planets",
).split(",")

# ── MongoDB ──────────────────────────────────────────────────────────────────
# Aspire sets ConnectionStrings__<dbname> for MongoDB references
MONGO_URI: str = os.getenv(
    "ConnectionStrings__starwars-db",
    os.getenv("MONGO_URI", "mongodb://localhost:27017"),
)
MONGO_DATABASE: str = os.getenv("MONGO_DATABASE", "starwars")
ARTICLES_COLLECTION: str = "articles"

# ── OpenAI embeddings ───────────────────────────────────────────────────────
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
EMBEDDING_MODEL: str = "text-embedding-3-small"
EMBEDDING_DIMENSIONS: int = 1536

# ── Agent ─────────────────────────────────────────────────────────────────────
AGENT_MODEL_ID: str = os.getenv("AGENT_MODEL_ID", "gpt-4.1-mini")
