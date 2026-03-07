"""Weather API Service - WeatherAPI.com httpx client with mock fallback."""

from __future__ import annotations

import datetime
import logging
import os
import random
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.weatherapi.com/v1"

# EPA index -> human-readable label
_EPA_LABELS: dict[int, str] = {
    1: "Good",
    2: "Moderate",
    3: "Unhealthy for Sensitive Groups",
    4: "Unhealthy",
    5: "Very Unhealthy",
    6: "Hazardous",
}

_MOCK_CONDITIONS = ("Sunny", "Cloudy", "Rainy", "Stormy", "Snowy", "Partly cloudy")
_MOCK_DIRS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


@dataclass
class CurrentWeatherResult:
    """Condensed current weather for a location."""

    location: str
    region: str
    country: str
    temp_c: float
    feelslike_c: float
    condition: str
    humidity: float
    wind_kph: float
    wind_dir: str
    precip_mm: float
    uv: int
    is_day: bool


@dataclass
class AirQualityResult:
    """Condensed air quality data for a location."""

    location: str
    co: float
    no2: float
    o3: float
    pm2_5: float
    pm10: float
    us_epa_index: int
    us_epa_label: str
    gb_defra_index: int


@dataclass
class ForecastDayResult:
    """Single day in a forecast."""

    date: str
    max_temp_c: float
    min_temp_c: float
    avg_temp_c: float
    condition: str
    chance_of_rain: float
    total_precip_mm: float
    uv: float


@dataclass
class ForecastResult:
    """Multi-day forecast for a location."""

    location: str
    days: list[ForecastDayResult]


def _is_mock() -> bool:
    return os.getenv("WEATHERAPI_MOCK", "false").lower() in ("1", "true", "yes")


def _api_key() -> str:
    key = os.getenv("WEATHERAPI_KEY", "")
    if not key:
        msg = "WEATHERAPI_KEY environment variable is not set"
        raise ValueError(msg)
    return key


