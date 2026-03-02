"""LangGraph-based review analyzer for game sentiment analysis."""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime
from typing import TypedDict

from langchain_core.messages import AIMessage
from langchain_core.runnables.config import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from game_news_agent.game_service_kiota import GameReview, RAWGKiotaClient
from game_news_agent.models import (
    GameInfo,
    ReviewAnalysisRequest,
    ReviewAnalysisResponse,
    ReviewSentiment,
    ReviewSummary,
)
from rawg_kiota_client.models.game_single import GameSingle

logger = logging.getLogger(__name__)


class ReviewAnalysisState(TypedDict):
    """State for review analysis workflow."""

    # Input
    request: ReviewAnalysisRequest
    context_id: str

    # Game information
    game_info: GameSingle | None
    validation_errors: list[str]

    # Review data
    positive_reviews_data: list[GameReview]
    negative_reviews_data: list[GameReview]

    # Analysis results
    positive_summary: ReviewSummary | None
    negative_summary: ReviewSummary | None
    analysis_markdown: str

    # Final
    output_valid: bool
    error_message: str | None


class ReviewAnalyzer:
    """LangGraph-based review analyzer with sentiment analysis."""

    def __init__(self, llm: ChatOpenAI | None = None):
        """Initialize the review analyzer.

        Args:
            llm: Optional ChatOpenAI instance (created from env if not provided)
        """
        self.llm = llm or ChatOpenAI(
            model=os.getenv("OPENAI_CHAT_MODEL_ID", "gpt-4o"),
            temperature=0.3,  # Lower temperature for more consistent analysis
            model_kwargs={"response_format": {"type": "json_object"}},
        )

        self.memory = MemorySaver()
        self.graph = self._build_graph()
        self.compiled_graph = self.graph.compile(checkpointer=self.memory)

    def _build_graph(self) -> StateGraph:
        """Build the review analysis workflow graph.

        Workflow:
        1. Fetch game details
        2. Fetch positive reviews (high ratings)
        3. Fetch negative reviews (low ratings)
        4. Analyze positive reviews
        5. Analyze negative reviews
        6. Generate markdown report
        """
        workflow = StateGraph(ReviewAnalysisState)

        # Add nodes
        workflow.add_node("fetch_game_info", self._fetch_game_info)
        workflow.add_node("fetch_positive_reviews", self._fetch_positive_reviews)
        workflow.add_node("fetch_negative_reviews", self._fetch_negative_reviews)
        workflow.add_node("analyze_positive", self._analyze_positive_reviews)
        workflow.add_node("analyze_negative", self._analyze_negative_reviews)
        workflow.add_node("generate_markdown", self._generate_markdown)

        # Define flow
        workflow.set_entry_point("fetch_game_info")
        workflow.add_edge("fetch_game_info", "fetch_positive_reviews")
        workflow.add_edge("fetch_positive_reviews", "fetch_negative_reviews")
        workflow.add_edge("fetch_negative_reviews", "analyze_positive")
        workflow.add_edge("analyze_positive", "analyze_negative")
        workflow.add_edge("analyze_negative", "generate_markdown")
        workflow.add_edge("generate_markdown", END)

        return workflow

    async def _fetch_game_info(self, state: ReviewAnalysisState) -> dict:
        """Fetch game details from RAWG API."""
        logger.info(f"Fetching game info for ID: {state['request'].game_id}")

        async with RAWGKiotaClient() as client:
            game_data = await client.get_game_details(state["request"].game_id)

        if not game_data:
            logger.error(f"Game not found: {state['request'].game_id}")
            return {
                "game_info": None,
                "validation_errors": [f"Game with ID {state['request'].game_id} not found"],
            }

        # game_data is already a typed GameSingle model
        logger.info(f"Found game: {game_data.name}")
        return {
            "game_info": game_data,
            "validation_errors": [],
        }

    async def _fetch_positive_reviews(self, state: ReviewAnalysisState) -> dict:
        """Fetch positive reviews (high ratings) from RAWG."""
        if state.get("validation_errors"):
            return {"positive_reviews_data": []}

        game_info = state.get("game_info")
        game_ref = game_info.slug if game_info and game_info.slug else state["request"].game_id
        logger.info(f"Fetching positive reviews for '{game_ref}'")

        async with RAWGKiotaClient() as client:
            reviews = await client.get_game_reviews(
                game_ref,
                page_size=state["request"].review_count,
                ordering="-rating",  # Highest-rated first
            )

        # Prioritise reviews with the most community upvotes so the LLM gets the most useful content
        reviews.sort(key=lambda r: r.likes_positive, reverse=True)
        logger.info(f"Found {len(reviews)} positive reviews")
        return {"positive_reviews_data": reviews}

    async def _fetch_negative_reviews(self, state: ReviewAnalysisState) -> dict:
        """Fetch negative reviews (low ratings) from RAWG."""
        if state.get("validation_errors"):
            return {"negative_reviews_data": []}

        game_info = state.get("game_info")
        game_ref = game_info.slug if game_info and game_info.slug else state["request"].game_id
        logger.info(f"Fetching negative reviews for '{game_ref}'")

        async with RAWGKiotaClient() as client:
            # Fetch a larger pool ordered by lowest rating first;
            # negative reviews are rare for popular games so we cast a wider net.
            reviews = await client.get_game_reviews(
                game_ref,
                page_size=max(state["request"].review_count * 4, 40),
                ordering="rating",  # Lowest-rated first
            )

        # rating 1-3 out of 5 — captures critical but not just contrarian 1-star reviews
        negative = [r for r in reviews if r.rating <= 3]
        negative.sort(key=lambda r: r.likes_positive, reverse=True)
        logger.info(f"Found {len(negative)} negative reviews (rating ≤ 3)")
        return {"negative_reviews_data": negative}

    async def _analyze_positive_reviews(self, state: ReviewAnalysisState) -> dict:
        """Analyze positive reviews using LLM."""
        if state.get("validation_errors"):
            return {"positive_summary": None}

        reviews_data = state.get("positive_reviews_data", [])

        if not reviews_data:
            # Create summary indicating no positive reviews
            return {
                "positive_summary": ReviewSummary(
                    sentiment=ReviewSentiment.POSITIVE,
                    review_count=0,
                    common_themes=[],
                    summary_text="No positive reviews available for analysis.",
                    sample_quotes=[],
                )
            }

        logger.info("Analyzing positive reviews with LLM")

        # Prepare reviews text for LLM
        reviews_text = "\n\n".join([
            f"Review {i+1} (rating {review.rating}/5, {review.likes_positive} helpful votes, by {review.username}):\n{review.text}"
            for i, review in enumerate(reviews_data[:state["request"].review_count])
        ])

        prompt = f"""Analyze the following positive user reviews for a game and provide:
1. 3-5 common themes mentioned across reviews
2. A concise summary (2-3 sentences) of the positive feedback
3. 2-3 representative quotes from the reviews

Reviews:
{reviews_text}

Respond in JSON format:
{{
    "common_themes": ["theme1", "theme2", ...],
    "summary_text": "summary here",
    "sample_quotes": ["quote1", "quote2", ...]
}}"""

        try:
            response: AIMessage = await self.llm.ainvoke(prompt)
            content = response.content if isinstance(response.content, str) else str(response.content)
            raw = re.sub(r'^```(?:json)?\s*|\s*```$', '', content.strip(), flags=re.MULTILINE)
            analysis = json.loads(raw)

            summary = ReviewSummary(
                sentiment=ReviewSentiment.POSITIVE,
                review_count=len(reviews_data),
                common_themes=analysis.get("common_themes", []),
                summary_text=analysis.get("summary_text", ""),
                sample_quotes=analysis.get("sample_quotes", []),
            )

            return {"positive_summary": summary}
        except Exception as e:
            logger.error(f"Error analyzing positive reviews: {e}")
            return {
                "positive_summary": ReviewSummary(
                    sentiment=ReviewSentiment.POSITIVE,
                    review_count=len(reviews_data),
                    common_themes=["Analysis error"],
                    summary_text=f"Error during analysis: {str(e)}",
                    sample_quotes=[],
                )
            }

    async def _analyze_negative_reviews(self, state: ReviewAnalysisState) -> dict:
        """Analyze negative reviews using LLM."""
        if state.get("validation_errors"):
            return {"negative_summary": None}

        reviews_data = state.get("negative_reviews_data", [])

        if not reviews_data:
            # Create summary indicating no negative reviews or use game rating
            game_info = state.get("game_info")

            if game_info and game_info.rating and game_info.rating >= 4.0:
                summary_text = "The game has received overwhelmingly positive feedback with minimal criticism."
            else:
                summary_text = "Limited negative review data available for analysis."

            return {
                "negative_summary": ReviewSummary(
                    sentiment=ReviewSentiment.NEGATIVE,
                    review_count=0,
                    common_themes=[],
                    summary_text=summary_text,
                    sample_quotes=[],
                )
            }

        logger.info("Analyzing negative reviews with LLM")

        reviews_text = "\n\n".join([
            f"Review {i+1} (rating {review.rating}/5, {review.likes_positive} helpful votes, by {review.username}):\n{review.text}"
            for i, review in enumerate(reviews_data[:state["request"].review_count])
        ])

        prompt = f"""Analyze the following negative user reviews for a game and provide:
1. 3-5 common criticisms mentioned across reviews
2. A concise summary (2-3 sentences) of the negative feedback
3. 2-3 representative quotes from the reviews

Reviews:
{reviews_text}

Respond in JSON format:
{{
    "common_themes": ["criticism1", "criticism2", ...],
    "summary_text": "summary here",
    "sample_quotes": ["quote1", "quote2", ...]
}}"""

        try:
            response = await self.llm.ainvoke(prompt)
            content = response.content if isinstance(response.content, str) else str(response.content)
            raw = re.sub(r'^```(?:json)?\s*|\s*```$', '', content.strip(), flags=re.MULTILINE)
            analysis = json.loads(raw)

            summary = ReviewSummary(
                sentiment=ReviewSentiment.NEGATIVE,
                review_count=len(reviews_data),
                common_themes=analysis.get("common_themes", []),
                summary_text=analysis.get("summary_text", ""),
                sample_quotes=analysis.get("sample_quotes", []),
            )

            return {"negative_summary": summary}
        except Exception as e:
            logger.error(f"Error analyzing negative reviews: {e}")
            return {
                "negative_summary": ReviewSummary(
                    sentiment=ReviewSentiment.NEGATIVE,
                    review_count=len(reviews_data),
                    common_themes=["Analysis error"],
                    summary_text=f"Error during analysis: {str(e)}",
                    sample_quotes=[],
                )
            }

    async def _generate_markdown(self, state: ReviewAnalysisState) -> dict:
        """Generate markdown report from analysis results."""
        if state.get("validation_errors"):
            return {
                "analysis_markdown": "# Error\n\n" + "\n".join(f"- {err}" for err in state["validation_errors"]),
                "output_valid": False,
                "error_message": "; ".join(state["validation_errors"]),
            }

        game_info = state.get("game_info")
        positive = state.get("positive_summary")
        negative = state.get("negative_summary")

        # Build markdown report - game_info is already typed GameSingle model
        game_name = game_info.name if game_info else "Unknown Game"
        release_date = str(game_info.released) if game_info and game_info.released else "TBD"
        rating = f"{game_info.rating}/5.0" if game_info else "N/A"
        metacritic = str(game_info.metacritic) if game_info and game_info.metacritic else "N/A"

        md_parts = [
            f"# Review Analysis: {game_name}",
            "",
            "## Game Information",
            f"- **Release Date**: {release_date}",
            f"- **Average Rating**: {rating}",
            f"- **Metacritic Score**: {metacritic}",
            "",
        ]

        # Positive reviews section
        if positive:
            md_parts.extend([
                f"## Positive Reviews ({positive.review_count} analyzed)",
                "",
                "### Common Positive Themes",
                *[f"- {theme}" for theme in positive.common_themes],
                "",
                "### Summary",
                positive.summary_text,
                "",
            ])

            if positive.sample_quotes:
                md_parts.extend([
                    "### Sample Quotes",
                    *[f"> {quote}" for quote in positive.sample_quotes],
                    "",
                ])

        # Negative reviews section
        if negative:
            criticisms = (
                [f"- {theme}" for theme in negative.common_themes]
                if negative.common_themes
                else ["- No significant criticisms found"]
            )
            md_parts.extend([
                f"## Negative Reviews ({negative.review_count} analyzed)",
                "",
                "### Common Criticisms",
                *criticisms,
                "",
                "### Summary",
                negative.summary_text,
                "",
            ])

            if negative.sample_quotes:
                md_parts.extend([
                    "### Sample Quotes",
                    *[f"> {quote}" for quote in negative.sample_quotes],
                    "",
                ])

        # Footer
        md_parts.extend([
            "---",
            f"*Analysis generated at {datetime.now().isoformat()}*",
            "",
            "*Data source: RAWG.io user-generated content*",
        ])

        markdown = "\n".join(md_parts)

        return {
            "analysis_markdown": markdown,
            "output_valid": True,
            "error_message": None,
        }

    async def invoke(self, request: ReviewAnalysisRequest, context_id: str) -> ReviewAnalysisResponse:
        """Execute review analysis workflow.

        Args:
            request: Review analysis request
            context_id: Unique context identifier for the session

        Returns:
            ReviewAnalysisResponse with positive/negative summaries
        """
        logger.info(f"Starting review analysis for game_id={request.game_id}, context_id={context_id}")

        # Initialize state
        initial_state: ReviewAnalysisState = {
            "request": request,
            "context_id": context_id,
            "game_info": None,
            "validation_errors": [],
            "positive_reviews_data": [],
            "negative_reviews_data": [],
            "positive_summary": None,
            "negative_summary": None,
            "analysis_markdown": "",
            "output_valid": False,
            "error_message": None,
        }

        # Run the graph
        config: RunnableConfig = {"configurable": {"thread_id": context_id}}
        final_state = await self.compiled_graph.ainvoke(initial_state, config)

        # Build response - game_info is already a typed GameSingle model
        game_info_model = final_state.get("game_info")
        if not game_info_model:
            # Fallback if game info wasn't found
            game_info = GameInfo(
                id=request.game_id,
                name="Unknown",
                released=None,
                rating=None,
                metacritic=None,
            )
        else:
            # Convert GameSingle to GameInfo
            game_info = GameInfo(
                id=game_info_model.id,
                name=game_info_model.name,
                released=game_info_model.released,
                rating=game_info_model.rating,
                metacritic=game_info_model.metacritic,
            )

        return ReviewAnalysisResponse(
            game=game_info,
            positive_reviews=final_state.get("positive_summary") or ReviewSummary(
                sentiment=ReviewSentiment.POSITIVE,
                review_count=0,
                common_themes=[],
                summary_text="No analysis available",
                sample_quotes=[],
            ),
            negative_reviews=final_state.get("negative_summary") or ReviewSummary(
                sentiment=ReviewSentiment.NEGATIVE,
                review_count=0,
                common_themes=[],
                summary_text="No analysis available",
                sample_quotes=[],
            ),
            analysis_markdown=final_state.get("analysis_markdown", ""),
            generated_at=datetime.now(),
            validation_errors=final_state.get("validation_errors") if final_state.get("validation_errors") else None,
        )
