'''
lifecylce.py
Description: handles entry and exit of gui
Date Last Modified: Nov 24 2026
'''
import atexit, signal, sys
from PLUTO import stop_tx

_cleaned = False

def cleanup():
    global _cleaned
    if _cleaned:          # runs from up to 3 hooks, so make it idempotent
        return
    _cleaned = True
    try:
        stop_tx()
        print("\n[INFO] Transmitter successfully disabled.")
    except Exception as e:
        print(f"\n[ERROR] Failed to stop transmitter during shutdown: {e}")

def _handle_signal(sig, frame):
    cleanup()
    sys.exit(0)

def register(app):
    app.on_shutdown(cleanup)
    atexit.register(cleanup)
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)
