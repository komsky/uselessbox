import time
from gpiozero import AngularServo
# If you still want to use pigpio under the hood:
# from gpiozero.pins.pigpio import PiGPIOFactory
# factory = PiGPIOFactory()

class HandServo:
    def __init__(self, gpio_pin, 
                 min_pulse_width=0.0005, max_pulse_width=0.0025,
                 pulse_duration=0.5):
        """
        gpio_pin: BCM pin number
        min_pulse_width: seconds corresponding to 0�
        max_pulse_width: seconds corresponding to 180�
        pulse_duration: how long to drive the servo before ?releasing?
        """
        # To use pigpio as backend, add: , pin_factory=factory
        self.servo = AngularServo(
            gpio_pin,
            min_angle=0, max_angle=180,
            min_pulse_width=min_pulse_width,
            max_pulse_width=max_pulse_width
        )
        self._duration = pulse_duration
        self._inited = True

    def _check(self):
        if not self._inited:
            raise RuntimeError("Servo not initialized. Create a new HandServo instance.")

    def _move(self, angle: float):
        self._check()
        self.servo.angle = angle
        time.sleep(self._duration)
        # stop sending pulses (lets servo ?relax?)
        self.servo.angle = None

    def zero(self):
        self._move(0)

    def angle45(self):
        self._move(45)

    def angle90(self):
        self._move(90)

    def angle(self, angle: int):
        if not (0 <= angle <= 180):
            raise ValueError("Angle must be between 0 and 180")
        self._move(angle)

    def cleanup(self):
        if self._inited:
            self.servo.angle = None
            self.servo.close()
            self._inited = False
