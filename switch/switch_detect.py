import lgpio
import time

SWITCH_PIN = 23  # BCM pin 17
CHIP = 0         # Default GPIO chip

h = lgpio.gpiochip_open(CHIP)
lgpio.gpio_claim_input(h, SWITCH_PIN, lgpio.SET_PULL_UP)

last_state = lgpio.gpio_read(h, SWITCH_PIN)
print("Initial switch state:", "ON" if last_state == 0 else "OFF")

try:
    while True:
        current_state = lgpio.gpio_read(h, SWITCH_PIN)
        if current_state != last_state:
            print("Switch state changed:", "ON" if current_state == 0 else "OFF")
            last_state = current_state
        time.sleep(0.05)  # check every 50ms

except KeyboardInterrupt:
    print("\nExiting...")
    lgpio.gpiochip_close(h)
