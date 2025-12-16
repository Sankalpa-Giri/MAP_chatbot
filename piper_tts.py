import sounddevice as sd
import soundfile as sf
import io
import os
from piper.voice import PiperVoice
import pyaudio
import numpy as np
# ==========================================
# CONFIGURATION
# ==========================================
# Update these paths if necessary
MODEL_PATH = r"Voices\en_US-amy-medium.onnx"
CONFIG_PATH = r"Voices\en_US-amy-medium.onnx.json"

_voice = None

def load_piper_model():
    """Lazy loads the model."""
    global _voice
    if _voice is None:
        if not os.path.exists(MODEL_PATH) or not os.path.exists(CONFIG_PATH):
            print("❌ Piper Error: Model or Config file not found!")
            return None
        
        #print("⏳ Loading Piper Model...")
        try:
            # We try to use GPU (use_cuda=True). If you haven't installed onnxruntime-gpu, 
            # it might fallback or warn, but it should still load.
            _voice = PiperVoice.load(MODEL_PATH, config_path=CONFIG_PATH)
            print("✅ Piper Loaded Successfully")
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            
    return _voice

def speak(text):
    """
    Synthesizes speech to an numpy array and plays it.
    """
    voice = load_piper_model()
    if not voice:
        return
    
    try:
        chunks = list(voice.synthesize(text))
        if not chunks:
            print("❌ No audio generated")
            return

        # Concatenate float arrays
        audio_float = np.concatenate([chunk.audio_float_array for chunk in chunks])

        # Normalize
        audio_float = audio_float / np.max(np.abs(audio_float))

        # Convert to int16 PCM
        audio_int16 = (audio_float * 32767).astype(np.int16)

        # Correct sample rate
        sample_rate = chunks[0].sample_rate

        # Add silence padding (start + end)
        pad = np.zeros(int(0.3 * sample_rate), dtype=np.int16)  # 300 ms
        audio_int16 = np.concatenate([pad, audio_int16, pad])

        # Play audio
        print(f"Assistant is speaking: '{text}'")
        sd.play(audio_int16, samplerate=sample_rate)
        sd.wait()


    except Exception as e:
        print(f"Piper Speech Error: {e}")


# Test
if __name__ == "__main__":
    speak("the sky")