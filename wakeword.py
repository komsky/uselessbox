import os
import argparse
import asyncio
from datetime import datetime

import numpy as np

# openWakeWord hardcodes num_threads=1 when building its tflite interpreters.
# On the Pi Zero 2 W that's ~89 ms per 80 ms frame (too slow); 3 threads brings
# it to ~63 ms (real-time with headroom). Patch the interpreter ctor before
# importing the Model so every interpreter oWW builds is multi-threaded.
_OWW_THREADS = int(os.getenv("OWW_THREADS", "3"))
try:
    import tflite_runtime.interpreter as _tflite
    _orig_interpreter = _tflite.Interpreter
    def _threaded_interpreter(*args, **kwargs):
        kwargs["num_threads"] = _OWW_THREADS
        return _orig_interpreter(*args, **kwargs)
    _tflite.Interpreter = _threaded_interpreter
except ImportError:
    pass  # off-Pi (no tflite_runtime): openwakeword falls back to its own backend

from openwakeword.model import Model
from pvrecorder import PvRecorder

# openWakeWord operates on 80ms frames at 16kHz
FRAME_LENGTH = 1280
SAMPLE_RATE = 16000


class WakeWordDetector:
    """
    Asynchronous Wake Word Detector using openWakeWord (tflite).

    Replaces the Picovoice Porcupine implementation (free tier discontinued
    2026-06-30) with locally-trained openWakeWord models. The public contract
    is unchanged: `await wait_for_wakeword()` returns (keyword_index, keyword),
    where keyword matches the legacy Porcupine phrase names ("hey-octo",
    "hey-coral", "knight-rider") derived from the model filename stem.

    Usage:
        detector = WakeWordDetector(
            model_paths=["models/hey_octo.tflite", "models/hey_coral.tflite"],
            threshold=0.6,
        )
        keyword_index, keyword = await detector.wait_for_wakeword()
    """

    def __init__(
        self,
        model_paths,
        threshold: float = 0.6,
        trigger_frames: int = 2,
        device_index: int = -1,
        inference_framework: str = "tflite",
        **_legacy_kwargs,  # tolerates old access_key/sensitivities call sites
    ):
        if isinstance(model_paths, str):
            model_paths = [model_paths]
        if not isinstance(model_paths, (list, tuple)) or not model_paths:
            raise ValueError("`model_paths` must be a non-empty string or list of strings.")

        validated = []
        for path in model_paths:
            p = os.path.expanduser(path)
            if not os.path.isfile(p):
                raise OSError(f"Couldn't find wake word model at '{path}'.")
            validated.append(p)
        self.model_paths = validated

        # "hey_octo.tflite" -> "hey-octo" (legacy Porcupine phrase names used by main.py).
        # rsplit, not splitext: built-in oww model names carry dots ("hey_jarvis_v0.1").
        self._model_keys = [
            os.path.basename(p).rsplit(".", 1)[0] for p in self.model_paths
        ]
        self._keywords = [k.replace("_", "-") for k in self._model_keys]

        self.threshold = threshold
        self.trigger_frames = max(1, trigger_frames)
        self.device_index = device_index

        # The model is loaded once (a few seconds on a Pi Zero 2); the recorder is
        # opened per wait call so the mic is released for the utterance capture.
        self._model = Model(
            wakeword_models=self.model_paths,
            inference_framework=inference_framework,
        )

    @property
    def keywords(self):
        return list(self._keywords)

    async def wait_for_wakeword(self):
        """
        Listen until one of the wake words fires.

        Returns:
            (keyword_index: int, keyword: str)
        """
        recorder = PvRecorder(frame_length=FRAME_LENGTH, device_index=self.device_index)
        loop = asyncio.get_running_loop()

        self._model.reset()
        consecutive = [0] * len(self._model_keys)
        recorder.start()
        try:
            while True:
                pcm = await loop.run_in_executor(None, recorder.read)
                frame = np.asarray(pcm, dtype=np.int16)
                scores = await loop.run_in_executor(None, self._model.predict, frame)
                for i, key in enumerate(self._model_keys):
                    if scores.get(key, 0.0) >= self.threshold:
                        consecutive[i] += 1
                        if consecutive[i] >= self.trigger_frames:
                            return i, self._keywords[i]
                    else:
                        consecutive[i] = 0
        finally:
            recorder.delete()


def main():
    parser = argparse.ArgumentParser(description="Run WakeWordDetector standalone.")
    parser.add_argument(
        '--model_paths', required=True, nargs='+',
        help='Paths to openWakeWord .tflite model files'
    )
    parser.add_argument('--threshold', type=float, default=0.6)
    parser.add_argument(
        '--audio_device_index', type=int, default=-1,
        help='Index of input audio device. Default: -1 (system default).'
    )
    args = parser.parse_args()

    detector = WakeWordDetector(
        model_paths=args.model_paths,
        threshold=args.threshold,
        device_index=args.audio_device_index,
    )
    print(f"Listening for {detector.keywords} ... Ctrl+C to stop")
    while True:
        index, keyword = asyncio.run(detector.wait_for_wakeword())
        print(f"[{datetime.now().strftime('%H:%M:%S')}] detected '{keyword}' (index {index})")


if __name__ == '__main__':
    main()
