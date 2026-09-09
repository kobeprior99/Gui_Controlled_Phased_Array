'''
Purpose: this is the entry point into the graphical user interface that host pages shown @pages
Author: Kobe Prior
Last Modified: September 7, 2026
'''
import asyncio
import signal
import atexit
import serial.tools.list_ports
from nicegui import ui, app,background_tasks

import state
import helpers
from PLUTO import stop_tx  # Import stop_tx from your SDR module

# Import all routers from the pages module
from pages import (
    calibrate_router,
    manual_router,
    beam_router,
    scattering_router,
    scattering_router2
)

# Attach/Include routers
app.include_router(calibrate_router)
app.include_router(manual_router)
app.include_router(beam_router)
app.include_router(scattering_router)
app.include_router(scattering_router2)

# --- Shutdown & Clean-Up Handlers ---
def cleanup():
    """Safety function to disable transmitter upon exit."""
    try:
        stop_tx()
        print("\n[INFO] Transmitter successfully disabled.")
    except Exception as e:
        print(f"\n[ERROR] Failed to stop transmitter during shutdown: {e}")

# 1. Hook into NiceGUI's app shutdown event
app.on_shutdown(cleanup)

# 2. Register Python process exit handlers (atexit & OS signals)
atexit.register(cleanup)

def signal_handler(sig, frame):
    cleanup()
    exit(0)

signal.signal(signal.SIGINT, signal_handler)   # Handles Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Handles terminate requests

# --- GUI Layout ---
@ui.page('/')
def main_page():
    ports = serial.tools.list_ports.comports()
    portsList = {p.device: f'{p.device} - {p.description}' for p in ports} 

    com_input = ui.select(
        options=portsList, 
        label=state.SELECTED_COM_PORT,
        on_change=lambda e: background_tasks.create(helpers.set_com_port(e.value))
    ).style('width: 300px')

    images = [
        ('/calibrate', 'Calibration.png'),
        ('/manual', 'Manual_Phase_Control.png'), 
        ('/beam', 'Beam_Control.png'),
        ('/scattering', 'Scattering_Experiment.png'),
        ('/scattering2', 'Scattering_Experiment2.jpeg')
    ]

    with ui.column().classes('w-full items-center'):
        ui.label('Antenna Array Control').classes('text-3xl font-bold mb-8')
    
    ui.add_head_html('''
        <style>
            @keyframes blink {
              0%, 100% { opacity: 1; }
              50% { opacity: 0.4; }
            }
            .blink { animation: blink 1.2s ease-in-out infinite; }
        </style>
    ''')

    with ui.row().classes('w-full justify-center items-center gap-4'):
        for target, filename in images:
            classes_style = 'w-1/5 cursor-pointer hover:scale-105 transition-transform duration-200' 
            if target == images[0][0] and not state.PHASE_CORRECTED: 
                ui.image(f'media/{filename}')\
                    .classes(f'{classes_style} blink') \
                    .on('click', lambda t=target: navigate_if_ready(t))
            else:
                ui.image(f'media/{filename}')\
                    .classes(classes_style) \
                    .on('click', lambda t=target: navigate_if_ready(t))
    
    def navigate_if_ready(target):
        if state.SELECTED_COM_PORT == 'SELECT MCU PORT':
            ui.notify("Please Select MCU Port before proceeding.", color='red')
            return
        ui.navigate.to(target)

# Execute the NiceGUI app
ui.run(title="Phase Network Control Dashboard", reload=False)
