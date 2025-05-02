import pigpio
import time

class HandServo:
    def __init__(self, gpio_pin):

        self.gpio_pin = gpio_pin
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise IOError("Could not connect to pigpio daemon. Make sure pigpiod is running.")
        self.pi.set_mode(gpio_pin, pigpio.OUTPUT)
        
        # Define servo pulse widths in microseconds (adjust based on your servo's calibration)
        self.pw_zero = 500    # Position for 0° (default)
        self.pw_45 = 1000     # Position for 45°
        self.pw_90 = 1500     # Position for 90°

        self.min_pulse = 500    # 0° -> 500µs
        self.max_pulse = 2500   # 180° -> 2500µs
        self.initiated = True

    def _check_initiated(self):
        if not self.initiated:
            raise Exception("Servo not initiated. Create a new instance of HandServo to initialize.")

    def _set_pulse_and_stop(self, pulse):
        self.pi.set_servo_pulsewidth(self.gpio_pin, pulse)
        time.sleep(0.5)  # Wait for servo movement
        self.pi.set_servo_pulsewidth(self.gpio_pin, 0)  # Stop the pulse

    def zero(self):
        self._check_initiated()
        self._set_pulse_and_stop(self.pw_zero)

    def angle45(self):
        self._check_initiated()
        self._set_pulse_and_stop(self.pw_45)

    def angle90(self):
        self._check_initiated()
        self._set_pulse_and_stop(self.pw_90)
        
    def angle(self, angle: int):
        self._check_initiated()
        if not (0 <= angle <= 180):
            raise ValueError("Angle must be between 0 and 180")
        pulse = self.min_pulse + (angle / 180.0) * (self.max_pulse - self.min_pulse)
        self._set_pulse_and_stop(pulse)

    def cleanup(self):
        if self.pi is not None:
            self.pi.set_servo_pulsewidth(self.gpio_pin, 0)
            self.pi.stop()
            self.initiated = False
