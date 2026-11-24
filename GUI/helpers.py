'''
Purpose: Contains helper functions to interface with the microcontroller, 
and the graphical user interface
Author: Kobe Prior
Last Modified: July 17, 2026
'''
import asyncio
import json
import os
import numpy as np
import serial
from nicegui import ui

import state
from config import BAUDRATE, CP_PHASES
from READ_S2P import get_phase_at_freq
from PLUTO import stop_tx

async def set_com_port(port: str):
    state.SELECTED_COM_PORT = port
    try:
        state.ser = serial.Serial(
            state.SELECTED_COM_PORT, 
            BAUDRATE, 
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE, 
            stopbits=serial.STOPBITS_ONE, 
            timeout=1
        )
        await asyncio.sleep(3)  # Allow Arduino to reset
        state.LUT_BYTES = None
        if uart_self_test():
            print(f'UART link verified on {port}')
        else:
            print(f'No ACK from MCU on {port} - check wiring/reset')

    except Exception as e:
        print(f'Failed to open serial port: {e}')

##--------- MCU Interfacing -----------------------------------
CMD_SET, CMD_LOAD_LUT, CMD_APPLY = 0x01, 0x02, 0x03
ACK, NACK = 0xAA, 0xEE
MAX_LUT = 32   # must match the firmware

def _to_hardware(phases: np.ndarray, include_cp: bool = True) -> np.ndarray:
    total = phases + state.PHASE_OFFSETS
    if include_cp and state.CP_ARRAY:
        total = total + CP_PHASES
    steps = np.round((total % 360) * (256 / 360)).astype(np.int64) % 256
    return steps.astype(np.uint8)

def _transact(frame: bytes, safe: bool, ack_timeout: float) -> bool | None:
    if state.ser is None:
        raise ConnectionError("Serial port is not connected.")
    if safe:
        state.ser.reset_input_buffer()
    state.ser.write(frame)
    if not safe:
        return None
    old = state.ser.timeout
    state.ser.timeout = ack_timeout
    resp = state.ser.read(1)
    state.ser.timeout = old
    if resp != bytes([ACK]):
        print(f"WARNING: no ACK (got {resp!r})")
        return False
    return True

def send_phases(phases, safe=False, ack_timeout=0.5, include_cp=True):
    frame = bytes([CMD_SET]) + _to_hardware(phases, include_cp).tobytes()
    return _transact(frame, safe, ack_timeout)

def _lut_body(phase_grid, include_cp) -> bytes:
    return b''.join(_to_hardware(p, include_cp).tobytes() for p in np.asarray(phase_grid))

def load_lut(phase_grid, include_cp=True, ack_timeout=1.0) -> bool:
    grid = np.asarray(phase_grid)
    if len(grid) > MAX_LUT:
        raise ValueError(f"LUT of {len(grid)} exceeds MAX_LUT={MAX_LUT}")
    body = _lut_body(grid, include_cp)
    ok = _transact(bytes([CMD_LOAD_LUT, len(grid)]) + body, True, ack_timeout)
    state.LUT_BYTES = body if ok else None
    return ok

def ensure_lut(phase_grid, include_cp=True) -> bool:
    '''Upload only if the table on the MCU differs from what would be sent now.'''
    if state.LUT_BYTES == _lut_body(phase_grid, include_cp):
        return True
    return load_lut(phase_grid, include_cp)

def apply_lut(index: int, safe=True, ack_timeout=0.5) -> bool | None:
    ok = _transact(bytes([CMD_APPLY, index]), safe, ack_timeout)
    if ok is False:
        state.LUT_BYTES = None   # table can't be trusted; next ensure_lut re-uploads
    return ok
def uart_self_test(timeout: float = 1.0) -> bool:
    if state.ser is None:
        return False
    state.ser.reset_output_buffer()
    frame = bytes([CMD_SET]) + bytes(16)
    return bool(_transact(frame, safe=True, ack_timeout=timeout))
#----end MCU interface ---

def update_phase(index: int, value: float):
    if value is None or value == '':
        return
    try:
        state.PHASE_OFFSETS[index] = float(value)
        state.PHASE_CORRECTED = True
    except ValueError:
        pass

def update_phase_inputs():
    for i, (field, val) in enumerate(zip(state.phase_inputs, state.PHASE_OFFSETS)):
        if not np.isclose(field.value, val):
            field.value = val

def save_calibration(filename: str):
    # Define the target directory
    directory = "Phase_Corrections"
    
    # Create the directory if it doesn't exist yet
    os.makedirs(directory, exist_ok=True)
    
    # Safeguard: ensure we append .json correctly and build the full path
    if not filename.endswith('.json'):
        filename = f"{filename}.json"
    filepath = os.path.join(directory, filename)
    
    rounded_offsets = (np.round(state.PHASE_OFFSETS / state.PHASE_STEP) * state.PHASE_STEP).tolist()
    
    with open(filepath, 'w') as f:
        json.dump(rounded_offsets, f)
    
    ui.notify(f'Calibration saved successfully into {filepath}!')


def use_calibration_file(filename: str):
    # Define the target directory
    directory = "Phase_Corrections"
    # Safeguard: ensure we append .json correctly and build the full path
    if not filename.endswith('.json'):
        filename = f"{filename}.json"
    filepath = os.path.join(directory, filename)
    try:
        with open(filepath, 'r') as f:
            loaded_offsets = json.load(f)
        state.PHASE_OFFSETS = np.round(np.array(loaded_offsets) / state.PHASE_STEP) * state.PHASE_STEP
        state.PHASE_CORRECTED = True
        update_phase_inputs()
        ui.notify(f'Calibration file: {filename} loaded and applied!')
    except FileNotFoundError:
        ui.notify(f"No calibration file: {filename} found in {directory}/")

def gen_Cal_from_S2P() -> None:
    phases = get_phase_at_freq()
    ref_phase = np.min(phases)
    state.PHASE_OFFSETS = (phases - ref_phase)
    ui.notify("Phase offsets computed and applied")
    update_phase_inputs()

def nav_back():
    stop_tx()
    state.selected = None
    ui.navigate.back()
