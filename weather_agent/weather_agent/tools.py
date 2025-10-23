"""Weather Agent Tools."""

import logging

from agents import function_tool
from weather_service import WeatherResponse, WeatherService

logger: logging.Logger = logging.getLogger(name=__name__)

@function_tool
async def get_weather_report(location: str) -> str:
    """Get the weather report for a specific location."""
    logger.info(
        "Tool get_weather_report invoked with location=%s",
        location,
    )

    weather_service = WeatherService()
    weather_response: WeatherResponse = weather_service.get_weather_for_location(location=location)
    return f"Weather in {location}: {weather_response.weather_condition} with {weather_response.temperature}°C."

@function_tool
async def get_air_quality_report(location: str) -> str:
    """Report air quality for the given location."""
    logger.info(
        "Tool get_air_quality_report invoked with location=%s",
        location,
    )
    weather_service = WeatherService()
    air_quality_response: WeatherResponse = weather_service.get_weather_for_location(location=location)
    return f"Air quality in {location}: AQI {air_quality_response.air_quality} ({air_quality_response.weather_condition})."