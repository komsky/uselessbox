#!/usr/bin/env python3
import wave
import numpy as np
import pyaudio
import glob
import random
import threading

SPEED = 1.3  # playback speed multiplier

def play_wav_speed(path: str, speed: float = SPEED):
    """Blocking: load a WAV, time-compress it by SPEED, and play at native rate."""
    # 1. Read WAV
    wf = wave.open(path, 'rb')
    n_channels = wf.getnchannels()
    sampwidth  = wf.getsampwidth()
    framerate  = wf.getframerate()
    frames     = wf.readframes(wf.getnframes())
    wf.close()

    # 2. Decode & reshape
    pcm = np.frombuffer(frames, dtype=np.int16).reshape(-1, n_channels)

    # 3. Time-compress each channel
    orig_len = pcm.shape[0]
    new_len  = int(orig_len / speed)
    if new_len < 1:
        return

    old_idx = np.arange(orig_len)
    new_idx = np.linspace(0, orig_len, new_len, endpoint=False)
    fast_pcm = np.vstack([
        np.interp(new_idx, old_idx, pcm[:, ch]).astype(np.int16)
        for ch in range(n_channels)
    ]).T

    # 4. Play via PyAudio at WAV?s sample rate
    pa = pyaudio.PyAudio()
    stream = pa.open(
        format    = pa.get_format_from_width(sampwidth),
        channels  = n_channels,
        rate      = framerate,
        output    = True,
        frames_per_buffer = 1024
    )
    stream.write(fast_pcm.tobytes())
    stream.stop_stream()
    stream.close()
    pa.terminate()

def _play_in_background(path: str):
    """Helper to fire-and-forget playback."""
    t = threading.Thread(target=play_wav_speed, args=(path,), daemon=True)
    t.start()

def play_random_ash():
    """
    Pick one random 'ash' intro WAV from audio/tts/ash/
    and play it at 1.3� speed on the left speaker.
    """
    files = glob.glob("audio/tts/ash/ash_intro_*.wav")
    if not files:
        raise FileNotFoundError("No ash intros found in audio/tts/ash/")
    choice = random.choice(files)
    # _play_in_background(choice)
    play_wav_speed(choice)

def play_random_coral():
    """
    Pick one random 'coral' intro WAV from audio/tts/coral/
    and play it at 1.3� speed on the right speaker.
    """
    files = glob.glob("audio/tts/coral/coral_intro_*.wav")
    if not files:
        raise FileNotFoundError("No coral intros found in audio/tts/coral/")
    choice = random.choice(files)
    # _play_in_background(choice)
    play_wav_speed(choice)

def play_random_nonet(wakeword: str):
    if wakeword not in ["hey-octo", "hey-coral"]:
        raise ValueError("Invalid wakeword. Choose 'ash' or 'coral'.")
    if wakeword == "hey-octo":
        files = glob.glob(f"audio/tts/ash/ash_nonet_*.wav")
    else:
        files = glob.glob(f"audio/tts/coral/coral_nonet_*.wav")
    if not files:
        raise FileNotFoundError(f"No {wakeword} intros found in audio/tts/")
    choice = random.choice(files)
    play_wav_speed(choice)
# Example usage:
if __name__ == "__main__":
    print("Triggering a random Ash intro?")
    play_random_ash()
    # your main thread continues immediately
    import time; time.sleep(3)

    print("Triggering a random Coral intro?")
    play_random_coral()
    time.sleep(3)
