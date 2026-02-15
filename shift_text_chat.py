"""
SHIFT Traffic Assistant - Text-Based Version
Lightweight chatbot without voice dependencies

Required modules:
- nlu_engine.py
- chatbot_brain.py 
- driver_rag.py
- maps_engine.py
"""

import sys
import time

# Import your existing modules
try:
    import nlu_engine
    import chatbot_brain
    import driver_rag
except ImportError as e:
    print(f"❌ Missing module: {e}")
    print("Make sure nlu_engine.py, chatbot_brain.py, driver_rag.py, and maps_engine.py are in the same directory")
    sys.exit(1)

# Session state
session = {
    "last_interaction": 0,
    "conversation_active": False
}

FOLLOW_UP_WINDOW = 30  # seconds

def display_header():
    """Show welcome banner"""
    print("\n" + "=" * 70)
    print("🚗 SHIFT - Your Traffic Assistant for Bhubaneswar")
    print("=" * 70)
    print("\n📍 What I can help with:")
    print("   • Traffic updates and route information")
    print("   • Turn-by-turn directions")
    print("   • Save favorite locations (home, office, gym)")
    print("   • Quick traffic checks")
    print("\n💡 Example commands:")
    print("   'Traffic to Esplanade'")
    print("   'How do I get to Nandankanan?'")
    print("   'Navigate to Master Canteen'")
    print("   'Remember my home is at Patia'")
    print("   'Take me to office' (if you've saved it)")
    print("   'Forget home'")
    print("\n⌨️  Type 'quit', 'exit', or 'stop' to leave")
    print("=" * 70 + "\n")

def format_bot_response(text):
    """Format bot responses nicely"""
    return f"🤖 Shift: {text}"

def format_user_input(text):
    """Format user input"""
    return f"👤 You: {text}"

def check_follow_up_status():
    """Check if we're in follow-up window"""
    elapsed = time.time() - session["last_interaction"]
    
    if session["conversation_active"] and elapsed < FOLLOW_UP_WINDOW:
        remaining = int(FOLLOW_UP_WINDOW - elapsed)
        return True, remaining
    else:
        if session["conversation_active"]:
            session["conversation_active"] = False
        return False, 0

def process_message(user_text):
    """Process user message and get response"""
    try:
        # Parse intent using your existing NLU
        intent = nlu_engine.parse_intent(user_text)
        
        # Debug info
        print(f"   [Intent: {intent.get('intent')}]", end="")
        if intent.get('destination'):
            print(f" [Destination: {intent.get('destination')}]")
        else:
            print()
        
        # Get bot response using your existing chatbot brain
        response = chatbot_brain.get_bot_response(intent, user_text)
        
        # Handle stop command
        if response == "stop_now":
            return None
        
        # Update session
        session["last_interaction"] = time.time()
        session["conversation_active"] = True
        
        return response
        
    except Exception as e:
        print(f"\n❌ Error processing message: {e}")
        return "Sorry, I encountered an error. Please try again."

def main():
    """Main chat loop"""
    display_header()
    
    # Initial greeting
    print(format_bot_response("Hi! I'm Shift, your traffic assistant. Where would you like to go?"))
    print()
    
    while True:
        try:
            # Check follow-up status
            in_follow_up, remaining = check_follow_up_status()
            
            # Show status indicator
            if in_follow_up:
                status = f"💬 Follow-up mode ({remaining}s)"
            else:
                status = "🟢 Ready"
            
            # Get user input
            try:
                user_input = input(f"{status} > ").strip()
            except EOFError:
                print("\n\n👋 Goodbye! Drive safe!")
                break
            
            # Skip empty input
            if not user_input:
                continue
            
            # Display formatted user input
            print(format_user_input(user_input))
            
            # Process and get response
            response = process_message(user_input)
            
            # Handle exit
            if response is None:
                print("\n" + format_bot_response("Goodbye! Drive safe!"))
                print("\n" + "=" * 70 + "\n")
                break
            
            # Display response
            print(format_bot_response(response))
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            print("=" * 70 + "\n")
            break
            
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            print("Continuing...\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
