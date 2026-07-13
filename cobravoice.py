import os
import sys
import argparse
import struct
import wave
import asyncio
from collections import deque
from datetime import datetime

import math

import webrtcvad
from pvrecorder import PvRecorder


def _rms(frame) -> float:
    return math.sqrt(sum(s * s for s in frame) / len(frame))


class CobraDetector:
    """
    Asynchronous voice activity detector with utterance segmentation.

    Replaces Picovoice Cobra (free tier discontinued 2026-06-30) with webrtcvad.
    Class name and public contract are unchanged so existing call sites keep
    working: `await wait_for_utterance(threshold, silence_timeout)` returns raw
    16-bit mono PCM bytes of one utterance.

    Improvements over the Cobra version:
    - a ~300ms pre-roll ring buffer, so the first syllable is not clipped
    - a max_utterance_s cap, so a noisy room cannot record forever
    """

    FRAME_MS = 30  # webrtcvad accepts 10/20/30ms frames

    def __init__(
        self,
        access_key: str = None,   # legacy arg, ignored (kept for call-site compat)
        library_path: str = None,  # legacy arg, ignored
        device_index: int = -1,
        sample_rate: int = 16000,
        max_utterance_s: float = 15.0,
    ):
        self.device_index = device_index
        self.sample_rate = sample_rate
        self.frame_length = sample_rate * self.FRAME_MS // 1000  # 480 @ 16k
        self.max_utterance_s = max_utterance_s

    async def wait_for_utterance(
        self,
        threshold: float = 0.5,
        silence_timeout: float = 1.0
    ) -> bytes:
        """
        Listen for speech: start when voice activity is detected, stop after
        silence_timeout seconds without speech. Returns raw PCM bytes.

        `threshold` maps to webrtcvad aggressiveness: <0.4 -> 1 (permissive),
        <0.7 -> 2, else 3 (strict).
        """
        aggressiveness = 1 if threshold < 0.4 else (2 if threshold < 0.7 else 3)
        vad = webrtcvad.Vad(aggressiveness)
        recorder = PvRecorder(frame_length=self.frame_length, device_index=self.device_index)
        recorder.start()

        loop = asyncio.get_running_loop()

        # The ReSpeaker emits a transient right after capture starts, and its noise
        # floor alone can read as speech to webrtcvad. Discard the first ~240ms AND
        # use those frames to measure ambient energy; speech then requires real
        # acoustic energy above the ambient baseline as well as a VAD vote.
        ambient = []
        for _ in range(8):
            warm = await loop.run_in_executor(None, recorder.read)
            ambient.append(_rms(warm))
        # Gate only the noise-floor-reads-as-speech pathology: adapt to quiet rooms but
        # cap the floor so speech always passes even when warm-up caught a loud room.
        energy_floor = min(max(200.0, 3.0 * (sum(ambient) / len(ambient))), 800.0)
        frame_time = self.frame_length / self.sample_rate
        max_silent = max(1, int(silence_timeout / frame_time))
        max_frames = int(self.max_utterance_s / frame_time)
        start_votes_needed = 2  # 60ms of speech to trigger (debounces clicks)

        preroll = deque(maxlen=int(0.3 / frame_time))
        frames = []
        started = False
        speech_votes = 0
        silent_frames = 0

        try:
            while True:
                pcm_frame = await loop.run_in_executor(None, recorder.read)
                raw = struct.pack("h" * len(pcm_frame), *pcm_frame)
                is_speech = (vad.is_speech(raw, self.sample_rate)
                             and _rms(pcm_frame) >= energy_floor)

                if not started:
                    preroll.append(raw)
                    speech_votes = speech_votes + 1 if is_speech else 0
                    if speech_votes >= start_votes_needed:
                        started = True
                        frames.extend(preroll)
                        preroll.clear()
                else:
                    frames.append(raw)
                    if is_speech:
                        silent_frames = 0
                    else:
                        silent_frames += 1
                        if silent_frames >= max_silent:
                            break
                    if len(frames) >= max_frames:
                        break
            return b"".join(frames)
        finally:
            recorder.delete()

    def save_wav(self, pcm_bytes: bytes, path: str):
        """Save PCM bytes (16-bit mono) to WAV file."""
        with wave.open(path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(pcm_bytes)

    @staticmethod
    def show_audio_devices():
        devices = PvRecorder.get_available_devices()
        for i, d in enumerate(devices):
            print(f"{i}: {d}")


def main():
    parser = argparse.ArgumentParser(description="VAD-based utterance detector (webrtcvad)")
    parser.add_argument("--device_index", type=int, default=-1, help="Audio device index")
    parser.add_argument("--threshold", type=float, default=0.5, help="Start threshold")
    parser.add_argument("--silence_timeout", type=float, default=1.0, help="Seconds of silence to stop")
    parser.add_argument("--out_dir", type=str, default='.', help="Directory for WAV output")
    parser.add_argument("--show_devices", action="store_true", help="List audio devices")
    args = parser.parse_args()

    if args.show_devices:
        CobraDetector.show_audio_devices()
        sys.exit(0)

    detector = CobraDetector(device_index=args.device_index)

    print(f"Waiting for utterance (threshold={args.threshold}, silence={args.silence_timeout}s)")
    pcm = asyncio.run(detector.wait_for_utterance(args.threshold, args.silence_timeout))

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    wav_path = os.path.join(args.out_dir, f"utt_{ts}.wav")
    detector.save_wav(pcm, wav_path)
    print(f"Saved utterance to {wav_path}")


if __name__ == '__main__':
    main()
