#!/usr/bin/env python3
import os

from gpiozero import AngularServo
from time import sleep

from servo_base import get_pin_factory

TOP_ARC = 40

# Hardware-PWM mode: created once the servo signal wire is moved to GPIO12 (the
# ReSpeaker Grove socket) and `dtoverlay=pwm,pin=12,func=4` is booted. Hardware
# pulses are timer-generated — a held servo is rock steady (software PWM on the
# loaded Zero 2 shakes the lid violently), and the PWM peripheral is independent
# of the I2S audio, unlike pigpiod's DMA.
HW_PWM_FLAG = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".top_hw_pwm")


class _HardwarePWMBackend:
    """Top-servo driver on PWM0/GPIO12 via the kernel's hardware PWM."""

    def __init__(self, min_pulse_s=0.0005, max_pulse_s=0.0025,
                 min_angle=0.0, max_angle=180.0, frame_s=0.02):
        from rpi_hardware_pwm import HardwarePWM
        self._min_pulse_s = min_pulse_s
        self._max_pulse_s = max_pulse_s
        self._min_angle = min_angle
        self._max_angle = max_angle
        self._frame_s = frame_s
        chip = int(os.getenv("TOP_HW_PWM_CHIP", "0"))
        self._pwm = HardwarePWM(pwm_channel=0, hz=round(1 / frame_s), chip=chip)
        self._running = False

    def _duty_for(self, angle: float) -> float:
        span = self._max_angle - self._min_angle
        pulse = self._min_pulse_s + ((angle - self._min_angle) / span) * (
            self._max_pulse_s - self._min_pulse_s)
        return pulse / self._frame_s * 100.0

    def set_angle(self, angle: float) -> None:
        duty = self._duty_for(angle)
        if self._running:
            self._pwm.change_duty_cycle(duty)
        else:
            self._pwm.start(duty)
            self._running = True

    def detach(self) -> None:
        if self._running:
            self._pwm.stop()
            self._running = False

    def close(self) -> None:
        self.detach()

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
        # The heavy lid falls the moment the servo detaches (field-tested: it nearly
        # closes itself and blocks the hand), so the lid is HELD for the whole open
        # phase and released only after closing. The hold source, best first:
        #   1. Hardware PWM on GPIO12 (flag file present, wire moved) — zero jitter.
        #   2. pigpio, if ever available (NOT on this box: its DMA wedges I2S audio).
        #   3. Default software PWM — holds, but shakes hard under CPU load.
        self._hw = None
        if os.path.exists(HW_PWM_FLAG):
            try:
                self._hw = _HardwarePWMBackend(
                    min_pulse_s=min_pulse_width, max_pulse_s=max_pulse_width,
                    min_angle=min_angle, max_angle=max_angle, frame_s=frame_width)
                print("top: hardware PWM backend active (GPIO12)")
            except Exception as exc:
                print(f"top: hardware PWM flagged but unavailable ({exc}); using gpiozero")
        self._pin_factory = get_pin_factory() if self._hw is None else None

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
        if not (self.min_angle <= angle <= self.max_angle):
            raise ValueError(f"Angle must be between {self.min_angle} and {self.max_angle}")
        if self._hw is not None:
            self._hw.set_angle(angle)
            sleep(0.4)  # reach the target
            if not hold:
                self._hw.detach()
            return
        # Software-PWM hold is BANNED: field-tested on the loaded Zero 2 it shakes the
        # box violently ("earthquake", nearly off the table). Until the servo wire is
        # on GPIO12 (hardware PWM), we always detach and accept the lid sag.
        servo = self.StartServo()
        servo.angle = angle
        sleep(0.4)  # reach the target / settle
        servo.detach()

    def up(self) -> None:
        """Open the box and hold the heavy lid up until down()/zero()."""
        self.arc(TOP_ARC, hold=True)

    def down(self) -> None:
        """Closing the box"""
        self.zero()

    def zero(self) -> None:
        """Move to min_angle and detach — a closed lid needs no torque."""
        self.arc(self.min_angle)

    def cleanup(self) -> None:
        """Release the GPIO pin and stop PWM."""
        if self._hw is not None:
            self._hw.close()
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
