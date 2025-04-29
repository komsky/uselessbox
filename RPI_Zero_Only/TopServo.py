#!/usr/bin/python3

import RPi.GPIO as GPIO
import time

class TopServo:
    def __init__(self, servo_pin=19):
        self.servo_pin = servo_pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.servo_pin, GPIO.OUT)
        # 50 Hz is common for servos (20 ms period).
        self._pwm = GPIO.PWM(self.servo_pin, 50)
        self._pwm.start(0)  # Start with 0% duty cycle
        self.initiated = True

    def _check_initiated(self):
        if not self.initiated:
            raise Exception("Servo not initiated. Create a new instance of TopServo to initialize.")

    def _move(self, duty):
        self._check_initiated()
        self._pwm.ChangeDutyCycle(duty)
        time.sleep(0.5)  # Give servo time to move

    def zero(self):
        self.arc(0)
        self._pwm.ChangeDutyCycle(0)  # Stop sending power to avoid jitter

    def arc(self, angle):
        self._check_initiated()
        duty = 2.0 + (angle / 18.0)
        self._move(duty)

    def cleanup(self):
        if self.initiated:
            self._pwm.stop()
            GPIO.cleanup()
            self.initiated = False
