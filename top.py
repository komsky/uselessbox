#!/usr/bin/env python3
from gpiozero import AngularServo
from time import sleep

from servo_base import get_pin_factory

TOP_ARC = 40

class TopServo:
    def __init__(
        self,
        servo_pin: int = 27,   # BCM pin
        min_angle: float = 0,
        max_angle: float = 180,
        min_pulse_width: float = 0.0005,
        max_pulse_width: float = 0.0025,
        frame_width: float = 0.02
    ):
        # save parameters so StartServo can see them
        self.servo_pin = servo_pin
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.min_pulse_width = min_pulse_width
        self.max_pulse_width = max_pulse_width
        self.frame_width = frame_width

        self.servo = None
        # pigpio gives hardware-timed pulses: a held servo doesn't jitter. Without it
        # we must not hold (software PWM jitters), so we fall back to detach-after-move
        # and the heavy lid sags a little — sag beats jitter.
        self._pin_factory = get_pin_factory()
        self._can_hold = self._pin_factory is not None

    def StartServo(self) -> AngularServo:
        if self.servo is None:
            self.servo = AngularServo(
                pin=self.servo_pin,
                min_angle=self.min_angle,
                max_angle=self.max_angle,
                min_pulse_width=self.min_pulse_width,
                max_pulse_width=self.max_pulse_width,
                frame_width=self.frame_width,
                pin_factory=self._pin_factory
            )
        return self.servo

    def arc(self, angle: float, hold: bool = False) -> None:
        servo = self.StartServo()
        if not (servo.min_angle <= angle <= servo.max_angle):
            raise ValueError(f"Angle must be between {servo.min_angle} and {servo.max_angle}")
        servo.angle = angle
        if hold and self._can_hold:
            sleep(0.2)  # let it reach the target; stays attached, keeps torque
        else:
            sleep(0.4)  # settle fully before losing torque
            servo.detach()

    def up(self) -> None:
        """Open the box and keep holding the heavy lid up."""
        self.arc(TOP_ARC, hold=True)

    def down(self) -> None:
        """Closing the box"""
        self.zero()

    def zero(self) -> None:
        """Move to min_angle and detach — a closed lid needs no torque."""
        self.arc(self.min_angle)

    def cleanup(self) -> None:
        """Release the GPIO pin and stop PWM."""
        if self.servo is not None:
            self.servo.close()

def main():
    servo = TopServo()
    try:
        servo.arc(TOP_ARC)
        sleep(2)

        print("Resetting to zero and detaching.")
        servo.zero()
        # ask for arc angle in a loop and move the servo, then zero
        while True:
            try:
                angle = float(input(f"Enter angle between {servo.min_angle} and {servo.max_angle}: "))
                servo.arc(angle)
                sleep(1)
                print("3 ...")
                sleep(1)
                print("2 ...")
                sleep(1)
                print("1 ...")
                sleep(1)
                print("Zeroing servo.")
                servo.zero()
            except ValueError as e:
                print(f"Invalid input: {e}")
            except KeyboardInterrupt:
                break
    finally:
        servo.cleanup()
        print("Cleaned up GPIO and exiting.")


if __name__ == "__main__":
    main()
