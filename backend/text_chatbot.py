
import sys
import time
from backend import nlu_engine
from backend import chatbot_brain
from backend import driver_rag

# Follow-up mode state
last_interaction_time = 0
FOLLOW_UP_TIMEOUT = 30  # 30-second follow-up window for text

def print_separator():
    """Print a visual separator"""
    print("\n" + "=" * 60)

def handle_user_input(user_text):
    """Process user input - text version"""
    global last_interaction_time
    
    if not user_text or len(user_text.strip()) < 2:
        return
    
    user_text = user_text.strip()
    print(f"\n✅ You: {user_text}")
    
    try:
        # Parse intent
        intent = nlu_engine.parse_intent(user_text)
        print(f"🔍 Intent: {intent.get('intent')}, Dest: {intent.get('destination')}")
        
        # Get response
        reply = chatbot_brain.get_bot_response(intent, user_text)
        
        # Handle stop command
        if reply == "stop_now":
            print("\n🤖 Bot: Goodbye! Drive safe!")
            print_separator()
            sys.exit(0)
        
        # Display response
        print(f"🤖 Bot: {reply}")
        
        # Update timer AFTER successful response
        last_interaction_time = time.time()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("🤖 Bot: Sorry, I had trouble with that.")
    
    print_separator()

def main():
    """Main text-based chatbot loop"""
    global last_interaction_time
    
    print_separator()
    print("🚗 SHIFT TRAFFIC ASSISTANT - Bhubaneswar (Text Mode)")
    print_separator()
    print("💡 Ask about traffic, routes, and directions")
    print("💡 Examples:")
    print("   - 'Traffic to Esplanade'")
    print("   - 'How to go to Nandankanan'")
    print("   - 'Take me to Cuttack'")
    print("   - 'Remember my home is at Patia'")
    print("   - 'Navigate to office'")
    print("💡 Type 'stop' or 'quit' to exit")
    print_separator()
    
    # Welcome message
    print("🤖 Bot: Hello! I'm your traffic assistant. Where would you like to go?")
    print_separator()
    
    while True:
        try:
            # Calculate time since last interaction
            time_since_last = time.time() - last_interaction_time
            in_follow_up = (last_interaction_time > 0 and time_since_last < FOLLOW_UP_TIMEOUT)
            
            if in_follow_up:
                # Follow-up mode indicator
                remaining = int(FOLLOW_UP_TIMEOUT - time_since_last)
                print(f"💬 [Follow-up active - {remaining}s left]")
            else:
                # Reset follow-up timer
                if last_interaction_time > 0:
                    last_interaction_time = 0
            
            # Get user input
            try:
                user_input = input("You: ").strip()
            except EOFError:
                print("\n\n👋 Goodbye!")
                sys.exit(0)
            
            if not user_input:
                continue
            
            # Process input
            handle_user_input(user_input)
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Drive safe!")
            print_separator()
            sys.exit(0)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(0.5)

if __name__ == "__main__":
    main()