import os
import wave
import webrtcvad
import pyaudio
from datetime import datetime
from openai import OpenAI

# ??? CONFIG ???
SAMPLE_RATE      = 16000
FRAME_DURATION_MS= 30                   # must be 10, 20 or 30
FRAME_SAMPLES    = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)  # 480
FRAME_BYTES      = FRAME_SAMPLES * 2     # 16-bit mono ? 2 bytes/sample
TIMEOUT_SILENCE  = 1.0                  # seconds of silence to stop
# ??????????

def record_utterance(aggressiveness=3):
    vad    = webrtcvad.Vad(aggressiveness)
    pa     = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16,
                     channels=1,
                     rate=SAMPLE_RATE,
                     input=True,
                     frames_per_buffer=FRAME_SAMPLES)

    print("? Waiting for speech?")
    # 1) spin until we see voice
    while True:
        buf = stream.read(FRAME_SAMPLES, exception_on_overflow=False)
        if len(buf) != FRAME_BYTES:
            continue
        if vad.is_speech(buf, SAMPLE_RATE):
            print("??  Speech started")
            break

    # 2) record until we see silence for TIMEOUT_SILENCE
    frames = [buf]
    silent_chunks = 0
    max_silent_chunks = int(TIMEOUT_SILENCE * 1000 / FRAME_DURATION_MS)

    while True:
        buf = stream.read(FRAME_SAMPLES, exception_on_overflow=False)
        if len(buf) != FRAME_BYTES:
            continue
        frames.append(buf)
        if vad.is_speech(buf, SAMPLE_RATE):
            silent_chunks = 0
        else:
            silent_chunks += 1
            if silent_chunks > max_silent_chunks:
                print("? Speech ended")
                break

    stream.stop_stream()
    stream.close()
    pa.terminate()

    return b"".join(frames)


def save_wav(pcm, path):
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm)


def transcribe(wav_path, language=None):
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("Please set OPENAI_API_KEY")
    client = OpenAI(api_key=key)
    with open(wav_path, "rb") as f:
        resp = client.audio.transcriptions.create(
            file=f,
            model="whisper-1",
            language=language,
            temperature=0.0,
            response_format="text",
        )
    return resp["text"]


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--aggressiveness", type=int, default=3,
                        help="VAD aggressiveness (0?3, higher=more filtering)")
    parser.add_argument("--language", type=str, default=None,
                        help="Whisper language code (e.g. en)")
    parser.add_argument("--out_dir", type=str, default=".",
                        help="Where to store temp WAV")
    args = parser.parse_args()

    pcm = record_utterance(args.aggressiveness)
    ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
    wav = os.path.join(args.out_dir, f"utt_{ts}.wav")
    save_wav(pcm, wav)
    print(f"? Saved: {wav}")

    text = transcribe(wav, args.language)
    print("? Transcription:", text)

    try:
        os.remove(wav)
        print(f"??  Deleted temp file")
    except OSError:
        pass


if __name__ == "__main__":
    main()
