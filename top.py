#!/usr/bin/env python3
from gpiozero import AngularServo
from time import sleep

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

    def StartServo(self) -> AngularServo:
        if self.servo is None:
            self.servo = AngularServo(
                pin=self.servo_pin,
                min_angle=self.min_angle,
                max_angle=self.max_angle,
                min_pulse_width=self.min_pulse_width,
                max_pulse_width=self.max_pulse_width,
                frame_width=self.frame_width
            )
        return self.servo

    def arc(self, angle: float) -> None:
        servo = self.StartServo()                # <-- use self.StartServo()
        if not (servo.min_angle <= angle <= servo.max_angle):
            raise ValueError(f"Angle must be between {servo.min_angle} and {servo.max_angle}")
        servo.angle = angle
        sleep(0.2) 
        servo.detach() 

    def up(self) -> None:
        """Opening the box"""
        self.arc(TOP_ARC)    
    def down(self) -> None:
        """Closing the box"""
        self.zero()

    def zero(self) -> None:
        """Move to min_angle and detach."""
        self.arc(self.min_angle)
        sleep(0.2)  #ensure the servo has time to move
        self.servo.detach()

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
