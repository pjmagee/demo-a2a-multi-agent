"""Fandom MediaWiki API client — fetch category members and page content."""

import logging
import re
import ssl

import certifi
import httpx

from starwars_agent.config import FANDOM_API_URL

logger = logging.getLogger(__name__)

_WIKITEXT_STRIP = re.compile(
    r"\[\[(?:File|Image):.*?\]\]"   # file embeds
    r"|\{\{[^}]*\}\}"              # templates
    r"|\[\[[^|\]]*\|([^\]]*)\]\]"  # [[target|display]] → display
    r"|\[\[([^\]]*)\]\]"           # [[link]] → link
    r"|'{2,3}"                     # bold / italic markup
    r"|<ref[^>]*>.*?</ref>"        # inline refs
    r"|<ref[^/]*/>"                # self-closing refs
    r"|<[^>]+>"                    # remaining HTML tags
    r"|\n{3,}",                    # excessive blank lines
    flags=re.DOTALL,
)


def _clean_wikitext(raw: str) -> str:
    """Strip common MediaWiki markup, returning readable plain text."""
    text = _WIKITEXT_STRIP.sub(lambda m: m.group(1) or m.group(2) or "", raw)
    # Collapse whitespace runs
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n\n", text)
    return text.strip()


async def fetch_category_members(
    category: str,
    *,
    limit: int = 500,
) -> list[dict[str, int | str]]:
    """Return all page stubs (pageid, title) in *category*, paginating fully."""
    pages: list[dict[str, int | str]] = []
    params: dict[str, str | int] = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": f"Category:{category}",
        "cmtype": "page",
        "cmlimit": limit,
        "format": "json",
    }
    # Use certifi CA bundle explicitly, bypassing Aspire-injected SSL_CERT_FILE
    # which only contains dev certs for internal HTTPS.
    _ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    async with httpx.AsyncClient(timeout=30, verify=_ssl_ctx) as client:
        while True:
            resp = await client.get(FANDOM_API_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            for member in data.get("query", {}).get("categorymembers", []):
                pages.append({"pageid": member["pageid"], "title": member["title"]})
            cont = data.get("continue")
            if not cont:
                break
            params["cmcontinue"] = cont["cmcontinue"]
    logger.info("Category '%s' has %d pages", category, len(pages))
    return pages


async def fetch_page_content(title: str) -> str:
    """Fetch the full wikitext of *title* and return cleaned plain text."""
    params: dict[str, str | int] = {
        "action": "parse",
        "page": title,
        "prop": "wikitext",
        "format": "json",
    }
    # Use certifi CA bundle explicitly for external Fandom API
    _ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    async with httpx.AsyncClient(timeout=30, verify=_ssl_ctx) as client:
        resp = await client.get(FANDOM_API_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
    raw = data.get("parse", {}).get("wikitext", {}).get("*", "")
    return _clean_wikitext(raw)
