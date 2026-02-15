import pvporcupine
import sounddevice as sd
import os

key_file = os.path.join("API Keys", "pico_access_key.txt")
with open(key_file, "r") as f:
    ACCESS_KEY = f.read().strip()

keyword_path = os.path.join("Pico Voice Agent", "Hey-Shift_en_windows_v3_0_0.ppn")

_porcupine = None
_using_custom_keyword = False

def initialize_wake_word():
    """Initialize Porcupine with fallback to built-in keyword"""
    global _porcupine, _using_custom_keyword
    
    if _porcupine:
        return True
    
    # Try custom keyword first
    try:
        if os.path.exists(keyword_path):
            _porcupine = pvporcupine.create(
                access_key=ACCESS_KEY, 
                keyword_paths=[keyword_path], 
                sensitivities=[0.7]
            )
            _using_custom_keyword = True
            print("✅ Wake word initialized (Hey Shift)")
            return True
    except Exception as e:
        print(f"⚠️ Custom keyword failed: {e}")
    
    # Fallback to built-in keyword
    try:
        _porcupine = pvporcupine.create(
            access_key=ACCESS_KEY, 
            keywords=["jarvis"],  # Built-in keyword
            sensitivities=[0.5]
        )
        _using_custom_keyword = False
        print("✅ Wake word initialized (say 'Jarvis')")
        return True
    except Exception as e:
        print(f"❌ Wake word init failed: {e}")
        return False


def wait_for_wake_word():
    """Wait for wake word using sounddevice"""
    global _porcupine
    
    if not _porcupine:
        if not initialize_wake_word():
            return None
    
    try:
        sample_rate = 16000
        frame_length = _porcupine.frame_length
        
        with sd.InputStream(
            samplerate=sample_rate,
            channels=1,
            dtype='int16',
            blocksize=frame_length
        ) as stream:
            
            while True:
                audio_frame, overflowed = stream.read(frame_length)
                
                if overflowed:
                    continue
                
                pcm = audio_frame.flatten()
                keyword_index = _porcupine.process(pcm)
                
                if keyword_index >= 0:
                    return True
                    
    except KeyboardInterrupt:
        return False
    except Exception as e:
        print(f"❌ Wake word error: {e}")
        return None


def cleanup_wake_word():
    """Cleanup Porcupine resources"""
    global _porcupine
    if _porcupine:
        _porcupine.delete()
        _porcupine = None