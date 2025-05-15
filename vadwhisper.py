#!/usr/bin/env python3
import os
import wave
import time
import math
import argparse
from datetime import datetime
from dotenv import load_dotenv
import numpy as np
import pyaudio
from openai import OpenAI

# ? CONFIGURATION ?????????????????????????????????????????????????????
SAMPLE_RATE    = 16000
FRAME_MS       = 30
FRAME_SIZE     = int(SAMPLE_RATE * FRAME_MS / 1000)      # samples per frame
FRAME_BYTES    = FRAME_SIZE * 2                         # 16-bit mono
START_THRESHOLD= 500    # tune: RMS above this ? start of speech
END_THRESHOLD  = 300    # tune: RMS below this ? possibly end of speech
MAX_SILENT_FRAMES = int(0.5 * 1000 / FRAME_MS)  # 0.5 s of silence to stop
# ????????????????????????????????????????????????????????????????


def rms(data: bytes) -> float:
    """Compute RMS of 16-bit PCM."""
    samples = np.frombuffer(data, dtype=np.int16)
    return math.sqrt(np.mean(samples.astype(np.float64)**2))


def record_energy_vad(start_thr, end_thr, max_silent):
    pa = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16,
                     channels=1,
                     rate=SAMPLE_RATE,
                     input=True,
                     frames_per_buffer=FRAME_SIZE)
    print("??  Waiting for speech?")
    # 1) wait for energy to exceed start threshold
    while True:
        buf = stream.read(FRAME_SIZE, exception_on_overflow=False)
        if rms(buf) > start_thr:
            print("?? Speech started")
            frames = [buf]
            break

    # 2) record until we get max_silent consecutive frames below end_thr
    silent = 0
    while True:
        buf = stream.read(FRAME_SIZE, exception_on_overflow=False)
        frames.append(buf)
        if rms(buf) < end_thr:
            silent += 1
            if silent > max_silent:
                print("?? Speech ended")
                break
        else:
            silent = 0

    stream.stop_stream()
    stream.close()
    pa.terminate()
    return b"".join(frames)


def save_wav(pcm: bytes, path: str):
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm)


def transcribe(wav_path: str, language: str = None) -> str:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("Please set OPENAI_API_KEY in your environment")
    client = OpenAI(api_key=key)
    with open(wav_path, "rb") as f:
        resp = client.audio.transcriptions.create(
            file=f,
            model="whisper-1",
            language=language,
            temperature=0.0,
            response_format="text"
        )
    return resp["text"]


def main():
    parser = argparse.ArgumentParser(
        description="Energy-threshold VAD ? Whisper transcription"
    )
    parser.add_argument("--start_thr", type=float, default=START_THRESHOLD,
                        help="RMS threshold to start recording")
    parser.add_argument("--end_thr",   type=float, default=END_THRESHOLD,
                        help="RMS threshold to end recording")
    parser.add_argument("--silence_s", type=float, default=0.5,
                        help="Seconds of silence to stop")
    parser.add_argument("--language",  type=str, default=None,
                        help="Whisper language code (e.g. en)")
    parser.add_argument("--out_dir",   type=str, default=".",
                        help="Where to write temporary WAV")
    args = parser.parse_args()

    max_silent = int(args.silence_s * 1000 / FRAME_MS)
    pcm = record_energy_vad(args.start_thr, args.end_thr, max_silent)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    wav_path = os.path.join(args.out_dir, f"utt_{ts}.wav")
    save_wav(pcm, wav_path)
    print(f"? Saved: {wav_path}")

    text = transcribe(wav_path, args.language)
    print("? Transcription:", text)

    try:
        os.remove(wav_path)
        print("??  Deleted temp file")
    except OSError:
        pass


if __name__ == "__main__":
    load_dotenv()
    main()
