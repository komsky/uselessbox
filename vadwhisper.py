import logging
import collections
import numpy as np
import webrtcvad
import wave
import os
from datetime import datetime
from AudioModule import Audio
from openai import OpenAI

logging.basicConfig(level=logging.INFO)


class VADAudio(Audio):
    """
    Filter & segment stereo audio with voice activity detection.
    Designed for 2-channel mics (e.g., ReSpeaker HAT).

    Yields contiguous speech frames as raw PCM bytes (mono, 16kHz, 16-bit).
    """

    def __init__(
        self,
        aggressiveness: int = 3,
        device=0,
        input_rate: int = 16000,
        file: str = None,
        frame_duration_ms: int = 30,
        padding_duration_ms: int = 300,
        ratio: float = 0.75,
    ):
        super().__init__(device=device, input_rate=input_rate, file=file)
        # Fallbacks if base class leaves these unset

        self.vad = webrtcvad.Vad(aggressiveness)
        # Core VAD parameters
        self._frame_duration_ms = frame_duration_ms
        self._padding_ms = padding_duration_ms
        self._ratio = ratio
        # calculate frame size in bytes: samples_per_frame * bytes_per_sample * channels
        samples_per_frame = int(input_rate * frame_duration_ms / 1000)
        self._frame_size = samples_per_frame * 2 * 2
        # override base if needed
        self.sample_rate = input_rate
        self.channels = 2

    def _frame_generator(self):
        """Yields raw frames from the audio source."""
        read_fn = self.read if self.input_rate == self.RATE_PROCESS else self.read_resampled
        while True:
            data = read_fn()
            if not data:
                break
            yield data

    def _downmix(self, stereo_bytes: bytes) -> bytes:
        """Downmix stereo bytes to mono by averaging channels."""
        samples = np.frombuffer(stereo_bytes, dtype=np.int16).reshape(-1, self.channels)
        mono = samples.mean(axis=1).astype(np.int16)
        return mono.tobytes()

    def vad_collector(self):
        """Generator yielding speech segments (mono PCM bytes)."""
        frames = self._frame_generator()
        num_padding = int(self._padding_ms / self._frame_duration_ms)
        ring_buffer = collections.deque(maxlen=num_padding)
        triggered = False

        for frame in frames:
            if len(frame) < self._frame_size:
                break
            mono = self._downmix(frame)
            is_speech = self.vad.is_speech(mono, self.sample_rate)

            if not triggered:
                ring_buffer.append((frame, mono, is_speech))
                num_voiced = sum(1 for _, _, speech in ring_buffer if speech)
                if num_voiced > self._ratio * ring_buffer.maxlen:
                    triggered = True
                    # yield buffered mono frames
                    for _, m, _ in ring_buffer:
                        yield m
                    ring_buffer.clear()
            else:
                yield mono
                ring_buffer.append((frame, mono, is_speech))
                num_unvoiced = sum(1 for _, _, speech in ring_buffer if not speech)
                if num_unvoiced > self._ratio * ring_buffer.maxlen:
                    triggered = False
                    # end of utterance
                    yield None
                    ring_buffer.clear()

    def write_wav(self, path: str, pcm_bytes: bytes):
        """Write mono WAV file from PCM bytes."""
        with wave.open(path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(pcm_bytes)

    def close(self):
        super().close()
        self.vad = None


def transcribe_with_whisper(wav_path: str, language: str = None) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable not set")
    client = OpenAI(api_key=api_key)
    with open(wav_path, 'rb') as audio_file:
        resp = client.audio.transcriptions.create(
            file=audio_file,
            model='whisper-1',
            language=language,
            temperature=0.0,
            response_format='text'
        )
    return resp['text']


def record_and_transcribe(
    aggressiveness: int =3,
    device=0,
    input_rate=16000,
    language: str = None,
    save_dir: str = '.'
) -> str:
    vad = VADAudio(
        aggressiveness=aggressiveness,
        device=device,
        input_rate=input_rate
    )
    logging.info("Please speak now...")
    wav_data = bytearray()
    for segment in vad.vad_collector():
        if segment is None:
            break
        wav_data.extend(segment)
    logging.info("Recording complete.")

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    wav_path = os.path.join(save_dir, f'command_{timestamp}.wav')
    vad.write_wav(wav_path, wav_data)
    logging.info(f"Saved utterance to {wav_path}")

    # Transcribe and then delete file
    text = transcribe_with_whisper(wav_path, language)
    logging.info(f"Transcription: {text}")
    try:
        os.remove(wav_path)
        logging.info(f"Deleted temporary file {wav_path}")
    except OSError as e:
        logging.warning(f"Could not delete wav file: {e}")

    return text


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Record via VAD and transcribe with Whisper")
    parser.add_argument('--aggressiveness', type=int, default=3, help='VAD aggressiveness (0-3)')
    parser.add_argument('--device', type=int, default=0, help='Audio device index')
    parser.add_argument('--input_rate', type=int, default=16000, help='Sampling rate')
    parser.add_argument('--language', type=str, default=None, help='Whisper language code')
    parser.add_argument('--save_dir', type=str, default='.', help='Directory to store temp WAV files')
    args = parser.parse_args()

    try:
        text = record_and_transcribe(
            aggressiveness=args.aggressiveness,
            device=args.device,
            input_rate=args.input_rate,
            language=args.language,
            save_dir=args.save_dir
        )
        print(f"You said: {text}")
    except Exception as e:
        logging.error(e)


if __name__ == '__main__':
    main()