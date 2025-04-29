import lgpio
import time
import threading
import logging
from flask import Flask, Response, jsonify

# --- Configuration & Logging ---
logging.basicConfig(level=logging.INFO)
SWITCH_PIN = 17         # BCM pin 17 (adjust if needed)
CHIP = 0                # Default GPIO chip
DEBOUNCE_DELAY = 0.2    # Debounce delay in seconds

# --- lgpio Setup ---
h = lgpio.gpiochip_open(CHIP)
lgpio.gpio_claim_input(h, SWITCH_PIN, lgpio.SET_PULL_UP)
lgpio.gpio_claim_input(h, SWITCH_PIN)

# Read initial state; here 0 will represent "ON" (switch closed) and nonzero "OFF"
switch_state = lgpio.gpio_read(h, SWITCH_PIN)
logging.info("Initial switch state: %s", "ON" if switch_state == 0 else "OFF")

# --- Polling Thread to Detect Changes ---
def poll_switch():
    global switch_state
    last_state = switch_state
    while True:
        current_state = lgpio.gpio_read(h, SWITCH_PIN)
        if current_state != last_state:
            # Simple debounce: wait a bit and re-read
            time.sleep(DEBOUNCE_DELAY)
            stable_state = lgpio.gpio_read(h, SWITCH_PIN)
            if stable_state == current_state:
                switch_state = current_state
                last_state = current_state
                state_str = "ON" if current_state == 0 else "OFF"
                logging.info("Switch state changed: %s", state_str)
            else:
                # Bounce detected; update last_state without logging
                last_state = stable_state
        time.sleep(0.05)  # Poll every 50ms

poll_thread = threading.Thread(target=poll_switch, daemon=True)
poll_thread.start()

# --- Flask Application ---
app = Flask(__name__)

@app.route('/status')
def get_status():
    """Return the current switch status as JSON."""
    state_str = "ON" if switch_state == 0 else "OFF"
    return jsonify({"state": state_str})

@app.route('/events')
def stream_events():
    """Stream state changes using Server-Sent Events (SSE)."""
    def event_stream():
        last_event = switch_state
        while True:
            if switch_state != last_event:
                data = "ON" if switch_state == 0 else "OFF"
                yield f"data: {data}\n\n"
                last_event = switch_state
            time.sleep(0.1)  # Adjust polling interval as needed
    return Response(event_stream(), mimetype="text/event-stream")

if __name__ == '__main__':
    try:
        # Run Flask on all interfaces on port 5000
        app.run(host='0.0.0.0', port=5000, threaded=True)
    except KeyboardInterrupt:
        logging.info("Service interrupted by user")
    finally:
        lgpio.gpiochip_close(h)
