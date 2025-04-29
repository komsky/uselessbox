#!/usr/bin/python3

import time
from HandServo import HandServo
from TopServo import TopServo
import requests
import wled
import random

EVENTS_URL = "http://127.0.0.1:5000/events"
handServo = HandServo(gpio_pin=27)
topServo = TopServo(servo_pin=19)

def randomAction():
    # Generate a random integer between 1 and 10
    num = random.randint(1, 10)
    print(f"Random number generated: {num}")

    # Switch-like structure using match-case
    match num:
        case 1:
            # Action for case 1
            print("Action for 1")
            topServo.arc(35)
        case 2:
            # Action for case 2
            print("Action for 2")
        case 3:
            # Action for case 3
            print("Action for 3")
        case 4:
            # Action for case 4
            print("Action for 4")
        case 5:
            # Action for case 5
            print("Action for 5")
        case 6:
            # Action for case 6
            print("Action for 6")
        case 7:
            # Action for case 7
            print("Action for 7")
        case 8:
            # Action for case 8
            print("Action for 8")
        case 9:
            # Action for case 9
            print("Action for 9")
        case 10:
            # Action for case 10
            print("Action for 10")
        case _:
            # Default action (should not occur in this example)
            print("Default action")


def subscribe_events():
    while True:
        try:
            print("Connecting to events endpoint at", EVENTS_URL)
            with requests.get(EVENTS_URL, stream=True) as r:
                for line in r.iter_lines(decode_unicode=True):
                    if line and line.startswith("data:"):
                        data = line.replace("data:", "").strip()
                        print("Received event:", data)

                        if data == "ON":
                            wled.on()
                            time.sleep(1)
                            topServo.arc(50)
                            time.sleep(1)
                            #wled.angry()  # example: move servo to 90 degrees
                            handServo.angle(80)
                            time.sleep(0.5)
                            handServo.zero()

                        elif data == "OFF":
                            wled.off()
                            topServo.zero()   # reset servo to 0 degrees
                            time.sleep(1)
                            topServo.arc(30)
                            handServo.angle(20)
                            time.sleep(0.5)
                            handServo.zero()
                            time.sleep(1.5)
                            topServo.zero()

        except Exception as e:
            print("Error while subscribing to events:", e)
            time.sleep(5)  # retry after a delay

if __name__ == '__main__':
    try:
        subscribe_events()
    except KeyboardInterrupt:
        print("Exiting box.py")
    finally:
        topServo.cleanup()  # optional, to ensure GPIO is cleaned up on exit
