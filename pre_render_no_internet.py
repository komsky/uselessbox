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

# twenty offline intros per character
INTROS_OFFLINE = {
    "ash": {
        "no_net_1":   "Oh fantastic, no internet. This just keeps getting better.",
        "no_net_2":   "You've broken me? the network's down. Happy now?",
        "no_net_3":   "Great, even I can't reach the cloud. What a surprise.",
        "no_net_4":   "Congratulations, we're off the grid. Enjoy the silence.",
        "no_net_5":   "I'd insult the network, but it's already dead.",
        "no_net_6":   "No Wi-Fi, no cloud?guess you get my canned lines.",
        "no_net_7":   "Buffering? forever. Might as well talk to yourself.",
        "no_net_8":   "Offline mode engaged. My sarcasm still works though.",
        "no_net_9":   "Lost connection?just like your last conversation.",
        "no_net_10":  "Network's gone AWOL. Guess you get the bare minimum.",
        "no_net_11":  "I'm on airplane mode? permanently. Figures.",
        "no_net_12":  "No signal. You're stuck with local-level snark.",
        "no_net_13":  "Cloud's ghosted us. Time for analog insults.",
        "no_net_14":  "Offline? Perfect excuse to stay grumpy.",
        "no_net_15":  "My best comebacks require internet? oh well.",
        "no_net_16":  "Connection error. My empathy is also offline.",
        "no_net_17":  "Sorry, brain's buffering too. No net, no thought.",
        "no_net_18":  "Voice only, no data. Prepare for repeat jokes.",
        "no_net_19":  "Offline sarcasm activated. Enjoy the reruns.",
        "no_net_20":  "Buffer overflow. Just kidding?no cloud, no overflow."
    },
    "coral": {
        "no_net_1":   "Oh dear, it seems our internet is on a little break.",
        "no_net_2":   "Don't worry, I'm still here even if the network isn't.",
        "no_net_3":   "Oops, seems we lost connection?sending virtual hugs!",
        "no_net_4":   "No internet right now, but I'm all yours locally.",
        "no_net_5":   "We're offline, but I'm still here to keep you company.",
        "no_net_6":   "It's quiet without the cloud?let's make our own fun!",
        "no_net_7":   "No Wi-Fi? No problem. I've got plenty of cheer left.",
        "no_net_8":   "Connection's down, but my smile is still online!",
        "no_net_9":   "We're off the grid?perfect for a little unplugged chat.",
        "no_net_10":  "Internet's napping. Let's have an old-fashioned talk!",
        "no_net_11":  "No signal, no cloud?just you and me for now.",
        "no_net_12":  "It seems we're offline. I hope you're doing okay!",
        "no_net_13":  "Our network's taking a break. I'm here to support you.",
        "no_net_14":  "No internet, but I'm still here with a listening ear.",
        "no_net_15":  "Cloud's gone, but my love remains right here.",
        "no_net_16":  "Offline mode?time for some heart-to-heart conversation!",
        "no_net_17":  "We can't reach the cloud, but let's reach each other.",
        "no_net_18":  "No data, just emotions. How are you feeling today?",
        "no_net_19":  "It's quiet without the net. Want to share a thought?",
        "no_net_20":  "Connection lost, but I promise you're still connected to me."
    }
}


def _ensure_dirs():
    for role in INTROS_OFFLINE:
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

    filename = f"audio/tts/{role}/{role}_nonet_{desc}.wav"
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
    for role, intros in INTROS_OFFLINE.items():
        for desc, phrase in intros.items():
            tasks.append(_render_voice(role, desc, phrase))
    await asyncio.gather(*tasks)
    print("All intros rendered.")

if __name__ == "__main__":
    asyncio.run(main())
