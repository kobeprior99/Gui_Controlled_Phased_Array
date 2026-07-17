'''
Contains helper functions for main.py
'''
import asyncio
import json
import numpy as np
import serial
from nicegui import ui

import state
from config import BAUDRATE
from READ_S2P import get_phase_at_freq
from PLUTO import stop_tx

async def set_com_port(port: str):
    state.SELECTED_COM_PORT = port
    try:
        # Note: serial is synchronous, but we handle the sleep asynchronously
        state.ser = serial.Serial(
            state.SELECTED_COM_PORT, 
            BAUDRATE, 
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE, 
            stopbits=serial.STOPBITS_ONE, 
            timeout=1
        )
        state.ser.dtr = True
        state.ser.rts = True
        await asyncio.sleep(3)  # Allow Arduino to reset
    except Exception as e:
        print(f'Failed to open serial port: {e}')

def send_phases(phases: np.ndarray):
    if state.ser is None:
        raise ConnectionError("Serial port is not connected.")
    
    total_phase = (phases + state.PHASE_OFFSETS)
    normalized_phase = total_phase % 360
    hardware_phases = np.uint8(np.round(normalized_phase * (256 / 360)))
    state.ser.write(hardware_phases.tobytes())

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
    rounded_offsets = (np.round(state.PHASE_OFFSETS / state.PHASE_STEP) * state.PHASE_STEP).tolist()
    with open(f'{filename}.json', 'w') as f:
        json.dump(rounded_offsets, f)
    ui.notify(f'Calibration saved successfully into {filename}.json!')

def use_calibration_file(filename: str):
    try:
        with open(f'{filename}.json', 'r') as f:
            loaded_offsets = json.load(f)
        state.PHASE_OFFSETS = np.round(np.array(loaded_offsets) / state.PHASE_STEP) * state.PHASE_STEP
        state.PHASE_CORRECTED = True
        update_phase_inputs()
        ui.notify(f'Calibration file: {filename}.json loaded and applied!')
    except FileNotFoundError:
        ui.notify(f"No calibration file: {filename}.json found")

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
