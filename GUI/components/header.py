'''
header.py
Description: header for home page
Author Kobe Prior
Date Last Modified: Nov 24, 2026
'''
import serial.tools.list_ports
from nicegui import ui, background_tasks
import state, helpers

def header():
    ports = {p.device: f'{p.device} - {p.description}'
             for p in serial.tools.list_ports.comports()}
    with ui.column().classes('w-full items-center'):
        ui.image('media/arcLogo_header.png') \
            .classes('w-full cursor-pointer hover:opacity-80 transition-opacity') \
            .on('click', lambda: ui.run_javascript(
                "window.open('https://arc.elsherbeni.com/', '_blank')"))
        ui.label("Low-Cost Software-Defined Phased Array Controller") \
            .classes('text-3xl font-bold mb-4')
        ui.label("Developed by Kobe Prior").classes('text-lg text-gray-500 mb-4')
        with ui.row().classes('items-center justify-center gap-6 mb-8'):
            ui.select(options=ports, label=state.SELECTED_COM_PORT,
                      on_change=lambda e: background_tasks.create(helpers.set_com_port(e.value))
                      ).style('width: 300px')
            ui.toggle({'linear': 'Linear Array', 'circular': 'Circularly Polarized Array'},
                      value='circular' if state.CP_ARRAY else 'linear',
                      on_change=lambda e: setattr(state, 'CP_ARRAY', e.value == 'circular'))
