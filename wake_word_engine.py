import pvporcupine
from pvrecorder import PvRecorder
import os
#5 sec cooldown is added automatically. You cannot fire rapid wake words

# Paste your Picovoice AccessKey here
key = open(r"API Keys\pico_access_key.txt","r")
ACCESS_KEY = key.read().strip()

keyword_path = os.path.join(
    "Pico Voice Agent",
    "Hey-Shift_en_windows_v3_0_0.ppn"
)


def wait_for_wake_word():
    """
    Listens passively for the wake word
    Returns True when detected.
    """
    print("'Hey Shift' to activate...")
    
    # Initialize Porcupine with a built-in keyword
    porcupine = pvporcupine.create(access_key=ACCESS_KEY, 
                                   keyword_paths=[keyword_path], 
                                   sensitivities=[0.85])

    recorder = PvRecorder(device_index=0, frame_length=porcupine.frame_length)

    try:
        recorder.start()

        while True:
            # Read a chunk of audio
            pcm = recorder.read()
            
            # Ask Porcupine: "Did you hear the word?"
            result_index = porcupine.process(pcm)
            
            if result_index >= 0:
                print("⚡ Wake Word Detected!")
                return True # Break the loop and return control

    except KeyboardInterrupt:
        recorder.stop()
    finally:
        # Clean up resources
        porcupine.delete()
        recorder.delete()

if __name__ == "__main__":
    while True:
        wait_for_wake_word()


