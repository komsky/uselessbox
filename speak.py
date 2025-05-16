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
_BASE_RATE   = 24_000           # native TTS rate
DEFAULT_GAIN = 2.0

# ensure our responses folder exists
def _ensure_dir():
    os.makedirs("responses", exist_ok=True)

# open a stereo WAV at the base rate
def _open_wav(ts: str):
    wf = wave.open(f"responses/{ts}.wav", "wb")
    wf.setnchannels(2)
    wf.setsampwidth(2)           # 16-bit
    wf.setframerate(_BASE_RATE)  # real TTS rate
    return wf

# core routine
async def _speak_chan(text: str, voice: str, left: bool, gain: float = DEFAULT_GAIN):
    _ensure_dir()
    ts = time.strftime("%Y%m%d-%H%M%S")
    print(f"[{ts}] Speaking ({'L' if left else 'R'}) ? {text!r} via ?{voice}?")

    # 1) Figure out your hardware's native playback rate:
    dev_info     = sd.query_devices(kind='output')
    play_rate    = int(dev_info['default_samplerate'])
    wf           = _open_wav(ts)
    buf          = bytearray()

    try:
        # 2) Open an output stream at that rate
        with sd.OutputStream(
            samplerate=play_rate,
            channels=2,
            dtype='int16',
            latency='low'
        ) as stream:
            async with client.audio.speech.with_streaming_response.create(
                model="gpt-4o-mini-tts",
                voice=voice,
                instructions=STYLE,
                input=text,
                response_format="pcm"
            ) as resp:
                async for chunk in resp.iter_bytes():
                    buf.extend(chunk)
                    n = (len(buf)//2)*2
                    if n == 0:
                        continue

                    # decode & gain
                    pcm = (
                        np.frombuffer(buf[:n], dtype=np.int16)
                          .astype(np.int32)
                    )
                    buf = buf[n:]
                    pcm = np.clip(pcm * gain, -32768, 32767).astype(np.int16)

                    # 3) Resample from 24 kHz ? play_rate
                    orig_len = pcm.shape[0]
                    new_len  = int(orig_len * play_rate / _BASE_RATE)
                    if new_len < 1:
                        continue
                    resampled = np.interp(
                        np.linspace(0, orig_len, new_len, endpoint=False),
                        np.arange(orig_len),
                        pcm
                    ).astype(np.int16)

                    # build stereo
                    if left:
                        stereo = np.column_stack((resampled, np.zeros_like(resampled)))
                    else:
                        stereo = np.column_stack((np.zeros_like(resampled), resampled))

                    # play and also write the ORIGINAL (non-resampled) stereo into the WAV
                    stream.write(stereo)
                    # for file, we want the true-speed 24 kHz, so re-build it from pcm:
                    if left:
                        wf.writeframes(np.column_stack((pcm, np.zeros_like(pcm))).tobytes())
                    else:
                        wf.writeframes(np.column_stack((np.zeros_like(pcm), pcm)).tobytes())

        wf.close()
        print(f"Saved as responses/{ts}.wav")

    except Exception:
        print(f"[{ts}] Playback or save failed!")
        traceback.print_exc()


# public APIs
async def speak_female(text: str):
    """Left-channel coral (female)."""
    await _speak_chan(text, voice="coral", left=True)

async def speak_male(text: str):
    """Right-channel ash (male)."""
    await _speak_chan(text, voice="ash", left=False)


if __name__ == "__main__":
    # make sure your client & STYLE are defined up top as before
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    STYLE = (
        "Tone: witty, dry sarcasm, cocky confidence.\n"
        "Emotion: amused contempt.\n"
        "Delivery: quick pace, short pauses, ends with a smug chuckle."
    )

    asyncio.run(speak_female("Hey, what's up, octo-honey?"))
    asyncio.run(speak_male("Leave me alone, you octo-pinky-winky-dinky!"))
    asyncio.run(speak_female("That's rude! You want a piece of me?"))
    asyncio.run(speak_male("I don't want a piece of you, I want the whole thing!"))
