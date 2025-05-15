import os
import sys
import argparse
import struct
import wave
import asyncio
from datetime import datetime

import pvcobra
from pvrecorder import PvRecorder


class CobraDetector:
    """
    Asynchronous Cobra voice activity detector with utterance segmentation.

    Usage:
        detector = CobraDetector(access_key, library_path=None, device_index=0)
        pcm = await detector.wait_for_utterance(
            threshold=0.5,
            silence_timeout=1.0
        )
    """

    def __init__(
        self,
        access_key: str,
        library_path: str = None,
        device_index: int = -1,
        frame_length: int = 512,
        sample_rate: int = 16000,
    ):
        self.access_key = access_key
        self.library_path = library_path
        self.device_index = device_index
        self.frame_length = frame_length
        self.sample_rate = sample_rate

    async def wait_for_utterance(
        self,
        threshold: float = 0.5,
        silence_timeout: float = 1.0
    ) -> bytes:
        """
        Listen for speech: start when voice probability ? threshold, stop when silence_timeout
        seconds of probability < threshold occur. Returns raw PCM bytes.
        """
        cobra = pvcobra.create(access_key=self.access_key, library_path=self.library_path)
        recorder = PvRecorder(frame_length=self.frame_length, device_index=self.device_index)
        recorder.start()

        loop = asyncio.get_running_loop()
        started = False
        frames = []
        silent_frames = 0
        frame_time = self.frame_length / self.sample_rate
        max_silent = int(silence_timeout / frame_time)

        try:
            while True:
                pcm_frame = await loop.run_in_executor(None, recorder.read)
                prob = cobra.process(pcm_frame)

                if not started:
                    if prob >= threshold:
                        started = True
                        frames.append(pcm_frame)
                else:
                    frames.append(pcm_frame)
                    if prob < threshold:
                        silent_frames += 1
                        if silent_frames >= max_silent:
                            break
                    else:
                        silent_frames = 0
            return b"".join(struct.pack("h" * len(f), *f) for f in frames)
        finally:
            recorder.delete()
            cobra.delete()

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
    parser = argparse.ArgumentParser(description="Cobra-based utterance detector")
    parser.add_argument("--access_key", help="Picovoice AccessKey")
    parser.add_argument("--library_path", help="Path to Cobra library")
    parser.add_argument("--device_index", type=int, default=-1, help="Audio device index")
    parser.add_argument("--threshold", type=float, default=0.5, help="Start threshold")
    parser.add_argument("--silence_timeout", type=float, default=1.0, help="Seconds of silence to stop")
    parser.add_argument("--out_dir", type=str, default='.', help="Directory for WAV output")
    parser.add_argument("--show_devices", action="store_true", help="List audio devices")
    args = parser.parse_args()

    if args.show_devices:
        CobraDetector.show_audio_devices()
        sys.exit(0)
    access_key = args.access_key
    if not args.access_key:
        access_key = os.getenv("PICOVOICE")

    detector = CobraDetector(
        access_key=access_key,
        library_path=args.library_path,
        device_index=args.device_index
    )

    print(f"Waiting for utterance (threshold={args.threshold}, silence={args.silence_timeout}s)")
    pcm = asyncio.run(detector.wait_for_utterance(args.threshold, args.silence_timeout))

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    wav_path = os.path.join(args.out_dir, f"utt_{ts}.wav")
    detector.save_wav(pcm, wav_path)
    print(f"Saved utterance to {wav_path}")


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    main()
