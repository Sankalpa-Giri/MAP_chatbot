import sys
import live_stt
import nlu_engine
import chatbot_brain
import geocoder
import wake_word_engine
import piper_tts as tts_engine
import time

# ==========================================
# REAL-TIME LOCATION MANAGER
# ==========================================
class LocationManager:
    """Manages current location with smart caching"""
    
    def __init__(self, cache_duration=300):
        """
        Args:
            cache_duration: Seconds before refreshing location (default: 5 minutes)
        """
        self.current_location = None
        self.last_update_time = 0
        self.cache_duration = cache_duration
        
        # Get initial location
        self.refresh_location()
    
    def refresh_location(self, force=False):
        """Update location from GPS/IP"""
        time_since_update = time.time() - self.last_update_time
        
        # Skip if cache is still fresh (unless forced)
        if not force and time_since_update < self.cache_duration:
            return False
        
        # Fetch new location
        try:
            g = geocoder.ip('me')
            
            if g.latlng:
                self.current_location = g.latlng
                self.last_update_time = time.time()
                print(f"📍 Location: {g.latlng} ({g.city})")
                return True
            else:
                print("⚠️ Could not detect location")
                return False
                
        except Exception as e:
            print(f"Location error: {e}")
            return False
    
    def get_location(self):
        """Get current location (auto-refreshes if stale)"""
        self.refresh_location()
        return self.current_location

# Initialize location manager
location_manager = LocationManager(cache_duration=300)

# ==========================================
# COMMAND HANDLER
# ==========================================
def handle_user_input(text_from_speech):
    """Main command processing loop"""
    global location_manager
    
    print(f"\n{'='*50}")
    print(f"User Said: {text_from_speech}")
    print('='*50)
    
    # 1. Check for termination
    if "terminate" in text_from_speech.lower():
        termination_msg = "Shutting down. Goodbye!"
        print(termination_msg)
        tts_engine.speak(termination_msg)
        sys.exit(0)
    
    # 2. Manual location refresh
    if "update location" in text_from_speech.lower() or "refresh location" in text_from_speech.lower():
        success = location_manager.refresh_location(force=True)
        tts_engine.speak("Location updated" if success else "Could not update location")
        raise StopIteration
    
    # 3. Get current location for traffic requests
    current_location = location_manager.get_location()
    
    # 4. Analyze intent
    analysis_result = nlu_engine.nlu_engine_control(
        text_from_speech, 
        current_location=current_location
    )
    
    print(f"DEBUG: Intent: {analysis_result}")
    
    # 5. Get response from brain
    bot_reply = chatbot_brain.get_bot_response(analysis_result, text_from_speech)
    
    print(f"Assistant: {bot_reply}")
    
    # 6. Speak the response
    tts_engine.speak(bot_reply)
    
    print("-" * 50)
    raise StopIteration

# ==========================================
# MAIN LOOP
# ==========================================
def main():
    """Main assistant loop"""
    
    # Startup message
    startup_msg = "Assistant initialized. Say Hey Shift to activate."
    print(startup_msg)
    tts_engine.speak(startup_msg)
    
    while True:
        try:
            # 1. Wait for wake word
            if wake_word_engine.wait_for_wake_word():
                
                # 2. Acknowledge
                tts_engine.speak("Yes?")
                
                # 3. Start listening
                try:
                    live_stt.start_listening(callback_function=handle_user_input)
                except StopIteration:
                    print("--- Command processed. Going back to sleep. ---\n")
                except Exception as e:
                    print(f"Error: {e}")
                    tts_engine.speak("Sorry, I didn't catch that.")
        
        except KeyboardInterrupt:
            print("\nStopping assistant...")
            tts_engine.speak("Goodbye!")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")

# ==========================================
# ENTRY POINT
# ==========================================
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        sys.exit(0)
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopping...")
