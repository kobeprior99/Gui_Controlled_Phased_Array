'''
Purpose: Contains helper functions for main.py
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
from config import BAUDRATE
from READ_S2P import get_phase_at_freq
from PLUTO import stop_tx

def uart_self_test(timeout: float = 1.0) ->bool:
    if state.ser is None:
        return False
    test_pattern = np.zeros(16, dtype=np.uint8)
    state.ser.reset_input_buffer()
    state.ser.reset_output_buffer()
    state.ser.write(test_pattern.tobytes())
    old_timeout = state.ser.timeout
    state.ser.timeout = timeout
    ack = state.ser.read(1)
    state.ser.timeout = old_timeout
    return ack == b'\xaa'

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
        if uart_self_test():
            print(f'UART link verified on {port}')
        else:
            print(f'No ACK from MCU on {port} - check wiring/reset')

    except Exception as e:
        print(f'Failed to open serial port: {e}')

def send_phases(phases: np.ndarray, safe: bool = False, ack_timeout: float = 0.5) -> bool | None:
    if state.ser is None:
        raise ConnectionError("Serial port is not connected.")

    total_phase = (phases + state.PHASE_OFFSETS)
    normalized_phase = total_phase % 360
    hardware_phases = np.uint8(np.round(normalized_phase * (256 / 360)))

    if safe:
        state.ser.reset_input_buffer()  # drop any stale bytes before we send

    state.ser.write(hardware_phases.tobytes())

    if not safe:
        return None  # fire-and-forget, no round trip cost

    old_timeout = state.ser.timeout
    state.ser.timeout = ack_timeout
    ack = state.ser.read(1)
    state.ser.timeout = old_timeout

    if ack != b'\xaa':
        print(f"WARNING: no ACK for phase update (got {ack!r})")
        return False
    return True

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
