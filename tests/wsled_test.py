from rpi_ws281x import PixelStrip, Color
import time

LED_COUNT=8
LED_PIN=18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 64
LED_INVERT = False
LED_CHANNEL = 0

strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

def color_wipe(color, wait_ms=50):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms / 1000.0)

try:
    while True:
        color_wipe(Color(255, 0, 0))  # Red
        color_wipe(Color(0, 255, 0))  # Green
        color_wipe(Color(0, 0, 255))  # Blue
except KeyboardInterrupt:
    color_wipe(Color(0, 0, 0), 10)
