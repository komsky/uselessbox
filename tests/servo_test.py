from gpiozero import Servo
from time import sleep
from gpiozero.pins.pigpio import PiGPIOFactory

# Connect via pigpio backend
factory = PiGPIOFactory()
servo = Servo(22, pin_factory=factory)  # GPIO27 = Pin 13

try:
    servo.value = 0.05
    sleep(1)
    servo.min()

except KeyboardInterrupt:
    print("Stopped")
