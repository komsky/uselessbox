import sounddevice as sd
print(sd.query_devices())

for idx, dev in enumerate(sd.query_devices()):
    if dev['max_output_channels'] >= 2:
        print(idx, dev['name'])