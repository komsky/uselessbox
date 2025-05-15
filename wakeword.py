import os
import argparse
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

    The wait_for_wakeword() method can be called in a loop ? each call reinitializes audio resources and cleans up afterward.
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
        # Store configuration ? actual Porcupine and recorder are initialized per call
        self.access_key = access_key
        self.keyword_paths = keyword_paths
        self.sensitivities = sensitivities or [0.5] * len(keyword_paths)
        if len(self.sensitivities) != len(self.keyword_paths):
            raise ValueError("Number of sensitivities must match number of keywords.")

        self.library_path = library_path
        self.model_path = model_path
        self.device_index = device_index

        # Precompute human-readable phrases from keyword paths
        self._keywords = []
        for path in keyword_paths:
            name = os.path.basename(path).replace('.ppn', '').split('_')
            phrase = ' '.join(name[:-6]) if len(name) > 6 else name[0]
            self._keywords.append(phrase)

    async def wait_for_wakeword(self):
        """
        Start listening and return upon detecting a wake word.

        Returns:
            (keyword_index: int, keyword: str)

        This method initializes its own Porcupine and recorder instances,
        so it can be called repeatedly in a loop with clean resource management.
        """
        # Initialize Porcupine and recorder
        porcupine = pvporcupine.create(
            access_key=self.access_key,
            keyword_paths=self.keyword_paths,
            sensitivities=self.sensitivities,
            library_path=self.library_path,
            model_path=self.model_path,
        )
        recorder = PvRecorder(
            frame_length=porcupine.frame_length,
            device_index=self.device_index
        )

        loop = asyncio.get_running_loop()
        recorder.start()

        try:
            while True:
                # Read from microphone (blocking) in executor
                pcm = await loop.run_in_executor(None, recorder.read)
                # Process audio in executor
                result = await loop.run_in_executor(None, porcupine.process, pcm)

                if result >= 0:
                    # Detected keyword: return index and phrase
                    return result, self._keywords[result]
        finally:
            # Always cleanup resources, even if cancelled or error
            recorder.delete()
            porcupine.delete()


def main():
    parser = argparse.ArgumentParser(description="Run WakeWordDetector standalone.")
    parser.add_argument(
        '--access_key', required=True,
        help='Picovoice AccessKey from https://console.picovoice.ai/'
    )
    parser.add_argument(
        '--keyword_paths', required=True, nargs='+',
        help='Paths to Porcupine keyword (.ppn) files'
    )
    parser.add_argument(
        '--sensitivities', nargs='+', type=float,
        help='Sensitivities for each keyword (0 to 1). Defaults to 0.5 each.'
    )
    parser.add_argument(
        '--library_path', help='Absolute path to Porcupine dynamic library.'
    )
    parser.add_argument(
        '--model_path', help='Absolute path to model parameters file.'
    )
    parser.add_argument(
        '--audio_device_index', type=int, default=-1,
        help='Index of input audio device. Default: -1 (system default).'
    )

    args = parser.parse_args()

    detector = WakeWordDetector(
        access_key=args.access_key,
        keyword_paths=args.keyword_paths,
        sensitivities=args.sensitivities,
        library_path=args.library_path,
        model_path=args.model_path,
        device_index=args.audio_device_index
    )

    print("Listening for wake word... Press Ctrl+C to exit.")
    try:
        index, keyword = asyncio.run(detector.wait_for_wakeword())
        print(f"[{datetime.now()}] Detected '{keyword}' (index: {index})")
    except KeyboardInterrupt:
        print("Interrupted by user.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # No persistent resources to close here
        pass


if __name__ == '__main__':
    main()
