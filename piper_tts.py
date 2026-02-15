import sounddevice as sd
import numpy as np
from pathlib import Path
import warnings
import sys

warnings.filterwarnings("ignore")
if not sys.warnoptions:
    warnings.simplefilter("ignore")

try:
    from piper.voice import PiperVoice
    PIPER_AVAILABLE = True
except ImportError:
    PIPER_AVAILABLE = False

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "Voices" / "en_US-amy-medium.onnx"
CONFIG_PATH = BASE_DIR / "Voices" / "en_US-amy-medium.onnx.json"

_voice = None

def load_piper_model():
    global _voice
    if _voice:
        return _voice
    if not PIPER_AVAILABLE or not MODEL_PATH.exists():
        return None
    try:
        _voice = PiperVoice.load(str(MODEL_PATH), config_path=str(CONFIG_PATH))
        print("✅ Piper Loaded Successfully")
    except Exception as e:
        print(f"❌ Load failed: {e}")
    return _voice

def speak(text: str):
    if not _voice:
        load_piper_model()
    
    print(f"🔊 Speaking: '{text}'")
    
    if not _voice:
        return
    
    try:
        chunks = list(_voice.synthesize(text))
        if not chunks:
            return
        
        # Correct way to handle AudioChunk
        audio_float = np.concatenate([c.audio_float_array for c in chunks])
        audio_int16 = (audio_float * 32767).astype(np.int16)
        sample_rate = chunks[0].sample_rate
        
        sd.play(audio_int16, samplerate=sample_rate, blocking=True)
        
    except Exception as e:
        print(f"❌ TTS Error: {e}")

def initialize():
    return load_piper_model() is not None