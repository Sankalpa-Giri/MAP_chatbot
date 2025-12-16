import requests

# 1. CONFIGURATION
api = open(r"API Keys\openweather_api_key.txt","r")
API_KEY = api.read()

def get_weather_report(city_name):
    """
    Fetches real-time weather (Celsius) and returns a spoken string.
    """
    if not city_name:
        return "I need to know the city name to check the weather."

    # We use units='metric' to get Celsius
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={API_KEY}&units=metric"

    try:
        response = requests.get(url)
        data = response.json()

        if response.status_code == 200:
            # 2. EXTRACT SPECIFIC FIELDS (Celsius & Feels Like)
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            description = data["weather"][0]["description"]
            location = data["name"]

            # 3. FORMULATE RESPONSE
            # Rounding numbers makes it sound more natural (e.g., "32 degrees" instead of "32.05")
            return (f"The current temperature in {location} is {round(temp)} degrees Celsius, "
                    f"but it feels like {round(feels_like)}. "
                    f"Conditions are {description}.")
        else:
            return f"I couldn't find weather data for {city_name}."

    except Exception as e:
        print(f"Weather API Error: {e}")
        return "I am having trouble connecting to the weather satellite."

# Test
if __name__ == "__main__":
    print(get_weather_report("Bhubaneswar"))