#!/usr/bin/env python3
import wave
import numpy as np
import pyaudio
import sys

SPEED = 1.3  # playback speed multiplier

def play_wav_speed(path: str, speed: float = SPEED):
    # 1. Open the WAV and read raw PCM
    wf = wave.open(path, 'rb')
    n_channels = wf.getnchannels()
    sampwidth  = wf.getsampwidth()
    framerate  = wf.getframerate()
    n_frames   = wf.getnframes()
    raw_data   = wf.readframes(n_frames)
    wf.close()

    # 2. Decode to int16 array and reshape for stereo/mono
    pcm = np.frombuffer(raw_data, dtype=np.int16)
    pcm = pcm.reshape(-1, n_channels)  # shape = (n_frames, channels)

    # 3. Time-compress by 'speed' factor (we shorten the signal)
    orig_len = pcm.shape[0]
    new_len  = int(orig_len / speed)
    if new_len < 1:
        print("Audio too short to speed up.")
        return

    # 4. Use linear interpolation to compress each channel
    indices_old = np.arange(orig_len)
    indices_new = np.linspace(0, orig_len, new_len, endpoint=False)
    pcm_fast = np.vstack([
        np.interp(indices_new, indices_old, pcm[:, ch]).astype(np.int16)
        for ch in range(n_channels)
    ]).T  # back to shape (new_len, channels)

    # 5. Initialize PyAudio and open output stream at the WAV's native rate
    p = pyaudio.PyAudio()
    stream = p.open(
        format    = p.get_format_from_width(sampwidth),
        channels  = n_channels,
        rate      = framerate,
        output    = True,
        frames_per_buffer = 1024
    )

    # 6. Play the compressed data
    print(f"Playing {path} at {speed}� speed...")
    stream.write(pcm_fast.tobytes())
    stream.stop_stream()
    stream.close()
    p.terminate()
    print("Done.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python play_wav_speed.py path/to/file.wav")
        sys.exit(1)
    play_wav_speed(sys.argv[1])
