"""Weather API Service."""

import random


class WeatherResponse:
    """Represents the weather response for a specific location."""

    location: str
    temperature: int
    weather_condition: str
    air_quality: str

    def __init__(self, location: str, temperature: int, weather_condition: str, air_quality: str) -> None:
        """"""
        self.location = location
        self.temperature = temperature
        self.weather_condition = weather_condition
        self.air_quality = air_quality


class WeatherService:
    """The weather service."""

    WEATHER_CONDITIONS: tuple[str, ...] = (
        "sunny",
        "cloudy",
        "rainy",
        "stormy",
        "snowy",
    )

    AIR_QUALITY_DESCRIPTIONS: tuple[str, ...] = (
        "Good",
        "Moderate",
        "Unhealthy for Sensitive Groups",
        "Unhealthy",
    )

    def __init__(self) -> None:
        """Initialize the WeatherService."""
        pass


    def get_weather_conditions(self) -> tuple[str, ...]:
        """Get the weather conditions."""
        return self.WEATHER_CONDITIONS

    def get_air_quality_descriptions(self) -> tuple[str, ...]:
        """Get the air quality descriptions."""
        return self.AIR_QUALITY_DESCRIPTIONS

    def get_weather_for_location(self, location: str) -> WeatherResponse:
        """Get pseudo-random weather for a specific location."""
        temperature: int = random.randint(a=-10, b=35)
        weather_condition: str = random.choice(seq=self.WEATHER_CONDITIONS)
        air_quality: str = random.choice(seq=self.AIR_QUALITY_DESCRIPTIONS)

        return WeatherResponse(
            location=location,
            temperature=temperature,
            weather_condition=weather_condition,
            air_quality=air_quality,
        )
