'''
receive.py
Description: scan through known angles and produce AoA
Author: Kobe Prior
Date Last Modified: Nov24, 2026
'''
import asyncio
import numpy as np
from nicegui import ui

import helpers
from config import THETA_LIST, PHI_LIST
from components.gain_slider import rx_gain_slider
from beam_tools.math import refine_peak, uv_from_angles, uv_to_angles
from beam_tools.plots import save_raw_heatmap, save_interp_heatmap
from beam_tools.scan import run_scan
from ._router import router

RAW_PNG = 'media/rx_heat.png'
INTERP_PNG = 'media/rx_heat_interp.png'


def _analyze_and_render(powers):
    '''Blocking: find the peak and write both heatmaps. Run in a worker thread.'''
    u_pts, v_pts = uv_from_angles(THETA_LIST, PHI_LIST)

    peak = int(np.argmax(powers))
    theta_grid, phi_grid = THETA_LIST[peak], PHI_LIST[peak]

    u_pk, v_pk, near_edge = refine_peak(u_pts, v_pts, powers)
    theta_ref, phi_ref = uv_to_angles(u_pk, v_pk)

    save_raw_heatmap(u_pts, v_pts, powers, peak, theta_grid, phi_grid, RAW_PNG)
    save_interp_heatmap(u_pts, v_pts, powers, peak, u_pk, v_pk,
                        theta_ref, phi_ref, near_edge, INTERP_PNG)


@router.page('/receive_mode')
def receive_mode():
    ui.button('⬅ Back', on_click=helpers.nav_back)
    with ui.column().classes('w-full'):
        ui.label('Receive mode').classes('text-2xl font-bold text-center')
        for text, width in [
            ('Please connect the phase shifting network with the following port order', None),
        ]:
            with ui.row().classes('w-full justify-center items-center'):
                ui.label(text).classes('text-base text-gray-600 text-center')

        with ui.row().classes('w-full justify-center items-center'):
            ui.image('media/Array_Configuration.png').style('width: 70%;')

        for text in (
            'Place the transmitting antenna somewhere within line of sight of the '
            'receiving array, then press start when you are ready to scan',
            'The coefficients are precomputed for the default array',
        ):
            with ui.row().classes('w-full justify-center items-center'):
                ui.label(text).classes('text-base text-gray-600 text-center')

        ui.label('SDR Gain Controls').classes('text-2xl font-bold text-center mt-6')
        rx_gain_slider()

    image_container = ui.row().classes('w-full justify-center items-center').style('order:2;')
    scan_running = {'value': False}

    async def start_scan():
        if scan_running['value']:
            ui.notify('A scan is already running', type='warning')
            return
        scan_running['value'] = True

        with ui.dialog() as dialog, ui.card():
            label = ui.label('Starting beam scan...')
            ui.linear_progress(show_value=False).props('indeterminate')
        dialog.open()

        try:
            powers = await run_scan(lambda i, n: label.set_text(f'Scanning {i}/{n}'))

            peak_val = np.max(powers)
            if peak_val <= 0:
                ui.notify('No signal detected, check TX/RX gain and connections', color='red')
                return
            powers = powers / peak_val

            label.set_text('Rendering plots...')
            await asyncio.to_thread(_analyze_and_render, powers)

            image_container.clear()
            with image_container:
                ui.image(RAW_PNG).style('width:65%;').force_reload()
                ui.image(INTERP_PNG).style('width:65%;').force_reload()
        except Exception as e:
            ui.notify(f'Scan failed: {e}', color='red')
        finally:
            dialog.close()
            scan_running['value'] = False

    ui.button('Start', on_click=start_scan)
