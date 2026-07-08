"""Open-Meteo weather (free, no key)."""
import requests

GEO = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST = "https://api.open-meteo.com/v1/forecast"
WMO = {
    0: "Clear", 1: "Mostly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Rime fog", 51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain", 66: "Freezing rain", 67: "Freezing rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow", 77: "Snow grains",
    80: "Light showers", 81: "Showers", 82: "Violent showers",
    85: "Snow showers", 86: "Snow showers", 95: "Thunderstorm",
    96: "Thunderstorm w/ hail", 99: "Thunderstorm w/ hail",
}


def get_weather(city: str) -> dict | None:
    """Current conditions + 3-day forecast + local time for a city name."""
    try:
        g = requests.get(GEO, params={"name": city, "count": 1}, timeout=10).json()
        if not g.get("results"):
            return None
        loc = g["results"][0]
        f = requests.get(FORECAST, params={
            "latitude": loc["latitude"], "longitude": loc["longitude"],
            "current": "temperature_2m,weather_code,relative_humidity_2m,wind_speed_10m",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "timezone": "auto", "forecast_days": 3,
        }, timeout=10).json()
        cur, daily = f.get("current", {}), f.get("daily", {})
        return {
            "city": loc["name"],
            "country": loc.get("country", ""),
            "timezone": f.get("timezone"),
            "local_time": cur.get("time"),
            "now": {
                "temp_c": cur.get("temperature_2m"),
                "condition": WMO.get(cur.get("weather_code"), "?"),
                "humidity": cur.get("relative_humidity_2m"),
                "wind_kmh": cur.get("wind_speed_10m"),
            },
            "daily": [
                {
                    "date": daily["time"][i],
                    "condition": WMO.get(daily["weather_code"][i], "?"),
                    "high_c": daily["temperature_2m_max"][i],
                    "low_c": daily["temperature_2m_min"][i],
                    "rain_pct": daily["precipitation_probability_max"][i],
                }
                for i in range(len(daily.get("time", [])))
            ],
        }
    except Exception:
        return None
