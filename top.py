#!/usr/bin/env python3
import threading

from gpiozero import AngularServo
from time import sleep

from servo_base import get_pin_factory

TOP_ARC = 40
NUDGE_INTERVAL_S = 8.0  # while the box is open, re-command the sagging lid this often

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
        # pigpio gives hardware-timed pulses: a held servo doesn't jitter. BUT on this
        # box pigpiod must NOT run: its DMA setup wedges the ReSpeaker's I2S audio until
        # reboot (mic dies with "Failed to read from device"). So on this hardware we
        # never hold attached; instead a nudger thread re-commands the raised lid every
        # NUDGE_INTERVAL_S — a 0.3s correction, not continuous PWM, so no jitter.
        self._pin_factory = get_pin_factory()
        self._can_hold = self._pin_factory is not None
        self._nudger = None
        self._nudge_stop = threading.Event()

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

    def _nudge_loop(self) -> None:
        while not self._nudge_stop.wait(NUDGE_INTERVAL_S):
            try:
                servo = self.StartServo()
                servo.angle = TOP_ARC
                sleep(0.3)
                servo.detach()
            except Exception:
                break

    def _start_nudger(self) -> None:
        if self._nudger is not None and self._nudger.is_alive():
            return
        self._nudge_stop.clear()
        self._nudger = threading.Thread(target=self._nudge_loop, daemon=True)
        self._nudger.start()

    def _stop_nudger(self) -> None:
        self._nudge_stop.set()
        if self._nudger is not None and self._nudger.is_alive():
            self._nudger.join(timeout=1.0)
        self._nudger = None

    def up(self) -> None:
        """Open the box and keep the heavy lid up (hold or periodic nudge)."""
        self._stop_nudger()
        self.arc(TOP_ARC, hold=True)
        if not self._can_hold:
            self._start_nudger()

    def down(self) -> None:
        """Closing the box"""
        self.zero()

    def zero(self) -> None:
        """Move to min_angle and detach — a closed lid needs no torque."""
        self._stop_nudger()
        self.arc(self.min_angle)

    def cleanup(self) -> None:
        """Release the GPIO pin and stop PWM."""
        self._stop_nudger()
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
