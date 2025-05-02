import board
import neopixel
import time

# NeoPixel strip configuration:
LED_COUNT = 11        # Number of LEDs in the strip
LED_PIN = 23  # GPIO23

# Initialize NeoPixel object
pixels = neopixel.NeoPixel(LED_PIN, LED_COUNT, brightness=0.3, auto_write=False)

def color_wipe(color, wait):
    for i in range(LED_COUNT):
        pixels[i] = color
        pixels.show()
        time.sleep(wait)

try:
    while True:
        color_wipe((255, 0, 0), 0.1)  # Red
        color_wipe((0, 255, 0), 0.1)  # Green
        color_wipe((0, 0, 255), 0.1)  # Blue
except KeyboardInterrupt:
    pixels.fill((0, 0, 0))
    pixels.show()
