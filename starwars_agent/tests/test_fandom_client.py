"""Tests for the Fandom MediaWiki API client."""

import pytest
from pytest_httpx import HTTPXMock

from starwars_agent.data_pipeline.fandom_client import (
    _clean_wikitext,
    fetch_category_members,
    fetch_page_content,
)


class TestCleanWikitext:
    """Unit tests for wikitext cleaning regex."""

    def test_strips_templates(self):
        assert _clean_wikitext("Hello {{Infobox|data}} world") == "Hello world"

    def test_strips_file_embeds(self):
        assert _clean_wikitext("Text [[File:Example.png]] more") == "Text more"

    def test_strips_image_embeds(self):
        assert _clean_wikitext("Text [[Image:Pic.jpg|thumb]] more") == "Text more"

    def test_converts_display_links(self):
        assert _clean_wikitext("The [[Galactic Empire|Empire]] fell") == "The Empire fell"

    def test_converts_plain_links(self):
        assert _clean_wikitext("Visit [[Tatooine]] today") == "Visit Tatooine today"

    def test_strips_bold_italic(self):
        assert _clean_wikitext("'''bold''' and ''italic''") == "bold and italic"

    def test_strips_inline_refs(self):
        assert _clean_wikitext("Fact<ref name='a'>source</ref> here") == "Fact here"

    def test_strips_self_closing_refs(self):
        assert _clean_wikitext("Fact<ref name='a'/> here") == "Fact here"

    def test_strips_html_tags(self):
        assert _clean_wikitext("<small>tiny</small> text") == "tiny text"

    def test_collapses_blank_lines(self):
        result = _clean_wikitext("Line one\n\n\n\nLine two")
        # regex strips 3+ newlines, then re.sub collapses remaining 2+ to 2
        assert "\n\n\n" not in result

    def test_empty_input(self):
        assert _clean_wikitext("") == ""


class TestFetchCategoryMembers:
    """Tests for category member pagination against the Fandom API."""

    @pytest.mark.asyncio
    async def test_single_page_response(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(json={
            "query": {
                "categorymembers": [
                    {"pageid": 1, "title": "A New Hope"},
                    {"pageid": 2, "title": "The Empire Strikes Back"},
                ],
            },
        })

        result = await fetch_category_members("Saga_films")

        assert len(result) == 2
        assert result[0] == {"pageid": 1, "title": "A New Hope"}
        assert result[1] == {"pageid": 2, "title": "The Empire Strikes Back"}

    @pytest.mark.asyncio
    async def test_paginated_response(self, httpx_mock: HTTPXMock):
        """Ensure cmcontinue is followed across pages."""
        httpx_mock.add_response(json={
            "query": {
                "categorymembers": [
                    {"pageid": 1, "title": "A New Hope"},
                ],
            },
            "continue": {"cmcontinue": "page2token", "continue": "-||"},
        })
        httpx_mock.add_response(json={
            "query": {
                "categorymembers": [
                    {"pageid": 2, "title": "The Empire Strikes Back"},
                ],
            },
        })

        result = await fetch_category_members("Saga_films")

        assert len(result) == 2
        assert result[0]["pageid"] == 1
        assert result[1]["pageid"] == 2

    @pytest.mark.asyncio
    async def test_empty_category(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(json={
            "query": {"categorymembers": []},
        })

        result = await fetch_category_members("Empty_category")

        assert result == []

    @pytest.mark.asyncio
    async def test_http_error_raises(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(status_code=500)

        with pytest.raises(Exception):
            await fetch_category_members("Saga_films")


class TestFetchPageContent:
    """Tests for fetching and cleaning individual page content."""

    @pytest.mark.asyncio
    async def test_returns_cleaned_content(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(json={
            "parse": {
                "title": "A New Hope",
                "wikitext": {
                    "*": "'''Star Wars''' is a [[science fiction|sci-fi]] film.",
                },
            },
        })

        result = await fetch_page_content("A New Hope")

        assert "Star Wars" in result
        assert "sci-fi" in result
        # Markup should be stripped
        assert "'''" not in result
        assert "[[" not in result

    @pytest.mark.asyncio
    async def test_missing_wikitext_returns_empty(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(json={"parse": {}})

        result = await fetch_page_content("Missing Page")

        assert result == ""

    @pytest.mark.asyncio
    async def test_http_error_raises(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(status_code=404)

        with pytest.raises(Exception):
            await fetch_page_content("Nonexistent")
