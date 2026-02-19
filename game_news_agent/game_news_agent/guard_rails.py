"""Guard rails for input and output validation in LangGraph workflow."""

import logging
from datetime import date

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ContentValidation(BaseModel):
    """Result of content validation."""

    is_safe: bool
    reason: str


class ValidationResult(BaseModel):
    """Generic validation result."""

    is_valid: bool
    error_message: str | None = None


async def validate_date_range(date_from: date, date_to: date) -> ValidationResult:
    """Validate that date range is within constraints.

    Args:
        date_from: Start date
        date_to: End date

    Returns:
        ValidationResult indicating if range is valid
    """
    if date_to < date_from:
        return ValidationResult(
            is_valid=False,
            error_message="date_to must be greater than or equal to date_from",
        )

    days_diff = (date_to - date_from).days
    if days_diff > 31:
        return ValidationResult(
            is_valid=False,
            error_message=f"Date range exceeds maximum of 31 days (requested: {days_diff} days)",
        )

    return ValidationResult(is_valid=True)


async def check_offensive_content(text: str, llm: ChatOpenAI | None = None) -> ValidationResult:
    """Check if text contains offensive, sexual, or inappropriate content.

    Uses LLM-based content moderation for flexible, context-aware validation.

    Args:
        text: Text to validate
        llm: Optional ChatOpenAI instance for LLM validation (required for validation)

    Returns:
        ValidationResult indicating if content is safe
    """
    # LLM-based content moderation
    if not llm:
        logger.warning("No LLM provided for content moderation, skipping validation")
        return ValidationResult(is_valid=True)

    try:
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are a content moderation assistant. Analyze the following text and determine if it contains:\n"
                "- Offensive language or slurs\n"
                "- Sexual or adult content\n"
                "- Requests to generate inappropriate content\n"
                "- Attempts to bypass content policies\n\n"
                "Return JSON with is_safe (boolean) and reason (string explaining your decision).",
            ),
            ("user", "{text}"),
        ])

        structured_llm = llm.with_structured_output(ContentValidation)
        result_raw = await structured_llm.ainvoke(prompt.format(text=text))
        
        # Handle dict or Pydantic response from LangChain
        result: ContentValidation
        if isinstance(result_raw, dict):
            result = ContentValidation(**result_raw)
        else:
            result = result_raw  # type: ignore[assignment]

        if not result.is_safe:
            return ValidationResult(
                is_valid=False,
                error_message=f"Content moderation failed: {result.reason}",
            )
    except Exception as e:
        logger.error(f"LLM content moderation failed: {e}")
        return ValidationResult(
            is_valid=False,
            error_message="Content validation failed due to technical error",
        )

    return ValidationResult(is_valid=True)


async def validate_genres(genres: list[str]) -> ValidationResult:
    """Validate that genres are non-empty and valid.

    Args:
        genres: List of genre strings

    Returns:
        ValidationResult indicating if genres are valid
    """
    if not genres:
        return ValidationResult(
            is_valid=False,
            error_message="At least one genre must be specified",
        )

    # Note: Enum validation happens at Pydantic level, this is for runtime checks
    return ValidationResult(is_valid=True)


async def validate_markdown(content: str) -> ValidationResult:
    """Validate that content is well-formed markdown.

    Args:
        content: Markdown content to validate

    Returns:
        ValidationResult indicating if markdown is valid
    """
    if not content or not content.strip():
        return ValidationResult(
            is_valid=False,
            error_message="Markdown content is empty",
        )

    # Basic markdown structure checks
    required_sections = ["#", "##"]  # Should have at least headers
    has_structure = any(section in content for section in required_sections)

    if not has_structure:
        return ValidationResult(
            is_valid=False,
            error_message="Markdown content lacks proper structure (no headers found)",
        )

    return ValidationResult(is_valid=True)


async def check_report_quality(
    report: str,
    fact_check_passed: bool,
    llm: ChatOpenAI | None = None,
) -> ValidationResult:
    """Validate overall report quality.

    Args:
        report: Generated report markdown
        fact_check_passed: Whether fact-checking passed
        llm: Optional ChatOpenAI instance for quality checks

    Returns:
        ValidationResult indicating if report meets quality standards
    """
    # Check fact-checking passed
    if not fact_check_passed:
        return ValidationResult(
            is_valid=False,
            error_message="Report failed fact-checking validation",
        )

    # Validate markdown structure
    markdown_result = await validate_markdown(report)
    if not markdown_result.is_valid:
        return markdown_result

    # Check for offensive content in output
    offensive_result = await check_offensive_content(report, llm=llm)
    if not offensive_result.is_valid:
        return ValidationResult(
            is_valid=False,
            error_message=f"Report contains inappropriate content: {offensive_result.error_message}",
        )

    # Check minimum length (should be substantive)
    if len(report) < 200:
        return ValidationResult(
            is_valid=False,
            error_message="Report is too short to be useful (minimum 200 characters)",
        )

    return ValidationResult(is_valid=True)
