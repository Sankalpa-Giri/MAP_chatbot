import googlemaps
from datetime import datetime
import pprint

# Read API key from file
with open("API Keys/Gemini_api_key.txt", "r") as f:
    API_KEY = f.read().strip()

# Initialize Google Maps client
gmaps = googlemaps.Client(key=API_KEY)


def fetch_directions(origin: str, destination: str):
    directions_result = gmaps.directions(
        origin=origin,
        destination=destination,
        mode="driving",
        departure_time=datetime.now(),
        alternatives=True
    )
    return directions_result


def main():
    result = fetch_directions(
        origin="KIIT Campus 4",
        destination="Jaydev Vatika"
    )

    pprint.pprint(result)


if __name__ == "__main__":
    main()