'''
scan.py
Description:Hardware scan logic for receive mode: uploads the LUT to the MCU, turns on
the transmitter, steps through every array state, and returns the measured
tone power for each one. No UI code lives here.
Author: Kobe Prior
Date Last Modified: Nov 24, 2026
'''
import asyncio
import numpy as np

import helpers
from PLUTO import get_tone_energy, tx, stop_tx, discard_buffer
from create_default_rx_grid import ensure_default_rx_lut

N_SETTLE_BUFFERS = 5   # buffers discarded after each state change
N_AVG_SCAN = 3         # buffers averaged for each measurement
TX_STABILIZE_S = 1.0   # Tx power / local oscillator settling time


def _measure(i):
    '''Blocking: runs in a worker thread, never touches the UI.'''
    if not helpers.apply_lut(i):
        raise RuntimeError(f'MCU did not confirm array state {i}')
    for _ in range(N_SETTLE_BUFFERS):
        discard_buffer()
    return get_tone_energy(N_AVG_SCAN)


async def run_scan(on_progress=None):
    '''
    Run a full beam scan and return the raw power array (one entry per
    array state). Raises RuntimeError if the MCU rejects the LUT or a state.

    on_progress(done, total) is called after each measurement, from the
    event loop, so it is safe to update NiceGUI elements from it.
    '''
    rx_grid, ok = await asyncio.to_thread(ensure_default_rx_lut)
    if not ok:
        raise RuntimeError('MCU did not confirm LUT upload')

    n_steps = len(rx_grid)
    powers = np.zeros(n_steps)

    tx()
    try:
        await asyncio.sleep(TX_STABILIZE_S)
        for i in range(n_steps):
            powers[i] = await asyncio.to_thread(_measure, i)
            if on_progress is not None:
                on_progress(i + 1, n_steps)
    finally:
        stop_tx()

    return powers
