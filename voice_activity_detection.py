import logging
import collections
import numpy as np
import webrtcvad
from AudioModule import Audio

logging.basicConfig(level=20)

class VADAudio(Audio):
    """Filter & segment stereo audio with voice activity detection."""

    def __init__(self, aggressiveness=3, device=None, input_rate=None, file=None):
        # force Audio to open as stereo
        self.CHANNELS = 2
        super().__init__(device=device, input_rate=input_rate, file=file)
        self.vad = webrtcvad.Vad(aggressiveness)

    def frame_generator(self):
        """Yields raw stereo frames from mic (or file)."""
        read_fn = self.read if self.input_rate == self.RATE_PROCESS else self.read_resampled
        while True:
            yield read_fn()

    def _downmix(self, frame_bytes):
        samples = np.frombuffer(frame_bytes, dtype=np.int16).reshape(-1, 2)

        # OPTION A: just use left channel
        # mono = samples[:,0]  # left channel
        #mono = samples[:,1]  # right channel
        #print("mono peak:", mono.max(), "? if this stays very low (e.g. <1000), VAD won?t fire")
        # OPTION B: sum channels (with int32 headroom), then clip to int16
        s = samples.astype(np.int32).sum(axis=1)
        mono = np.clip(s, -32768, 32767).astype(np.int16)
        return mono.astype(np.int16).tobytes()

    def vad_collector(self, padding_ms=200, ratio=0.5, frames=None):
        """Yields original stereo frames, splitting on speech/no-speech."""
        if frames is None:
            frames = self.frame_generator()

        num_padding = padding_ms // self.frame_duration_ms
        ring_buffer = collections.deque(maxlen=num_padding)
        triggered = False

        # how many bytes per raw stereo frame?
        bytes_per_frame = self.block_size * self.CHANNELS * 2

        for frame in frames:
            #print("got frame bytes:", len(frame))
            if len(frame) < bytes_per_frame:
                return

            # downmix for VAD
            mono_frame = self._downmix(frame)
            #print("downmixed frame bytes:", len(mono_frame))
            is_speech = self.vad.is_speech(mono_frame, self.sample_rate)

            if not triggered:
                ring_buffer.append((frame, is_speech))
                num_voiced = sum(1 for f, speech in ring_buffer if speech)
                if num_voiced > ratio * ring_buffer.maxlen:
                    triggered = True
                    # emit all buffered *stereo* frames
                    for f, _ in ring_buffer:
                        yield f
                    ring_buffer.clear()
            else:
                yield frame
                ring_buffer.append((frame, is_speech))
                num_unvoiced = sum(1 for f, speech in ring_buffer if not speech)
                if num_unvoiced > ratio * ring_buffer.maxlen:
                    triggered = False
                    yield None
                    ring_buffer.clear()
