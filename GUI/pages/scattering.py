'''
Purpose: Run a scattering experiment to compare the scattering due to
incident structured waveforms to compare to plane wave illumination
Author: Kobe Prior
Last Modified: July 17, 2026
'''
# pages/scattering.py
from nicegui import APIRouter, ui
import state
import helpers
from config import OAM_PHASES
from PLUTO import tx, stop_tx, discard_buffer, get_dBFS
import numpy as np

router = APIRouter()

def oam_mode(mode: str):
    phases = OAM_PHASES * int(mode)
    try: 
        helpers.send_phases(phases)
    except Exception as e:
        ui.notify(f'Failed to send phases: {e}', color='red')
    else:
        ui.notify('Successfully sent phases')

def hermite_mode(mode: str):
    if mode == '01':
        phases = np.array([
            0,0,0,0,0,0,0,0,180,180,180,180,180,180,180,180
        ])
    elif mode == '10':
        phases = np.array([
            0,0,180,180,0,0,180,180,0,0,180,180,0,0,180,180
        ])
    else:
        phases = np.array([
            0,0,180,180,0,0,180,180,180,180,0,0,180,180,0,0
        ]) 

    try: 
        helpers.send_phases(phases)
    except Exception as e:
        ui.notify(f'Failed to send phases: {e}', color='red')
    else:
        ui.notify('Successfully sent phases')


@router.page('/scattering')
def scattering():
    ui.button('⬅ Back', on_click=helpers.nav_back)
    with ui.column().classes('w-full items-center gap-6 mt-6'):
        ui.label('Scattering Mode Selection').classes('text-2xl font-bold text-center')
        ui.label('Attach provided 4x4 antenna array port 1 to top left ascending going down and to the right').classes('text-base text-gray-600 text-center')
        
        with ui.row().classes('w-full justify-center items-center'):
            ui.image('media/Default_Array.png').style('width: 35%;')
            ui.image('media/Default_Array2.png').style('width: 35%;')

    oam_images = [
        ('-3', 'oam--3.png'),
        ('-2', 'oam-2.png'), 
        ('-1', 'oam-1.png'),
        ('1', 'oam1.png'),
        ('2', 'oam2.png'),
        ('3', 'oam3.png'),
        ('0', 'plane_wave.png')
    ]

    hermite_images = [
        ('01', '01.png'), 
        ('10', '10.png'),
        ('11', '11.png'),
    ]

    image_elements = {}

    def select_oam_image(t):
        if state.selected is not None and state.selected in image_elements:
            image_elements[state.selected].classes(remove='ring-4 ring-red-500')
        image_elements[t].classes('ring-4 ring-red-500')
        state.selected = t
        oam_mode(t)

    def select_hermite_image(t):
        if state.selected is not None and state.selected in image_elements:
            image_elements[state.selected].classes(remove='ring-4 ring-red-500')
        image_elements[t].classes('ring-4 ring-red-500')
        state.selected = t
        hermite_mode(t)

    ui.label('OAM Modes').classes('text-xl font-bold text-center mt-4')
    with ui.row().classes('w-full justify-center items-center gap-4'):
        for target, filename in oam_images:
            img = ui.image(f'media/{filename}')\
                .classes('w-1/5 cursor-pointer hover:scale-105 transition-transform duration-200') \
                .on('click', lambda _, t=target: select_oam_image(t))
            image_elements[target] = img

    ui.label('Hermite Modes').classes('text-xl font-bold text-center mt-4')
    with ui.row().classes('w-full justify-center items-center gap-4'):
        for target, filename in hermite_images:
            img = ui.image(f'media/{filename}')\
                .classes('w-1/5 cursor-pointer hover:scale-105 transition-transform duration-200') \
                .on('click', lambda _, t=target: select_hermite_image(t))
            image_elements[target] = img

    # ---- Noise Measurement (dBFS) ----
    ui.label('Noise Measurement').classes('text-2xl font-bold text-center mt-6')
    ui.label('Press the button below to record and report the receiver noise level in dBFS.')\
        .classes('text-base text-gray-600 text-center')

    noise_label = ui.label('').classes('text-xl font-bold text-center mt-2')
    noise_dbfs_value = {'value': None}

    def record_noise_and_coupling_dbfs():
        try:
            tx()
            for _ in range(100):
                discard_buffer()
            dbfs = get_dBFS()
            stop_tx()
        except Exception as e:
            ui.notify(f'Failed to measure noise: {e}', color='red')
            return
        finally:
            stop_tx()
        noise_dbfs_value['value'] = dbfs
        noise_label.set_text(f'Noise Level: {dbfs:.2f} dBFS')
        ui.notify('Noise measurement complete', type='positive')

    ui.button('Record Noise and coupling (dBFS)', on_click=record_noise_and_coupling_dbfs)
    
    # ---- Backscattered Power Measurement ----
    ui.label('Backscattered Power Measurement').classes('text-2xl font-bold text-center mt-6')
    ui.label('Press the button below to transmit and record the backscattered power above the noise floor.')\
        .classes('text-base text-gray-600 text-center')
    
    tx_dbfs_label = ui.label('').classes('text-xl font-bold text-center mt-2')
    
    def record_tx_dbfs():
        if noise_dbfs_value['value'] is None:
            ui.notify('Please record the noise floor first!', type='warning')
            return
        try:
            tx()
            for _ in range(100):
                discard_buffer()
            dbfs = get_dBFS()
        except Exception as e:
            ui.notify(f'Failed to measure backscattered power: {e}', color='red')
            return
        finally:
            stop_tx()
        rel_power = dbfs - noise_dbfs_value['value']
        tx_dbfs_label.set_text(f'Backscattered Power Above Noise: {rel_power:.2f} dB')
        ui.notify('Backscattered power measurement complete', type='positive')
        
    ui.button('Record Backscattered Power Above Noise', on_click=record_tx_dbfs)
