import queue
import sys
import os
from pathlib import Path
import pyaudio
from google.cloud import speech
from vocabulary import MASTER_PHRASE_HINTS

# ==========================================
# CONFIGURATION - Use relative paths
# ==========================================
BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_PATH = BASE_DIR / "API_Keys" / "key.json"

# Set Google Cloud credentials
if CREDENTIALS_PATH.exists():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(CREDENTIALS_PATH)
    print(f"✅ Google credentials loaded from: {CREDENTIALS_PATH}")
else:
    print(f"❌ ERROR: Google credentials not found at: {CREDENTIALS_PATH}")
    print("Please ensure key.json is in the API_Keys folder")

SAMPLE_RATE = 16000
CHUNK_SIZE = int(SAMPLE_RATE / 10)

# ==========================================
# MICROPHONE STREAM
# ==========================================
class MicrophoneStream:
    """Microphone stream generator"""
    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
            stream_callback=self._fill_buffer,
        )
        self.closed = False
        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None: 
                return
            data = [chunk]
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None: 
                        return
                    data.append(chunk)
                except queue.Empty:
                    break
            yield b"".join(data)

# ==========================================
# SPEECH RECOGNITION
# ==========================================
def start_listening(callback_function):
    """
    Starts the microphone loop with Indian English & Phrase Hints.
    """
    # Check if credentials are set
    if not CREDENTIALS_PATH.exists():
        print("❌ Cannot start listening: Google credentials missing!")
        raise FileNotFoundError(f"key.json not found at {CREDENTIALS_PATH}")
    
    print(f"--- 🎤 Microphone Active (Indian Mode | {SAMPLE_RATE} Hz) ---")
    
    try:
        client = speech.SpeechClient()
    except Exception as e:
        print(f"❌ Failed to create Google Speech client: {e}")
        print("Make sure your key.json is valid and has the Speech-to-Text API enabled")
        raise
    
    # Prepare the Phrase Hints
    speech_contexts = [speech.SpeechContext(phrases=MASTER_PHRASE_HINTS)]

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=SAMPLE_RATE,
        language_code="en-IN",  # Indian English
        speech_contexts=speech_contexts,
        model="command_and_search"  # Better for navigation/commands
    )
    
    streaming_config = speech.StreamingRecognitionConfig(
        config=config, 
        interim_results=True
    )

    with MicrophoneStream(SAMPLE_RATE, CHUNK_SIZE) as stream:
        audio_generator = stream.generator()
        requests = (
            speech.StreamingRecognizeRequest(audio_content=content) 
            for content in audio_generator
        )
        
        try:
            responses = client.streaming_recognize(streaming_config, requests)

            for response in responses:
                if not response.results: 
                    continue
                    
                result = response.results[0]
                if not result.alternatives: 
                    continue

                transcript = result.alternatives[0].transcript

                if result.is_final:
                    print(f"\n✅ Recognized: {transcript}")
                    callback_function(transcript)
                    
                    if "terminate the program" in transcript.lower():
                        return
                else:
                    # Show interim results
                    sys.stdout.write(f"\r🎤 Listening: {transcript}...")
                    sys.stdout.flush()

        except StopIteration:
            # Normal exit when command processed
            return 
        except Exception as e:
            print(f"\n❌ Error during recognition: {e}")
            raise

# ==========================================
# TEST
# ==========================================
if __name__ == "__main__":
    print("Testing Google Speech Recognition...")
    print(f"Credentials path: {CREDENTIALS_PATH}")
    print(f"Exists: {CREDENTIALS_PATH.exists()}")
    
    if CREDENTIALS_PATH.exists():
        print("\nSpeak something after the beep...")
        
        def test_callback(text):
            print(f"\nYou said: {text}")
            raise StopIteration
        
        try:
            start_listening(test_callback)
        except Exception as e:
            print(f"Test failed: {e}")