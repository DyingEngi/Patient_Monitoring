import torch
import queue
import pyaudio
import numpy as np
import wave
import time
from transformers import pipeline

# Load Whisper model
whisper = pipeline("automatic-speech-recognition", "openai/whisper-large-v3", 
                   torch_dtype=torch.float16, device="cuda:0")

# Audio settings
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
SILENCE_THRESHOLD = 500  # Adjust based on environment noise
MAX_SILENCE_TIME = 8  # Stop recording after 2 seconds of silence

audio_queue = queue.Queue()
is_listening = False

def audio_callback(in_data, frame_count, time_info, status):
    """Captures audio and stores it in a queue."""
    audio_queue.put(in_data)
    return in_data, pyaudio.paContinue

def transcribe_audio():
    """Records and transcribes audio continuously.
    Stops when silence is detected for MAX_SILENCE_TIME seconds.
    """
    global is_listening
    audio = pyaudio.PyAudio()

    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK,
                        stream_callback=audio_callback)

    print("Recording started... Speak now!")

    frames = []
    silent_time = 0  # Tracks time of silence
    start_time = time.time()

    while is_listening:
        frame = audio_queue.get()
        audio_data = np.frombuffer(frame, dtype=np.int16)
        frames.append(frame)

        # Measure volume level
        volume_level = np.abs(audio_data).mean()

        if volume_level < SILENCE_THRESHOLD:
            silent_time += time.time() - start_time
            if silent_time >= MAX_SILENCE_TIME:
                print("Silence detected. Stopping recording.")
                break
        else:
            silent_time = 0  # Reset silent time when voice is detected

        start_time = time.time()  # Reset the timer

    # Save the recorded audio
    with wave.open("temp.wav", "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Transcribe the saved audio
    transcription = whisper("temp.wav", generate_kwargs={"language": "en"})
    text = transcription["text"].strip()

    print("Transcription:", text)

    # Save to file
    with open("TranscribedText.txt", "w", encoding="utf-8") as f:
        f.write(text)

    stop_listening()

def start_listening():
    """Starts listening for speech."""
    global is_listening
    if not is_listening:
        is_listening = True
        transcribe_audio()

def stop_listening():
    """Stops transcription."""
    global is_listening
    is_listening = False
    print("Listening stopped.")

if __name__ == "__main__":
    start_listening()
