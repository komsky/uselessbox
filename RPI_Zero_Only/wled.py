#!/usr/bin/python3
"""
wled.py

Module for controlling a 35-LED WS2812b strip on GPIO 18.
"""

from rpi_ws281x import PixelStrip, Color
import threading
import time

# LED strip configuration:
LED_COUNT      = 35       # Number of LED pixels.
LED_PIN        = 18       # GPIO pin connected to the pixels (must support PWM).
LED_FREQ_HZ    = 800000   # LED signal frequency in hertz (usually 800kHz)
LED_DMA        = 10       # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255      # Brightness (0 to 255)
LED_INVERT     = False    # True to invert the signal (if using NPN transistor level shift)
LED_CHANNEL    = 0

# Global PixelStrip instance.
_strip = None

def _init_strip():
    """Initialize the PixelStrip if not already done."""
    global _strip
    if _strip is None:
        _strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA,
                            LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
        _strip.begin()

def on():
    """Turn all LEDs on (green)."""
    _init_strip()
    for i in range(_strip.numPixels()):
        _strip.setPixelColor(i, Color(128, 72, 0))  # Green
    _strip.show()

def off():
    """Turn all LEDs off."""
    _init_strip()
    for i in range(_strip.numPixels()):
        _strip.setPixelColor(i, Color(0, 0, 0))
    _strip.show()

# Global variables for managing the strobe effect.
_angry_thread = None
_angry_stop_event = threading.Event()

def angry():
    """Start angry strobe flashes asynchronously."""
    global _angry_thread, _angry_stop_event
    _init_strip()
    # If already flashing, do nothing.
    if _angry_thread is not None and _angry_thread.is_alive():
        return

    # Clear the stop event and start the flashing loop.
    _angry_stop_event.clear()

    def flash_loop():
        while not _angry_stop_event.is_set():
            # Turn all LEDs red for a fast strobe effect.
            for i in range(_strip.numPixels()):
                _strip.setPixelColor(i, Color(255, 0, 0))
            _strip.show()
            time.sleep(0.05)  # On duration.
            # Turn off all LEDs.
            for i in range(_strip.numPixels()):
                _strip.setPixelColor(i, Color(0, 0, 0))
            _strip.show()
            time.sleep(0.05)  # Off duration.

    _angry_thread = threading.Thread(target=flash_loop)
    _angry_thread.start()

def down():
    """Stop the angry strobe effect and turn off the LEDs."""
    global _angry_thread, _angry_stop_event
    _angry_stop_event.set()
    if _angry_thread is not None:
        _angry_thread.join()
        _angry_thread = None
    off()
