import asyncio, os, wave, time, numpy as np, sounddevice as sd
from dotenv import load_dotenv
from openai import AsyncOpenAI
import traceback

load_dotenv()
_BASE_RATE = 24_000             # native sample rate
SPEED = 1.9                     # 30% faster
_OUT_RATE = int(_BASE_RATE * SPEED)
DEFAULT_GAIN = 2.0
sd.default.device = (None, 'plughw:1,0')

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
    wf.setnchannels(2)           # stereo
    wf.setsampwidth(2)           # 16-bit
    wf.setframerate(_OUT_RATE)   # speed-up via header
    return wf

async def _speak_chan(text: str, voice: str, left: bool, gain: float = DEFAULT_GAIN):
    _ensure_dir()
    ts = time.strftime("%Y%m%d-%H%M%S")
    print(f"[{ts}] Speaking ({'L' if left else 'R'}) → {text!r} via “{voice}”")
    wf = _open_wav(ts)
    buf = bytearray()
    try:
        with sd.OutputStream(samplerate=_OUT_RATE, channels=2, dtype="int16") as stream:
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
                        frame_bytes = buf[:n]
                        buf = buf[n:]
                        # decode and apply gain
                        pcm16 = np.frombuffer(frame_bytes, dtype=np.int16).astype(np.int32)
                        pcm16 = np.clip(pcm16 * gain, -32768, 32767).astype(np.int16)
                        #build stereo: [L, R]
                        if left:
                            stereo = np.column_stack((pcm16, np.zeros_like(pcm16)))
                        else:
                            stereo = np.column_stack((np.zeros_like(pcm16), pcm16))
                                # play fast on the fly?
                        print("stereo.shape =", stereo.shape)
                        print("first 4 samples L/R:", stereo[:4])
                        stream.write(stereo)
                        # ?and save a true?speed WAV
                        wf.writeframes(stereo.astype(np.int16).tobytes())
                wf.close()
                print(f"Saved as responses/{ts}.wav")
    except Exception:
          print(f"[{ts}] Playback or save failed!")
          traceback.print_exc()
async def speak_female(text: str):
    """Left-channel coral (female) at 1.3 speed."""
    await _speak_chan(text, voice="coral", left=True)

async def speak_male(text: str):
    """Right-channel ash (male) at 1.3 speed."""
    await _speak_chan(text, voice="ash", left=False)

# test CLI
if __name__ == "__main__":
    asyncio.run(speak_female("Hey, whats up, octo-honey?"))
    asyncio.run(speak_male("Leave me alone, you octo-pinky-winky-dinky!"))
    asyncio.run(speak_female("That's rude! You want a piece of me?"))
    asyncio.run(speak_male("I don't want a piece of you, I want the whole thing!"))
