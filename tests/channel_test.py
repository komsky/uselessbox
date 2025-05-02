import numpy as np, sounddevice as sd

fs = 48000
t = np.linspace(0, 1, int(fs), endpoint=False)
tone = (0.2 * np.sin(2*np.pi*440*t)).astype(np.float32)

# shape (frames,2): left only
stereo = np.column_stack((tone, np.zeros_like(tone)))

# send straight to hw:1,0 (bypass dmix)
sd.default.device = (None, 'hw:1,0')
sd.play(stereo, fs)
sd.wait()
