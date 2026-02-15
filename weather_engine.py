import pvporcupine
from pvrecorder import PvRecorder
import os
import time

key_file = os.path.join("API Keys", "pico_access_key.txt")
with open(key_file, "r") as f:
    ACCESS_KEY = f.read().strip()

keyword_path = os.path.join("Pico Voice Agent", "Hey-Shift_en_windows_v3_0_0.ppn")

# Global persistent instances
_porcupine = None
_recorder = None

def initialize():
    """Initialize wake word engine (call once at startup)"""
    global _porcupine, _recorder
    
    try:
        _porcupine = pvporcupine.create(
            access_key=ACCESS_KEY, 
            keyword_paths=[keyword_path], 
            sensitivities=[0.75]  # Slightly lower for better detection
        )
        
        _recorder = PvRecorder(
            device_index=-1, 
            frame_length=_porcupine.frame_length
        )
        
        print("✅ Wake word engine initialized")
        return True
    except Exception as e:
        print(f"❌ Wake word init failed: {e}")
        return False

def wait_for_wake_word():
    """Wait for wake word using persistent resources"""
    global _porcupine, _recorder
    
    # Initialize if not already done
    if not _porcupine or not _recorder:
        if not initialize():
            print("⚠️ Press Enter to simulate wake word")
            input()
            return True
    
    try:
        # Start recording if not already running
        if not _recorder.is_recording:
            _recorder.start()
        
        print("👂 Listening for 'Hey Shift'...")
        
        while True:
            pcm = _recorder.read()
            result = _porcupine.process(pcm)
            
            if result >= 0:
                print("⚡ Wake Word Detected!")
                time.sleep(0.3)  # Small delay to avoid re-triggering
                return True
    
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
        cleanup()
        return False
    except Exception as e:
        print(f"❌ Wake word error: {e}")
        # Don't cleanup - try to recover
        time.sleep(1)
        return wait_for_wake_word()  # Retry

def cleanup():
    """Clean up resources on shutdown"""
    global _porcupine, _recorder
    
    if _recorder:
        try:
            if _recorder.is_recording:
                _recorder.stop()
            _recorder.delete()
        except:
            pass
        _recorder = None
    
    if _porcupine:
        try:
            _porcupine.delete()
        except:
            pass
        _porcupine = None
    
    print("✅ Wake word engine cleaned up")

# Initialize on import
if __name__ != "__main__":
    initialize()
