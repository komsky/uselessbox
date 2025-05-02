#!/usr/bin/env python3

from gpiozero import AngularServo
from time import sleep

class TopServo:
    def __init__(
        self,
        servo_pin: int = 19,
        min_angle: float = 0,
        max_angle: float = 180,
        min_pulse_width: float = 0.0005,
        max_pulse_width: float = 0.0025,
        frame_width: float = 0.02
    ):
        # gpiozero uses BCM numbering by default
        self.servo = AngularServo(
            pin=servo_pin,
            min_angle=min_angle,
            max_angle=max_angle,
            min_pulse_width=min_pulse_width,
            max_pulse_width=max_pulse_width,
            frame_width=frame_width
        )

    def arc(self, angle: float) -> None:
        """Move to a specific angle (in degrees)."""
        if not (self.servo.min_angle <= angle <= self.servo.max_angle):
            raise ValueError(f"Angle must be between {self.servo.min_angle} and {self.servo.max_angle}")
        self.servo.angle = angle
        sleep(0.5)

    def zero(self) -> None:
        """Move to zero position, then detach to stop jitter."""
        self.arc(self.servo.min_angle)
        self.servo.detach()

    def cleanup(self) -> None:
        """Release the GPIO pin and stop PWM."""
        self.servo.close()
