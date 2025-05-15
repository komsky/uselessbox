import os
import wave
import time
import webrtcvad
import pyaudio
from datetime import datetime
from openai import OpenAI

SAMPLE_RATE = 16000
FRAME_MS   = 30
FRAME_BYTES = int(SAMPLE_RATE * FRAME_MS / 1000) * 2  # 16-bit mono

def record_utterance(aggressiveness=3, timeout_s=5):
    """Record until we see speech, then until we see silence again."""
    vad = webrtcvad.Vad(aggressiveness)
    pa  = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16,
                     channels=1,
                     rate=SAMPLE_RATE,
                     input=True,
                     frames_per_buffer=FRAME_BYTES)

    print("Waiting for you to start speaking?")
    # wait for speech
    while True:
        frame = stream.read(FRAME_BYTES, exception_on_overflow=False)
        if vad.is_speech(frame, SAMPLE_RATE):
            print("? Speech started")
            break

    # collect until silence
    frames = [frame]
    silent_chunks = 0
    max_silent = int(timeout_s * 1000 / FRAME_MS)

    while True:
        frame = stream.read(FRAME_BYTES, exception_on_overflow=False)
        if vad.is_speech(frame, SAMPLE_RATE):
            frames.append(frame)
            silent_chunks = 0
        else:
            silent_chunks += 1
            if silent_chunks > max_silent:
                print("? Speech ended")
                break
            frames.append(frame)

    stream.stop_stream()
    stream.close()
    pa.terminate()

    return b"".join(frames)

def save_wav(pcm_bytes, path):
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm_bytes)

def transcribe(wav_path, language=None):
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("Set OPENAI_API_KEY in environment")
    client = OpenAI(api_key=key)
    with open(wav_path, "rb") as f:
        resp = client.audio.transcriptions.create(
            file=f, model="whisper-1",
            language=language, temperature=0,
            response_format="text"
        )
    return resp["text"]

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--aggressiveness", type=int, default=3,
                        help="VAD mode 0?3 (higher=more aggressive)")
    parser.add_argument("--language", type=str, default=None,
                        help="Whisper language code (e.g. 'en')")
    parser.add_argument("--out_dir", type=str, default=".",
                        help="Where to put temporary WAV")
    args = parser.parse_args()

    pcm = record_utterance(args.aggressiveness)
    ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
    wav = os.path.join(args.out_dir, f"utt_{ts}.wav")
    save_wav(pcm, wav)
    print(f"Saved ? {wav}")

    text = transcribe(wav, args.language)
    print("Transcription:", text)

    try:
        os.remove(wav)
        print(f"Deleted temporary file {wav}")
    except OSError:
        pass

if __name__ == "__main__":
    main()
