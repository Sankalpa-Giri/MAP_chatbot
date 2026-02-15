import sys
import time
import sounddevice as sd
import live_stt
import nlu_engine
import chatbot_brain
import wake_word_engine
import piper_tts as tts_engine

# Follow-up mode state
last_interaction_time = 0
FOLLOW_UP_TIMEOUT = 10  # 10-second follow-up window

def handle_user_input(text_from_speech):
    """
    Process user speech - CRITICAL: Update timer here
    """
    global last_interaction_time
    
    if not text_from_speech or len(text_from_speech.strip()) < 2:
        return
    
    print(f"\n✅ User: {text_from_speech}")
    
    try:
        # Parse intent
        intent = nlu_engine.parse_intent(text_from_speech)
        print(f"🔍 Intent: {intent.get('intent')}, Dest: {intent.get('destination')}")
        
        # Get response
        reply = chatbot_brain.get_bot_response(intent, text_from_speech)
        
        # Handle stop command
        if reply == "stop_now":
            print("🤖 Bot: Goodbye!")
            tts_engine.speak("Goodbye!")
            sd.stop()
            sys.exit(0)
        
        # Speak response
        print(f"🤖 Bot: {reply}")
        tts_engine.speak(reply)
        
        # CRITICAL: Update timer AFTER successful response
        last_interaction_time = time.time()
        print(f"⏱️ Timer reset - 10s follow-up window active")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        try:
            tts_engine.speak("Sorry, I had trouble with that.")
        except:
            pass
    finally:
        sd.stop()

def listen_for_speech():
    """
    Listen for user speech
    """
    sd.stop()
    time.sleep(0.2)
    
    try:
        live_stt.start_listening(callback_function=handle_user_input)
    except StopIteration:
        pass
    except Exception as e:
        if "timeout" not in str(e).lower() and "iterating" not in str(e).lower():
            print(f"⚠️ Speech error: {e}")
        sd.stop()

def main():
    """
    MAIN LOOP: Wake word → Command → 10s follow-up
    """
    global last_interaction_time
    
    print("=" * 60)
    print("🚗 SHIFT TRAFFIC ASSISTANT - Bhubaneswar")
    print("=" * 60)
    print("💡 Say 'Hey Shift' to activate")
    print("💡 Ask follow-ups within 10 seconds (no wake word needed)")
    print("💡 Say 'stop' to exit")
    print("=" * 60)
    
    tts_engine.initialize()
    
    while True:
        try:
            # Calculate time since last interaction
            time_since_last = time.time() - last_interaction_time
            in_follow_up = (last_interaction_time > 0 and time_since_last < FOLLOW_UP_TIMEOUT)
            
            if in_follow_up:
                # FOLLOW-UP MODE
                remaining = int(FOLLOW_UP_TIMEOUT - time_since_last)
                print(f"\n💬 Follow-up active ({remaining}s left) - Speak now!")
                
                listen_for_speech()
                
                # Small delay before next loop iteration
                time.sleep(0.5)
                
            else:
                # WAKE WORD MODE
                if last_interaction_time > 0:
                    print("\n⏰ Follow-up window closed")
                    last_interaction_time = 0
                
                print("\n👂 Waiting for 'Hey Shift'...")
                
                if wake_word_engine.wait_for_wake_word():
                    print("✅ Wake word detected!")
                    
                    # Acknowledge
                    tts_engine.speak("Yes")
                    time.sleep(0.3)
                    
                    # Listen for command
                    listen_for_speech()
                    
                    # Small delay
                    time.sleep(0.5)
        
        except KeyboardInterrupt:
            print("\n\n👋 Shutting down...")
            sd.stop()
            sys.exit(0)
            
        except Exception as e:
            print(f"❌ Main loop error: {e}")
            sd.stop()
            time.sleep(1)

if __name__ == "__main__":
    main()