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

# === Constants ===
_BASE_RATE   = 24_000       # TTS engine?s native sample rate
SPEED        = 1.3          # playback speed multiplier
DEFAULT_GAIN = 2.0

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
    wf.setnchannels(2)
    wf.setsampwidth(2)             # 16-bit
    wf.setframerate(_BASE_RATE)    # files stay at true speed
    return wf

async def _speak_chan(text: str, voice: str, left: bool, gain: float = DEFAULT_GAIN):
    _ensure_dir()
    ts = time.strftime("%Y%m%d-%H%M%S")
    print(f"[{ts}] Rendering ? {text!r} ({voice})")

    # 1) Fetch *all* PCM bytes
    buf = bytearray()
    try:
        async with client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice=voice,
            instructions=STYLE,
            input=text,
            response_format="pcm"
        ) as resp:
            async for chunk in resp.iter_bytes():
                buf.extend(chunk)
    except Exception:
        print(f"[{ts}] TTS fetch failed!")
        traceback.print_exc()
        return

    # 2) Decode & apply gain
    pcm = (
        np.frombuffer(buf, dtype=np.int16)
          .astype(np.int32)
    )
    pcm = np.clip(pcm * gain, -32768, 32767).astype(np.int16)

    # 3) Build stereo True-speed file data
    stereo_file = (
        np.column_stack((pcm, np.zeros_like(pcm))) if left
        else np.column_stack((np.zeros_like(pcm), pcm))
    )

    # 4) Write it out immediately
    wf = _open_wav(ts)
    wf.writeframes(stereo_file.tobytes())
    wf.close()
    print(f"[{ts}] Saved WAV at true speed")

    # 5) Speed & resample for playback
    dev = sd.query_devices(kind='output')
    play_rate = int(dev['default_samplerate'])
    orig_len = pcm.shape[0]
    # first compress time by SPEED
    compressed_len = int(orig_len / SPEED)
    if compressed_len < 1:
        print(f"[{ts}] Audio too short to speed up.")
        return

    compressed = np.interp(
        np.linspace(0, orig_len, compressed_len, endpoint=False),
        np.arange(orig_len),
        pcm
    ).astype(np.int16)

    # then resample to hardware rate
    final_len = int(compressed_len * (play_rate / _BASE_RATE))
    played = np.interp(
        np.linspace(0, compressed_len, final_len, endpoint=False),
        np.arange(compressed_len),
        compressed
    ).astype(np.int16)

    # stereo for playback
    stereo_play = (
        np.column_stack((played, np.zeros_like(played))) if left
        else np.column_stack((np.zeros_like(played), played))
    )

    # 6) Fire-and-forget playback (PortAudio pulls from our array)
    print(f"[{ts}] Playing back at {play_rate} Hz, {SPEED}� speed")
    sd.play(stereo_play, samplerate=play_rate, blocking=True)
    print(f"[{ts}] Done.")

async def speak_female(text: str):
    await _speak_chan(text, voice="coral", left=False)

async def speak_male(text: str):
    await _speak_chan(text, voice="ash", left=True)

if __name__ == "__main__":
    asyncio.run(speak_female("Hey, what's up, octo-honey?"))
    asyncio.run(speak_male("Leave me alone, you octo-pinky-winky-dinky!"))
    asyncio.run(speak_female("That's rude! You want a piece of me?"))
    asyncio.run(speak_male("I don't want a piece of you, I want the whole thing!"))
