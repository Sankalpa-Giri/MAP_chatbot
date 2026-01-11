def wait_for_wake_word():
    """
    Mock wake word detection for testing.
    """
    print("'Hey Shift' to activate... (Press Enter to simulate)")
    input()  # Wait for user to press Enter
    print("⚡ Wake Word Detected!")
    return True

if __name__ == "__main__":
    while True:
        wait_for_wake_word()
        print("You can now test your chatbot...")
