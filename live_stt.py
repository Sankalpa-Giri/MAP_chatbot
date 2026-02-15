import sys
import os
from pathlib import Path
import pyaudio
from google.cloud import speech
from vocabulary import MASTER_PHRASE_HINTS
import time
import audioop

BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_PATH = BASE_DIR / "API Keys" / "key.json"

if CREDENTIALS_PATH.exists():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(CREDENTIALS_PATH)

SAMPLE_RATE = 16000
CHUNK_SIZE = int(SAMPLE_RATE / 10)
TIMEOUT_SECONDS = 10

class MicrophoneStream:
    def __init__(self, rate, chunk, timeout=TIMEOUT_SECONDS):
        self._rate = rate
        self._chunk = chunk
        self.closed = True
        self._audio_interface = None
        self._audio_stream = None
        self.timeout = timeout
        self.last_audio_time = None

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
            stream_callback=None,
        )
        self.closed = False
        self.last_audio_time = time.time()
        return self

    def __exit__(self, type, value, traceback):
        if self._audio_stream:
            self._audio_stream.stop_stream()
            self._audio_stream.close()
        if self._audio_interface:
            self._audio_interface.terminate()
        self.closed = True

    def generator(self):
        while not self.closed:
            try:
                if self.last_audio_time and (time.time() - self.last_audio_time) > self.timeout:
                    self.closed = True
                    break
                
                data = self._audio_stream.read(self._chunk, exception_on_overflow=False)
                
                rms = audioop.rms(data, 2)
                if rms > 100:
                    self.last_audio_time = time.time()
                
                yield data
                
            except Exception as e:
                break

def start_listening(callback_function):
    print(f"🎤 Listening...")
    
    if not CREDENTIALS_PATH.exists():
        raise StopIteration
    
    try:
        client = speech.SpeechClient()
        
        speech_contexts = [speech.SpeechContext(phrases=MASTER_PHRASE_HINTS)]

        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=SAMPLE_RATE,
            language_code="en-IN",
            speech_contexts=speech_contexts,
            model="command_and_search"
        )
        
        streaming_config = speech.StreamingRecognitionConfig(
            config=config, 
            interim_results=True
        )

        with MicrophoneStream(SAMPLE_RATE, CHUNK_SIZE, timeout=TIMEOUT_SECONDS) as stream:
            audio_generator = stream.generator()
            
            def request_generator():
                for content in audio_generator:
                    if stream.closed:
                        break
                    yield speech.StreamingRecognizeRequest(audio_content=content)
            
            requests = request_generator()
            responses = client.streaming_recognize(streaming_config, requests)

            got_speech = False
            
            for response in responses:
                if not response.results: 
                    continue
                    
                result = response.results[0]
                if not result.alternatives: 
                    continue

                transcript = result.alternatives[0].transcript
                got_speech = True

                if result.is_final:
                    print(f"✅ Recognized: {transcript}")
                    callback_function(transcript)
                    stream.closed = True
                    raise StopIteration
                else:
                    sys.stdout.write(f"\r🎤 {transcript}...")
                    sys.stdout.flush()
            
            if not got_speech:
                print("\n⏰ Timeout - no speech")

    except StopIteration:
        return 

    except Exception as e:
        if "iterating requests" not in str(e) and "Audio Timeout" not in str(e):
            print(f"\n❌ Error: {e}")
        raise StopIteration