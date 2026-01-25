import requests
from pathlib import Path

# ==========================================
# 1. CONFIGURATION
# ==========================================

API_KEY_PATH = Path("API Keys/openweather_api_key.txt")

if not API_KEY_PATH.exists():
    raise RuntimeError("OpenWeather API key not found.")

API_KEY = API_KEY_PATH.read_text().strip()


# ==========================================
# 2. WEATHER FETCHER
# ==========================================

def get_weather_report(city: str) -> dict:
    """
    Fetches real-time weather data in Celsius.
    Returns structured weather information.
    """

    if not city:
        return {"error": "MISSING_CITY"}

    url = (
        "http://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={API_KEY}&units=metric"
    )

    try:
        response = requests.get(url, timeout=5)
        data = response.json()

        if response.status_code != 200:
            return {
                "error": "CITY_NOT_FOUND",
                "city": city
            }

        return {
            "city": data["name"],
            "temperature_c": round(data["main"]["temp"]),
            "feels_like_c": round(data["main"]["feels_like"]),
            "humidity": data["main"]["humidity"],
            "description": data["weather"][0]["description"],
            "wind_speed": data["wind"]["speed"]
        }

    except requests.exceptions.RequestException as e:
        return {
            "error": "WEATHER_API_UNAVAILABLE",
            "details": str(e)
        }
