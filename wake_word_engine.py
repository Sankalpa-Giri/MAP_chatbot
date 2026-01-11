import platform
from pathlib import Path

# Try to import Picovoice
try:
    import pvporcupine
    from pvrecorder import PvRecorder
    PICOVOICE_AVAILABLE = True
except ImportError:
    PICOVOICE_AVAILABLE = False
    print("⚠️ Picovoice not installed. Using mock wake word mode.")

# ==========================================
# CONFIGURATION - Use relative paths
# ==========================================
BASE_DIR = Path(__file__).resolve().parent

# Access Key
key_path = BASE_DIR / "API_Keys" / "pico_access_key.txt"
if key_path.exists():
    with open(key_path, "r") as f:
        ACCESS_KEY = f.read().strip()
    print(f"✅ Pico access key loaded")
else:
    ACCESS_KEY = "FAKE_ACCESS_KEY"
    print(f"⚠️ Pico access key not found at: {key_path}")

# Keyword file paths
keyword_file_linux = BASE_DIR / "Pico Voice Agent" / "Hey-Shift_en_linux_v3_0_0.ppn"
keyword_file_windows = BASE_DIR / "Pico Voice Agent" / "Hey-Shift_en_windows_v3_0_0.ppn"

# Detect platform
SYSTEM = platform.system().lower()
if SYSTEM == "windows":
    keyword_path = keyword_file_windows
else:
    keyword_path = keyword_file_linux

print(f"📍 Platform: {SYSTEM}")
print(f"📍 Wake word file: {keyword_path}")
print(f"📍 File exists: {keyword_path.exists()}")

# Decide if we should use mock mode
USE_MOCK_WAKE_WORD = not PICOVOICE_AVAILABLE or not keyword_path.exists() or ACCESS_KEY == "FAKE_ACCESS_KEY"

if USE_MOCK_WAKE_WORD:
    print("⚠️ Using MOCK wake word mode (Press Enter to activate)")
    if not PICOVOICE_AVAILABLE:
        print("   Reason: Picovoice not installed")
    if not keyword_path.exists():
        print(f"   Reason: Wake word file not found")
    if ACCESS_KEY == "FAKE_ACCESS_KEY":
        print(f"   Reason: Access key not found")

# ==========================================
# WAKE WORD DETECTION
# ==========================================
def wait_for_wake_word():
    """
    Waits for the wake word to activate the assistant.
    Returns True when detected.
    """
    global USE_MOCK_WAKE_WORD

    # Mock mode - for testing without hardware
    if USE_MOCK_WAKE_WORD:
        print("'Hey Shift' to activate... (Press Enter to simulate)")
        input()
        print("⚡ Wake Word Detected! (Mock)")
        return True

    # Real Picovoice wake word detection
    print("'Hey Shift' to activate...")
    
    porcupine = None
    recorder = None

    try:
        # Create Porcupine instance
        porcupine = pvporcupine.create(
            access_key=ACCESS_KEY,
            keyword_paths=[str(keyword_path)],
            sensitivities=[0.80]  # Adjust sensitivity (0.0 to 1.0)
        )

        # Create audio recorder
        recorder = PvRecorder(
            device_index=-1,  # Default microphone
            frame_length=porcupine.frame_length
        )
        
        recorder.start()
        print("✅ Wake word detection active")

        # Listen loop
        while True:
            pcm = recorder.read()
            result_index = porcupine.process(pcm)
            
            if result_index >= 0:
                print("⚡ Wake Word Detected!")
                return True

    except KeyboardInterrupt:
        print("\n🛑 Wake word detection stopped")
        if recorder:
            recorder.stop()
        return False
        
    except Exception as e:
        print(f"❌ Wake word error: {e}")
        print("🔄 Switching to mock mode...")
        USE_MOCK_WAKE_WORD = True
        
        # Clean up before switching to mock
        if recorder:
            try:
                recorder.stop()
                recorder.delete()
            except:
                pass
        if porcupine:
            try:
                porcupine.delete()
            except:
                pass
        
        # Retry in mock mode
        return wait_for_wake_word()
        
    finally:
        # Always clean up resources
        if recorder:
            try:
                recorder.stop()
                recorder.delete()
            except:
                pass
        if porcupine:
            try:
                porcupine.delete()
            except:
                pass

# ==========================================
# TEST
# ==========================================
if __name__ == "__main__":
    print("\n" + "="*50)
    print("WAKE WORD ENGINE TEST")
    print("="*50)
    print(f"Mode: {'MOCK' if USE_MOCK_WAKE_WORD else 'REAL'}")
    print("="*50 + "\n")
    
    while True:
        if wait_for_wake_word():
            print("✅ Wake word detected successfully!")
            print("Press Ctrl+C to exit, or Enter to test again...")
            try:
                input()
            except KeyboardInterrupt:
                print("\n👋 Exiting...")
                break
        else:
            break