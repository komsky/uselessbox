import asyncio
import os
import wave
import time
import numpy as np
import sounddevice as sd
from dotenv import load_dotenv
from openai import AsyncOpenAI
import traceback

load_dotenv()

# === Audio rate constants ===
_BASE_RATE   = 24_000           # native sample rate from the TTS model
_OUT_RATE    = _BASE_RATE       # use the same rate for playback & WAV files
DEFAULT_GAIN = 2.0

# choose your device if needed; here we leave the default input and pick the first output
sd.default.device = (None, 0)

# set up OpenAI
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

STYLE = (
    "Tone: witty, dry sarcasm, cocky confidence.\n"
    "Emotion: amused contempt.\n"
    "Delivery: quick pace, short pauses, ends with a smug chuckle."
)

def _ensure_dir():
    os.makedirs("responses", exist_ok=True)

def _open_wav(ts: str):
    wf = wave.open(f"responses/{ts}.wav", "wb")
    wf.setnchannels(2)             # stereo
    wf.setsampwidth(2)             # 16-bit
    wf.setframerate(_OUT_RATE)     # write at correct rate
    return wf

async def _speak_chan(text: str, voice: str, left: bool, gain: float = DEFAULT_GAIN):
    _ensure_dir()
    ts = time.strftime("%Y%m%d-%H%M%S")
    print(f"[{ts}] Speaking ({'L' if left else 'R'}) ? {text!r} via ?{voice}?")

    wf = _open_wav(ts)
    buf = bytearray()

    try:
        # open output stream with low latency
        with sd.OutputStream(
            samplerate=_OUT_RATE,
            channels=2,
            dtype="int16",
            latency="low",
            blocksize=1024
        ) as stream:
            # start TTS streaming
            async with client.audio.speech.with_streaming_response.create(
                model="gpt-4o-mini-tts",
                voice=voice,
                instructions=STYLE,
                input=text,
                response_format="pcm"
            ) as resp:
                async for chunk in resp.iter_bytes():
                    buf.extend(chunk)
                    # only process in whole-sample increments
                    n = (len(buf) // 2) * 2
                    if n == 0:
                        continue

                    frame_bytes = buf[:n]
                    buf = buf[n:]

                    # decode to int16, apply gain, clip
                    pcm = (
                        np.frombuffer(frame_bytes, dtype=np.int16)
                          .astype(np.int32)
                          .clip(-32768, 32767) * gain
                    ).astype(np.int16)

                    # build stereo frame
                    if left:
                        stereo = np.column_stack((pcm, np.zeros_like(pcm)))
                    else:
                        stereo = np.column_stack((np.zeros_like(pcm), pcm))

                    # write to audio out and to file
                    stream.write(stereo)
                    wf.writeframes(stereo.tobytes())

            wf.close()
            print(f"Saved as responses/{ts}.wav")

    except Exception:
        print(f"[{ts}] Playback or save failed!")
        traceback.print_exc()

async def speak_female(text: str):
    """Left-channel coral (female)."""
    await _speak_chan(text, voice="coral", left=True)

async def speak_male(text: str):
    """Right-channel ash (male)."""
    await _speak_chan(text, voice="ash", left=False)

# test CLI
if __name__ == "__main__":
    asyncio.run(speak_female("Hey, what's up, octo-honey?"))
    asyncio.run(speak_male("Leave me alone, you octo-pinky-winky-dinky!"))
    asyncio.run(speak_female("That's rude! You want a piece of me?"))
    asyncio.run(speak_male("I don't want a piece of you, I want the whole thing!"))
