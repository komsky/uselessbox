import pyaudio
import wave
import numpy as np
import time

# Audio configuration
FORMAT = pyaudio.paInt16
CHANNELS = 2  # ReSpeaker has 2 mics
RATE = 16000  # Standard for voice
RECORD_SECONDS = 5
DEVICE_INDEX = 1  # Your ReSpeaker device index
OUTPUT_FILENAME = "test_recording.wav"

def list_audio_devices():
    p = pyaudio.PyAudio()
    print("\nAvailable audio devices:")
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        print(f"{i}: {dev['name']} (Input channels: {dev['maxInputChannels']})")
    p.terminate()

def test_recording():
    p = pyaudio.PyAudio()
    
    # Print selected device info
    dev_info = p.get_device_info_by_index(DEVICE_INDEX)
    print(f"\nUsing device: {dev_info['name']}")
    print(f"Input channels: {dev_info['maxInputChannels']}")
    print(f"Sample rate: {RATE} Hz")
    
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        input_device_index=DEVICE_INDEX,
        frames_per_buffer=1024
    )
    
    print("\nRecording for 5 seconds... Speak into the microphones!")
    frames = []
    for _ in range(0, int(RATE / 1024 * RECORD_SECONDS)):
        data = stream.read(1024, exception_on_overflow=False)
        frames.append(data)
    
    print("Recording complete")
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # Save recording
    with wave.open(OUTPUT_FILENAME, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
    print(f"Saved recording to {OUTPUT_FILENAME}")

if __name__ == "__main__":
    list_audio_devices()
    test_recording()
    print("\nPlay the recording with:")
    print(f"aplay -D plughw:{DEVICE_INDEX} {OUTPUT_FILENAME}")