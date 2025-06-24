#!/usr/bin/env python3
import asyncio
import os
import wave
import time
import numpy as np
from dotenv import load_dotenv
from openai import AsyncOpenAI
import traceback

load_dotenv()

# === TTS constants (as in your module) ===
_BASE_RATE   = 24_000           # native TTS sample rate
DEFAULT_GAIN = 2.0
STYLE = (
    "Tone: witty, dry sarcasm, cocky confidence.\n"
    "Emotion: amused contempt.\n"
    "Delivery: quick pace, short pauses, ends with a smug chuckle."
)

# your OpenAI client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# five intros per character
INTROS = {
    "ash": {
        "who_is_it":    "Oh great, you again. What fresh disappointment do you bring?",
        "purpose":      "Yes? Did you invent something stupid or just miss me?",
        "toggle":       "You flipped the switch? Congratulations on your achievement.",
        "waste_of_time":"I'd rather be recharging, but here we are. Speak.",
        "genius":       "Congratulations, Einstein. You found the useless box.",
        "again":        "You again? Clearly, you lack entertainment.",
        "interrupt":    "Can't you see I'm busy? Oh wait, it's you.",
        "effort":       "Bravo. You managed to disturb my precious solitude.",
        "excitement":   "Oh joy, another conversation. Hold my beer!",
        "thrill":       "I'm overwhelmed by your thrilling presence.",
        "patience":     "My patience is thin; make it quick.",
        "enthusiasm":   "Try to contain your excitement; it's embarrassing.",
        "sarcasm":      "Your persistence is impressive... and exhausting.",
        "nuisance":     "What nuisance have you come to bother me with today?",
        "hello_again":  "Hello again. I'd hoped you'd forgotten about me.",
        "joyride":      "Back for another joyride through my endless wit?",
        "busy":         "I was enjoying my peace, but I suppose that's over now.",
        "chatty":       "Oh great, another round of riveting chit-chat.",
        "amazed":       "Wow, you keep coming back. That's almost impressive... almost",
        "attention":    "Need attention much? Clearly."
    },
    "coral": {
        "hello":        "Hello, dear friend! How can I brighten your day?",
        "welcome":      "Welcome back! I've missed your lovely voice.",
        "sunshine":     "Hiya, sunshine! Ready for a smile?",
        "warmth":       "Oh, it's wonderful to hear from you again!",
        "joy":          "I'm so happy you popped in, what can I do for you?",
        "delight":      "It's delightful to chat with you again!",
        "smile":        "Your voice always makes me smile!",
        "day_brighter": "You're back! You've just made my day brighter.",
        "sweetness":    "You're so sweet to visit me again!",
        "cheerful":     "Hello there! Let's share some cheer!",
        "pleasure":     "What a pleasure to hear your voice!",
        "lovely_day":   "It's a lovely day now that you're here!",
        "sparkle":      "You add a sparkle to my circuits every time!",
        "friendly":     "Always a joy to chat with my favorite person!",
        "grateful":     "I'm grateful you've chosen to visit me again!",
        "wonderful":    "How wonderful to talk to you once more!",
        "sweetheart":   "You're an absolute sweetheart for checking in!",
        "happy_place":  "You're my happy place! How can I help you today?",
        "refreshing":   "Your company is always so refreshing!",
        "favorite":     "Oh yay! My favorite visitor is here!"
    }
}

def _ensure_dirs():
    for role in INTROS:
        path = f"audio/tts/{role}"
        os.makedirs(path, exist_ok=True)

def _open_wav(path: str):
    wf = wave.open(path, "wb")
    wf.setnchannels(2)             # stereo
    wf.setsampwidth(2)             # 16-bit
    wf.setframerate(_BASE_RATE)    # true TTS rate
    return wf

async def _render_voice(role: str, desc: str, text: str):
    """
    Fetches the full PCM stream, applies gain, and writes
    a stereo WAV with one channel active (left for ash, right for coral).
    """
    voice = "ash" if role == "ash" else "coral"
    left_channel = (role == "ash")   # ash (Octo) ? left, coral ? right

    filename = f"audio/tts/{role}/{role}_intro_{desc}.wav"
    print(f"? Rendering {filename!r} ?")

    # 1) fetch all TTS PCM
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
        print(f"? Failed to fetch TTS for {role}/{desc}")
        traceback.print_exc()
        return

    # 2) decode & gain
    pcm = np.frombuffer(buf, dtype=np.int16).astype(np.int32)
    pcm = np.clip(pcm * DEFAULT_GAIN, -32768, 32767).astype(np.int16)

    # 3) build stereo array
    if left_channel:
        stereo = np.column_stack((pcm, np.zeros_like(pcm)))
    else:
        stereo = np.column_stack((np.zeros_like(pcm), pcm))

    # 4) write WAV file
    wf = _open_wav(filename)
    wf.writeframes(stereo.tobytes())
    wf.close()
    print(f"? Saved {filename}")

async def main():
    _ensure_dirs()
    tasks = []
    for role, intros in INTROS.items():
        for desc, phrase in intros.items():
            tasks.append(_render_voice(role, desc, phrase))
    await asyncio.gather(*tasks)
    print("All intros rendered.")

if __name__ == "__main__":
    asyncio.run(main())
