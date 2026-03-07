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
# 2. WEATHER CONDITION ANALYZER
# ==========================================

def analyze_weather_conditions(temp, description):
    """
    Adds useful weather condition flags for reasoning
    """
    description = description.lower()

    return {
        "is_hot": temp >= 32,
        "is_cold": temp <= 15,
        "is_rainy": "rain" in description or "drizzle" in description,
        "is_cloudy": "cloud" in description,
        "is_clear": "clear" in description
    }


# ==========================================
# 3. WEATHER BY CITY
# ==========================================

def get_weather_report(city: str) -> dict:
    """
    Fetches real-time weather data using city name.
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

        temp = round(data["main"]["temp"])
        description = data["weather"][0]["description"]

        conditions = analyze_weather_conditions(temp, description)

        return {
            "city": data["name"],
            "temperature_c": temp,
            "feels_like_c": round(data["main"]["feels_like"]),
            "humidity": data["main"]["humidity"],
            "description": description,
            "wind_speed": data["wind"]["speed"],
            **conditions
        }

    except requests.exceptions.RequestException as e:
        return {
            "error": "WEATHER_API_UNAVAILABLE",
            "details": str(e)
        }


# ==========================================
# 4. WEATHER BY LATITUDE & LONGITUDE
# ==========================================

def get_weather_by_coordinates(lat: float, lon: float) -> dict:
    """
    Fetch weather using latitude and longitude.
    """

    if lat is None or lon is None:
        return {"error": "MISSING_COORDINATES"}

    url = (
        "http://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    )

    try:
        response = requests.get(url, timeout=5)
        data = response.json()

        if response.status_code != 200:
            return {
                "error": "LOCATION_NOT_FOUND",
                "lat": lat,
                "lon": lon
            }

        temp = round(data["main"]["temp"])
        description = data["weather"][0]["description"]

        conditions = analyze_weather_conditions(temp, description)

        return {
            "city": data.get("name", "Unknown"),
            "latitude": lat,
            "longitude": lon,
            "temperature_c": temp,
            "feels_like_c": round(data["main"]["feels_like"]),
            "humidity": data["main"]["humidity"],
            "description": description,
            "wind_speed": data["wind"]["speed"],
            **conditions
        }

    except requests.exceptions.RequestException as e:
        return {
            "error": "WEATHER_API_UNAVAILABLE",
            "details": str(e)
        }


# ==========================================
# 5. TEST
# ==========================================

import pprint

if __name__ == "__main__":

    print("City Weather")
    result = get_weather_report("Angul")
    pprint.pprint(result)

    print("\nCoordinate Weather")
    result = get_weather_by_coordinates(20.353708, 85.819925)
    pprint.pprint(result)