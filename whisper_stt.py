from faster_whisper import WhisperModel
import os
import sys

# ==========================================
# 🔧 WINDOWS GPU FIX
# ==========================================
# This forces Python to find the cuDNN DLLs we just installed
try:
    import nvidia.cudnn
    import nvidia.cublas
    # Add the library directories to the DLL search path
    cudnn_dir = os.path.dirname(nvidia.cudnn.__file__)
    cublas_dir = os.path.dirname(nvidia.cublas.__file__)
    
    os.add_dll_directory(os.path.join(cudnn_dir, "bin"))
    os.add_dll_directory(os.path.join(cublas_dir, "bin"))
    
    print("✅ NVIDIA Libraries Linked Successfully")
except ImportError:
    print("⚠️ Warning: nvidia-cudnn-cu12 not found. GPU mode might fail.")
except Exception as e:
    print(f"⚠️ DLL Link Error: {e}")

# ==========================================
# CONFIGURATION
# ==========================================
MODEL_SIZE = "small.en"
DEVICE = "cuda"
COMPUTE_TYPE = "float16"

_model = None

def load_model():
    global _model
    if _model is None:
        print(f"⏳ Loading Whisper STT Model ({MODEL_SIZE})...")
        try:
            # It will now find the DLLs in the current folder automatically
            _model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
            print("✅ Whisper System Online (GPU Mode)")
        except Exception as e:
            print(f"❌ GPU Error: {e}")
            print("🔄 Falling back to CPU...")
            _model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
            print("✅ Whisper System Online (CPU Mode)")
    
    return _model

def transcribe(audio_file_path):
    model = load_model()
    if not os.path.exists(audio_file_path):
        return ""
    try:
        segments, info = model.transcribe(audio_file_path, beam_size=5)
        return " ".join([segment.text for segment in segments]).strip()
    except Exception as e:
        print(f"Transcription Error: {e}")
        return ""

if __name__ == "__main__":
    print("Transcribed sentence: ")
    load_model()
    transcribe(r"Audio\harvard.wav")