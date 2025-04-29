import pyaudio
import time

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2  # Must be 2 for WM8960
RATE = 16000  # Or 44100 if 16kHz doesn't work
DEVICE_INDEX = 1  # Your hw:1 device

p = pyaudio.PyAudio()

# Print device info for debugging
dev_info = p.get_device_info_by_index(DEVICE_INDEX)
print(f"Using device: {dev_info['name']}")
print(f"Max input channels: {dev_info['maxInputChannels']}")

# Special stream configuration for WM8960
stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    input_device_index=DEVICE_INDEX,
    frames_per_buffer=CHUNK,
    input_host_api_specific_stream_info=None,  # Important!
    start=False  # We'll start manually
)

stream.start_stream()
print("Recording... (Ctrl+C to stop)")

try:
    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        # Process your audio here
        time.sleep(0.1)
except KeyboardInterrupt:
    stream.stop_stream()
    stream.close()
    p.terminate()
    print("Stopped recording")