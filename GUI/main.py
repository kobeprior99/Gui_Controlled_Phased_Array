import asyncio
import serial.tools.list_ports
from nicegui import ui, app

import state
import helpers

# Import all routers from the pages module
from pages import (
    calibrate_router,
    manual_router,
    beam_router,
    scattering_router
)

# Attach/Include routers
app.include_router(calibrate_router)
app.include_router(manual_router)
app.include_router(beam_router)
app.include_router(scattering_router)

@ui.page('/')
def main_page():
    ports = serial.tools.list_ports.comports()
    portsList = {p.device: f'{p.device} - {p.description}' for p in ports} 

    com_input = ui.select(
        options=portsList, 
        label=state.SELECTED_COM_PORT,
        on_change=lambda e: asyncio.create_task(helpers.set_com_port(e.value))
    ).style('width: 300px')

    images = [
        ('/calibrate', 'Calibration.png'),
        ('/manual', 'Manual_Phase_Control.png'), 
        ('/beam', 'Beam_Control.png'),
        ('/scattering', 'Scattering_Experiment.png')
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
