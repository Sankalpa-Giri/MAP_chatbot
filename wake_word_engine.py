import sys
import platform
from pathlib import Path

# Check if Picovoice libraries are available
try:
    import pvporcupine
    from pvrecorder import PvRecorder
    PICOVOICE_AVAILABLE = True
except ImportError:
    PICOVOICE_AVAILABLE = False

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# AccessKey
key_path = BASE_DIR / "API_Keys" / "pico_access_key.txt"
if key_path.exists():
    with open(key_path, "r") as f:
        ACCESS_KEY = f.read().strip()
else:
    ACCESS_KEY = "FAKE_ACCESS_KEY"
    print(f"⚠️ Pico Access Key file missing. Using fake key.")

# Keyword file path
keyword_file_linux = BASE_DIR / "Pico Voice Agent" / "Hey-Shift_en_linux_v3_0_0.ppn"
keyword_file_windows = BASE_DIR / "Pico Voice Agent" / "Hey-Shift_en_windows_v3_0_0.ppn"

# Detect platform
SYSTEM = platform.system().lower()
if SYSTEM == "windows":
    keyword_path = keyword_file_windows
else:
    keyword_path = keyword_file_linux

# Fallback: use mock if Picovoice not available or file missing
USE_MOCK_WAKE_WORD = not PICOVOICE_AVAILABLE or not keyword_path.exists()


def wait_for_wake_word():
    """
    Waits for the wake word to activate the assistant.
    Returns True when detected.
    """
    global USE_MOCK_WAKE_WORD  # <-- moved to top of function

    if USE_MOCK_WAKE_WORD:
        # Mock wake word for testing
        print("'Hey Shift' to activate... (Press Enter to simulate)")
        input()
        print("⚡ Wake Word Detected! (Mock)")
        return True

    # Real Picovoice wake word
    print("'Hey Shift' to activate...")

    try:
        porcupine = pvporcupine.create(
            access_key=ACCESS_KEY,
            keyword_paths=[str(keyword_path)],
            sensitivities=[0.80]
        )

        recorder = PvRecorder(device_index=0, frame_length=porcupine.frame_length)
        recorder.start()

        while True:
            pcm = recorder.read()
            result_index = porcupine.process(pcm)
            if result_index >= 0:
                print("⚡ Wake Word Detected!")
                return True

    except KeyboardInterrupt:
        recorder.stop()
    except Exception as e:
        print(f"Wake word error: {e}\nSwitching to mock mode.")
        USE_MOCK_WAKE_WORD = True
        return wait_for_wake_word()
    finally:
        if 'porcupine' in locals():
            porcupine.delete()
        if 'recorder' in locals():
            recorder.delete()


if __name__ == "__main__":
    while True:
        wait_for_wake_word()
