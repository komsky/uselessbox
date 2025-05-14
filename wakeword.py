import os
import struct
import asyncio
from datetime import datetime

import pvporcupine
from pvrecorder import PvRecorder


class WakeWordDetector:
    """
    Asynchronous Wake Word Detector using Picovoice Porcupine.

    Usage:
        detector = WakeWordDetector(
            access_key="YOUR_ACCESS_KEY",
            keyword_paths=["/path/to/keyword1.ppn", "/path/to/keyword2.ppn"],
            sensitivities=[0.5, 0.6]
        )
        keyword_index, keyword = await detector.wait_for_wakeword()
    """

    def __init__(
        self,
        access_key: str,
        keyword_paths: list,
        sensitivities: list = None,
        library_path: str = None,
        model_path: str = None,
        device_index: int = -1,
    ):
        if sensitivities is None:
            sensitivities = [0.5] * len(keyword_paths)
        if len(sensitivities) != len(keyword_paths):
            raise ValueError("Number of sensitivities must match number of keywords.")

        self._porcupine = pvporcupine.create(
            access_key=access_key,
            keyword_paths=keyword_paths,
            sensitivities=sensitivities,
            library_path=library_path,
            model_path=model_path,
        )
        self._recorder = PvRecorder(
            frame_length=self._porcupine.frame_length,
            device_index=device_index
        )
        self._keywords = []
        for path in keyword_paths:
            name = os.path.basename(path).replace('.ppn', '').split('_')
            phrase = ' '.join(name[:-6]) if len(name) > 6 else name[0]
            self._keywords.append(phrase)

        self._running = False

    async def wait_for_wakeword(self):
        """
        Start listening and return upon detecting a wake word.

        Returns:
            (keyword_index: int, keyword: str)
        """
        if self._running:
            raise RuntimeError("Detector is already running")
        self._running = True

        loop = asyncio.get_running_loop()
        # Start recorder in main thread
        self._recorder.start()

        try:
            while True:
                # Read and process in executor to avoid blocking
                pcm = await loop.run_in_executor(None, self._recorder.read)
                result = await loop.run_in_executor(None, self._porcupine.process, pcm)
                if result >= 0:
                    return result, self._keywords[result]
        finally:
            # Cleanup resources
            self._recorder.delete()
            self._porcupine.delete()
            self._running = False

    def close(self):
        """
        Forcefully stop and clean up resources.
        """
        if self._running:
            self._recorder.delete()
            self._porcupine.delete()
            self._running = False
