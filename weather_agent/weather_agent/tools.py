"""Weather Agent Tools."""

import logging

from agents import function_tool

from weather_agent.weather_service import (
    AirQualityResult,
    CurrentWeatherResult,
    ForecastResult,
    WeatherService,
)

logger: logging.Logger = logging.getLogger(name=__name__)


@function_tool
async def get_weather_report(location: str) -> str:
    """Get the current weather for a specific location."""
    logger.info("Tool get_weather_report invoked with location=%s", location)
    result: CurrentWeatherResult = await WeatherService().get_current_weather(location)
    return (
        f"Current weather in {result.location}, {result.region}, {result.country}:\n"
        f"  Temperature: {result.temp_c:.1f}°C (feels like {result.feelslike_c:.1f}°C)\n"
        f"  Condition: {result.condition}\n"
        f"  Humidity: {result.humidity:.0f}%\n"
        f"  Wind: {result.wind_kph:.1f} km/h {result.wind_dir}\n"
        f"  Precipitation: {result.precip_mm:.1f} mm\n"
        f"  UV Index: {result.uv}\n"
        f"  Daytime: {'Yes' if result.is_day else 'No'}"
    )


@function_tool
async def get_air_quality_report(location: str) -> str:
    """Get the current air quality for a specific location."""
    logger.info("Tool get_air_quality_report invoked with location=%s", location)
    result: AirQualityResult = await WeatherService().get_air_quality(location)
    return (
        f"Air quality in {result.location}:\n"
        f"  US EPA Index: {result.us_epa_index} ({result.us_epa_label})\n"
        f"  GB DEFRA Index: {result.gb_defra_index}\n"
        f"  PM2.5: {result.pm2_5:.1f} μg/m³\n"
        f"  PM10: {result.pm10:.1f} μg/m³\n"
        f"  CO: {result.co:.1f} μg/m³\n"
        f"  NO2: {result.no2:.1f} μg/m³\n"
        f"  O3: {result.o3:.1f} μg/m³"
    )


@function_tool
async def get_forecast(location: str, days: int = 3) -> str:
    """Get a multi-day weather forecast for a specific location.

    Args:
        location: City name, postcode, coordinates or IP address.
        days: Number of forecast days (1-14, default 3).

    """
    logger.info(
        "Tool get_forecast invoked with location=%s days=%s",
        location,
        days,
    )
    result: ForecastResult = await WeatherService().get_forecast(location, days)
    lines = [f"Weather forecast for {result.location} ({len(result.days)} days):"]
    for day in result.days:
        lines.append(
            f"  {day.date}: {day.condition} | "
            f"{day.min_temp_c:.1f}°C - {day.max_temp_c:.1f}°C | "
            f"Rain: {day.chance_of_rain:.0f}% | "
            f"Precip: {day.total_precip_mm:.1f} mm | "
            f"UV: {day.uv:.0f}",
        )
    return "\n".join(lines)
