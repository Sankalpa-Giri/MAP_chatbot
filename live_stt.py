import queue
import sys
import os
import pyaudio
from google.cloud import speech
from vocabulary import MASTER_PHRASE_HINTS
# Configuration
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"D:\SG Resources\Python speech transcriber\key.json"
SAMPLE_RATE = 16000
CHUNK_SIZE = int(SAMPLE_RATE / 10)

# ==========================================
# 🚀 BOOSTING ACCURACY FOR INDIAN PLACES
# ==========================================
# Add hard-to-recognize local names here.
# Google will now prioritize these words when it hears something similar.
#MASTER_PHRASE_HINTS

class MicrophoneStream:
    """Microphone stream generator (Standard Boilerplate)"""
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
            if chunk is None: return
            data = [chunk]
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None: return
                    data.append(chunk)
                except queue.Empty:
                    break
            yield b"".join(data)

def start_listening(callback_function):
    """
    Starts the microphone loop with Indian English & Phrase Hints.
    """
    print(f"--- Ears Active (Indian Mode | {SAMPLE_RATE} Hz) ---")
    
    client = speech.SpeechClient()
    
    # 1. Prepare the Phrase Hints object
    speech_contexts = [speech.SpeechContext(phrases=MASTER_PHRASE_HINTS)]

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=SAMPLE_RATE,
        
        # CHANGE 1: Indian English
        language_code="en-IN", 
        
        # CHANGE 2: Add the hints
        speech_contexts=speech_contexts,
        
        # CHANGE 3: Use the 'command_and_search' model
        # This model is specifically better for short queries like maps/navigation
        model="command_and_search"
    )
    
    streaming_config = speech.StreamingRecognitionConfig(config=config, interim_results=True)

    with MicrophoneStream(SAMPLE_RATE, CHUNK_SIZE) as stream:
        audio_generator = stream.generator()
        requests = (speech.StreamingRecognizeRequest(audio_content=content) for content in audio_generator)
        
        try:
            responses = client.streaming_recognize(streaming_config, requests)

            for response in responses:
                if not response.results: continue
                result = response.results[0]
                if not result.alternatives: continue

                transcript = result.alternatives[0].transcript

                if result.is_final:
                    callback_function(transcript)
                    if "terminate the program" in transcript.lower():
                        return
                else:
                    sys.stdout.write(f"\rListening: {transcript}...")
                    sys.stdout.flush()

        # --- FIX STARTS HERE ---
        # If main.py says "StopIteration", we just return silently (No error print)
        except StopIteration:
            return 
        # --- FIX ENDS HERE ---

        except Exception as e:
            print(f"\nError during recognition: {e}")