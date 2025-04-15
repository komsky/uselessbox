#!/usr/bin/python3
"""
servo_top.py

Module for controlling a servo connected to GPIO 19 using RPi.GPIO.
Defines two methods:
- zero() : reset the servo to 0 degrees
- arc(angle) : move the servo to a given angle (0-180)
"""

import RPi.GPIO as GPIO
import time

SERVO_PIN = 19

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO_PIN, GPIO.OUT)

# 50 Hz is common for servos (20 ms period).
# Duty cycle range ~2% (0 degrees) to ~12% (180 degrees) depends on your servo.
_pwm = GPIO.PWM(SERVO_PIN, 50)  
_pwm.start(0)  # start with 0% duty cycle

def zero():
    """Move servo to 0 degrees."""
    arc(0)

def arc(angle):
    """
    Move servo to a given angle between 0 and 180.
    The duty cycle formula can vary by servo; adjust as needed.
    """
    # Simple formula: 2% duty = 0 deg, 12% duty = 180 deg
    duty = 2.0 + (angle / 18.0)  # angle/18 -> 10 range from 0-180, plus base 2
    _pwm.ChangeDutyCycle(duty)
    time.sleep(0.5)  # give servo time to move
    # Optional: set to 0 to stop sending power if you prefer
    _pwm.ChangeDutyCycle(0)

def cleanup():
    """Stop PWM and clean up GPIO."""
    _pwm.stop()
    GPIO.cleanup()