class WeatherService:
    """Facade over WeatherAPI.com with WEATHERAPI_MOCK=true stub mode."""

    # ------------------------------------------------------------------
    # Current weather
    # ------------------------------------------------------------------

    async def get_current_weather(self, location: str) -> CurrentWeatherResult:
        """Return current weather for *location*.

        If WEATHERAPI_MOCK=true, returns synthetic data instead.
        """
        if _is_mock():
            return self._mock_current(location)

        key = _api_key()
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{_BASE_URL}/current.json",
                params={"key": key, "q": location, "aqi": "yes"},
            )
            resp.raise_for_status()
            data = resp.json()

        loc = data["location"]
        cur = data["current"]
        return CurrentWeatherResult(
            location=loc.get("name", location),
            region=loc.get("region", ""),
            country=loc.get("country", ""),
            temp_c=cur.get("temp_c", 0.0),
            feelslike_c=cur.get("feelslike_c", 0.0),
            condition=cur.get("condition", {}).get("text", ""),
            humidity=cur.get("humidity", 0.0),
            wind_kph=cur.get("wind_kph", 0.0),
            wind_dir=cur.get("wind_dir", ""),
            precip_mm=cur.get("precip_mm", 0.0),
            uv=cur.get("uv", 0),
            is_day=bool(cur.get("is_day", 1)),
        )

    # ------------------------------------------------------------------
    # Air quality
    # ------------------------------------------------------------------

    async def get_air_quality(self, location: str) -> AirQualityResult:
        """Return air quality for *location*.

        Reuses the current weather endpoint with ``aqi=yes``.
        """
        if _is_mock():
            return self._mock_air_quality(location)

        key = _api_key()
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{_BASE_URL}/current.json",
                params={"key": key, "q": location, "aqi": "yes"},
            )
            resp.raise_for_status()
            data = resp.json()

        loc = data["location"]
        aq = data.get("current", {}).get("air_quality", {})
        epa = aq.get("us-epa-index", 1)
        return AirQualityResult(
            location=loc.get("name", location),
            co=aq.get("co", 0.0),
            no2=aq.get("no2", 0.0),
            o3=aq.get("o3", 0.0),
            pm2_5=aq.get("pm2_5", 0.0),
            pm10=aq.get("pm10", 0.0),
            us_epa_index=epa,
            us_epa_label=_EPA_LABELS.get(epa, "Unknown"),
            gb_defra_index=aq.get("gb-defra-index", 0),
        )

    # ------------------------------------------------------------------
    # Forecast
    # ------------------------------------------------------------------

    async def get_forecast(self, location: str, days: int = 3) -> ForecastResult:
        """Return a multi-day weather forecast for *location*.

        *days* must be 1-14.
        """
        if _is_mock():
            return self._mock_forecast(location, days)

        key = _api_key()
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{_BASE_URL}/forecast.json",
                params={"key": key, "q": location, "days": days, "aqi": "no", "alerts": "no"},
            )
            resp.raise_for_status()
            data = resp.json()

        loc = data["location"]
        day_results: list[ForecastDayResult] = []
        for fd in data.get("forecast", {}).get("forecastday", []):
            d = fd.get("day", {})
            day_results.append(
                ForecastDayResult(
                    date=fd.get("date", ""),
                    max_temp_c=d.get("maxtemp_c", 0.0),
                    min_temp_c=d.get("mintemp_c", 0.0),
                    avg_temp_c=d.get("avgtemp_c", 0.0),
                    condition=d.get("condition", {}).get("text", ""),
                    chance_of_rain=d.get("daily_chance_of_rain", 0.0),
                    total_precip_mm=d.get("totalprecip_mm", 0.0),
                    uv=d.get("uv", 0.0),
                ),
            )

        return ForecastResult(location=loc.get("name", location), days=day_results)

    # ------------------------------------------------------------------
    # Mock helpers
    # ------------------------------------------------------------------

    def _mock_current(self, location: str) -> CurrentWeatherResult:
        logger.info(
            "WEATHERAPI_MOCK enabled - synthetic current weather for %s", location
        )
        return CurrentWeatherResult(
            location=location,
            region="Mock Region",
            country="Mockland",
            temp_c=random.uniform(-5, 35),  # noqa: S311
            feelslike_c=random.uniform(-7, 33),  # noqa: S311
            condition=random.choice(_MOCK_CONDITIONS),  # noqa: S311
            humidity=random.uniform(30, 95),  # noqa: S311
            wind_kph=random.uniform(0, 60),  # noqa: S311
            wind_dir=random.choice(_MOCK_DIRS),  # noqa: S311
            precip_mm=random.uniform(0, 20),  # noqa: S311
            uv=random.randint(0, 11),  # noqa: S311
            is_day=True,
        )

    def _mock_air_quality(self, location: str) -> AirQualityResult:
        logger.info(
            "WEATHERAPI_MOCK enabled - synthetic air quality for %s", location
        )
        epa = random.randint(1, 4)  # noqa: S311
        return AirQualityResult(
            location=location,
            co=random.uniform(100, 800),  # noqa: S311
            no2=random.uniform(1, 50),  # noqa: S311
            o3=random.uniform(10, 120),  # noqa: S311
            pm2_5=random.uniform(1, 75),  # noqa: S311
            pm10=random.uniform(5, 150),  # noqa: S311
            us_epa_index=epa,
            us_epa_label=_EPA_LABELS.get(epa, "Unknown"),
            gb_defra_index=random.randint(1, 10),  # noqa: S311
        )

    def _mock_forecast(self, location: str, days: int) -> ForecastResult:
        logger.info("WEATHERAPI_MOCK enabled - synthetic forecast for %s", location)
        today = datetime.datetime.now(tz=datetime.UTC).date()
        day_results = []
        for i in range(days):
            date = (today + datetime.timedelta(days=i)).isoformat()
            day_results.append(
                ForecastDayResult(
                    date=date,
                    max_temp_c=random.uniform(10, 35),  # noqa: S311
                    min_temp_c=random.uniform(-5, 15),  # noqa: S311
                    avg_temp_c=random.uniform(5, 25),  # noqa: S311
                    condition=random.choice(_MOCK_CONDITIONS),  # noqa: S311
                    chance_of_rain=random.uniform(0, 100),  # noqa: S311
                    total_precip_mm=random.uniform(0, 30),  # noqa: S311
                    uv=random.uniform(0, 11),  # noqa: S311
                ),
            )
        return ForecastResult(location=location, days=day_results)
