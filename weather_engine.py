import requests
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Path to OpenWeather API key
API_KEYS_DIR = BASE_DIR / "API_Keys"
API_KEYS_DIR.mkdir(exist_ok=True)

OPENWEATHER_KEY_FILE = API_KEYS_DIR / "openweather_api_key.txt"
if not OPENWEATHER_KEY_FILE.exists():
    with open(OPENWEATHER_KEY_FILE, "w") as f:
        f.write("FAKE_OPENWEATHER_KEY")
    print(f"⚠️ OpenWeather API key missing. Created fake key at {OPENWEATHER_KEY_FILE}")

with open(OPENWEATHER_KEY_FILE, "r") as f:
    OPENWEATHER_API_KEY = f.read().strip()

if not OPENWEATHER_API_KEY:
    OPENWEATHER_API_KEY = "FAKE_OPENWEATHER_KEY"

def get_weather_report(city_name):
    """
    Fetches real-time weather (Celsius) and returns a spoken string.
    """
    if not city_name:
        return "I need to know the city name to check the weather."

    url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={OPENWEATHER_API_KEY}&units=metric"

    try:
        response = requests.get(url)
        data = response.json()

        if response.status_code == 200:
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            description = data["weather"][0]["description"]
            location = data["name"]

            return (f"The current temperature in {location} is {round(temp)}°C, "
                    f"but it feels like {round(feels_like)}°C. "
                    f"Conditions are {description}.")
        else:
            return f"I couldn't find weather data for {city_name}."
    except Exception as e:
        print(f"Weather API Error: {e}")
        return "I am having trouble connecting to the weather service."

# Test
if __name__ == "__main__":
    print(get_weather_report("Bhubaneswar"))
