#!/usr/bin/env python3
"""Shared servo pin-factory selection.

With the default gpiozero factory, servo pulses are software-timed: holding a
servo attached makes it jitter audibly. pigpio generates hardware-timed pulses
(DMA), so a held servo stays rock steady — that's what lets the top servo keep
torque on the heavy lid while it's open. Requires the pigpiod daemon.
"""


def get_pin_factory():
    """Return a PiGPIOFactory when pigpiod is reachable, else None (default factory).

    None also signals callers that holding a servo attached would jitter, so
    they should fall back to detach-after-move.
    """
    try:
        from gpiozero.pins.pigpio import PiGPIOFactory
        factory = PiGPIOFactory()
        # Constructor may succeed lazily; verify the daemon connection is live.
        conn = getattr(factory, "connection", None)
        if conn is not None and not conn.connected:
            raise RuntimeError("pigpiod not connected")
        return factory
    except Exception as exc:
        print(f"servo_base: pigpio unavailable ({exc}); using default pin factory")
        return None
