from pushbullet import Pushbullet
import urllib.parse

# ==========================================
# 1. CONFIGURATION
# ==========================================
# Paste your Access Token from Pushbullet.com
PB_API_KEY = "o.t7RFtFbpRdUMXZctwRStwq6OPMHetnoO"

def get_pb_service():
    try:
        return Pushbullet(PB_API_KEY)
    except:
        return None

def find_my_phone():
    """
    Sends a high-priority notification to the phone to make it ring/vibrate.
    """
    pb = get_pb_service()
    if not pb:
        return "I cannot connect to the phone service."
    
    try:
        # Sends a notification. If phone volume is on, it will chime!
        push = pb.push_note("⚠️ ALERT", "I am here! (Triggered by Assistant)")
        return "I have sent a ping to your phone."
    except Exception as e:
        return f"Failed to ping phone: {e}"

def send_navigation_link(destination):
    """
    Constructs a Google Maps Navigation URL and pushes it to the phone.
    """
    pb = get_pb_service()
    if not pb:
        return False # Silent fail if service is down

    try:
        # 1. Encode the destination (e.g., "Jaydev Vihar" -> "Jaydev+Vihar")
        encoded_dest = urllib.parse.quote(destination)
        
        # 2. Create the Universal Google Maps URL
        # 'api=1' = Use standard version
        # 'dir' = Directions mode
        # 'destination' = Where we are going
        # 'origin' is omitted -> Maps defaults to "Current GPS Location" (Perfect for driving)
        map_url = f"https://www.google.com/maps/dir/?api=1&destination={encoded_dest}&travelmode=driving"

        # 3. Send as a "Link" type push (Phone treats this differently than a Note)
        push = pb.push_link("Navigating to " + destination, map_url)
        return True
        
    except Exception as e:
        print(f"Phone Link Error: {e}")
        return False

# Test
if __name__ == "__main__":
    send_navigation_link("Nexus Esplanade Mall, Rasulgarh")