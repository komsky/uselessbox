from rpi_ws281x import PixelStrip, Color
import time
import threading

LED_COUNT = 11
LED_PIN = 12
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 64
LED_INVERT = False
LED_CHANNEL = 0

# Global PixelStrip instance and animation control
_strip = None
_current_animation = None
_animation_lock = threading.Lock()


def _init_strip():
    """Initialize the PixelStrip if not already done."""
    global _strip
    if _strip is None:
        _strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA,
                            LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
        _strip.begin()


def _set_all(color):
    """Helper to set all LEDs to a single color."""
    _init_strip()
    for i in range(_strip.numPixels()):
        _strip.setPixelColor(i, color)
    _strip.show()


def off():
    """Turn all LEDs off and stop any running animation."""
    _stop_animation()
    _set_all(Color(0, 0, 0))


def on():
    """Turn all LEDs on (warm white)."""
    _stop_animation()
    _set_all(Color(192, 128, 100))


def _stop_animation():
    """Internal: stop the current animation if running."""
    global _current_animation
    with _animation_lock:
        if _current_animation and _current_animation.is_alive():
            _current_animation.stop()
            _current_animation.join()
        _current_animation = None


def _start_animation(anim):
    """Internal: stop existing and start new animation thread."""
    global _current_animation
    with _animation_lock:
        _stop_animation()
        _current_animation = anim
        _current_animation.start()


class Animation(threading.Thread):
    """Base animation thread with stoppable event."""
    def __init__(self):
        super().__init__()
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    @property
    def stopped(self):
        return self._stop_event.is_set()

    def run(self):
        raise NotImplementedError


class ListeningAnimation(Animation):
    """Alexa-like blue pulsing ring."""
    def run(self):
        _init_strip()
        base_color = (0, 0, 50)
        max_brightness = 150
        step = 10
        brightness = base_color[2]
        direction = 1
        while not self.stopped:
            # pulse brightness
            brightness += direction * step
            if brightness >= max_brightness or brightness <= base_color[2]:
                direction *= -1
                brightness = max(base_color[2], min(brightness, max_brightness))
            _set_all(Color(base_color[0], base_color[1], brightness))
            time.sleep(0.05)


def listening():
    """Start listening animation."""
    anim = ListeningAnimation()
    _start_animation(anim)


class SpeakingAnimation(Animation):
    """Alexa-like color wave indicating speaking."""
    def run(self):
        _init_strip()
        colors = [Color(0, 0, 255), Color(0, 200, 255), Color(0, 150, 200)]
        idx = 0
        while not self.stopped:
            # wave across strip
            for i in range(_strip.numPixels()):
                if self.stopped: return
                color = colors[(idx + i) % len(colors)]
                _strip.setPixelColor(i, color)
            _strip.show()
            idx = (idx + 1) % len(colors)
            time.sleep(0.1)
        

def speaking():
    """Start speaking animation."""
    anim = SpeakingAnimation()
    _start_animation(anim)


class ThinkingAnimation(Animation):
    """Alexa-like slow rotating white dot."""
    def run(self):
        _init_strip()
        pos = 0
        length = _strip.numPixels()
        while not self.stopped:
            _set_all(Color(30, 30, 30))
            _strip.setPixelColor(pos, Color(255, 255, 255))
            _strip.show()
            pos = (pos + 1) % length
            time.sleep(0.2)


def thinking():
    """Start thinking animation."""
    anim = ThinkingAnimation()
    _start_animation(anim)


class KnightRiderAnimation(Animation):
    """KITT-style back-and-forth red scanner."""
    def run(self):
        _init_strip()
        length = _strip.numPixels()
        pos = 0
        direction = 1
        tail = 3
        while not self.stopped:
            # clear all
            _set_all(Color(0, 0, 0))
            # draw tail
            for t in range(tail):
                idx = pos - t * direction
                if 0 <= idx < length:
                    fade = int(255 * (1 - t / tail))
                    _strip.setPixelColor(idx, Color(fade, 0, 0))
            _strip.show()
            pos += direction
            if pos == length - 1 or pos == 0:
                direction *= -1
            time.sleep(0.05)


def knightrider():
    """Start Knight Rider animation."""
    anim = KnightRiderAnimation()
    _start_animation(anim)

if __name__ == "__main__":
    # Example usage
    print("Running example animations...")
    print("On")
    on()
    time.sleep(1)
    print("Off")
    off()
    time.sleep(1)
    print("Listening")
    listening()
    time.sleep(2)
    print("Speaking")
    speaking()
    time.sleep(2)
    print("Thinking")
    thinking()
    time.sleep(2)
    print("Knight Rider")
    knightrider()
    time.sleep(5)
    print("Off")
    off()
# Example usage:
# listening()
# time.sleep(5)
# speaking()
# time.sleep(5)
# thinking()
# time.sleep(5)
# knightrider()
