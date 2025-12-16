import sys
import live_stt       # Ears
import nlu_engine     # Logic
import chatbot_brain  # Brain
#import tts_engine     # Mouth
import geocoder
import wake_word_engine
import piper_tts as tts_engine
g = geocoder.ip('me')
current_loc = g.latlng
def handle_user_input(text_from_speech):
    """
    Main Loop: Listen -> Think -> Speak
    """
    print(f"\nUser Said: {text_from_speech}")

    # 1. Check for Termination
    if "terminate" in text_from_speech.lower():
        termination_msg = "Shutting down. Goodbye!"
        print(f"{termination_msg}")
        tts_engine.speak(termination_msg) # Speak before dying
        sys.exit(0)

    # 2. Analyze Intent
    analysis_result = nlu_engine.nlu_engine_control(text_from_speech)
    
    # 3. Get Response from Brain
    bot_reply = chatbot_brain.get_bot_response(analysis_result, text_from_speech)
    
    # --- 🔊 THE NEW PART ---
    tts_engine.speak(bot_reply)
    # -----------------------

    print("-" * 40)
    raise StopIteration

def main():
    tts_engine.speak("Assistant Initialised. Hey Shift to activate.")
    
    while True:
        # 1. WAIT FOR WAKE WORD (Offline & Private)
        # The code blocks here until you say "Jarvis"
        if wake_word_engine.wait_for_wake_word():
            
            # 2. WAKE UP SOUND
            tts_engine.speak("Yes?")
            
            # 3. START ACTIVE LISTENING (Google Cloud)
            try:
                # We start the Google stream. It runs until 'StopIteration' is raised above.
                live_stt.start_listening(callback_function=handle_user_input)
            except StopIteration:
                print("--- Command processed. Going back to sleep. ---")
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopping...")