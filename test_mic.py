import sounddevice as sd
import numpy as np

print("Testing microphone...")
print("\nAvailable audio devices:")
print(sd.query_devices())

try:
    print("\nRecording 2 seconds...")
    audio = sd.rec(int(2 * 16000), samplerate=16000, channels=1, dtype='int16')
    sd.wait()
    print("✅ Microphone works!")
except Exception as e:
    print(f"❌ Microphone failed: {e}")