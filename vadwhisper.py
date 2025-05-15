import os
import wave
import speech_recognition as sr
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

def listen_and_transcribe(language=None):
    # pull your Whisper key from the env
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Set OPENAI_API_KEY")

    # set up the mic + recognizer
    r = sr.Recognizer()
    with sr.Microphone(sample_rate=16000) as mic:
        print("? Speak now?")
        # blocks until user stops speaking (silence timeout baked in)
        audio = r.listen(mic)
        print("??  Done recording.")

    # save to temp WAV
    pcm = audio.get_raw_data(convert_rate=16000, convert_width=2)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    wav_path = f"utt_{ts}.wav"
    with wave.open(wav_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(pcm)

    # send to Whisper
    client = OpenAI(api_key=api_key)
    with open(wav_path, "rb") as f:
        resp = client.audio.transcriptions.create(
            file=f,
            model="whisper-1",
            language=language,
            temperature=0.0,
            response_format="text"
        )

    # cleanup + return
    os.remove(wav_path)
    return resp["text"]

if __name__ == "__main__":
    load_dotenv()
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--language", default=None)
    args = p.parse_args()

    text = listen_and_transcribe(language=args.language)
    print("? You said:", text)
