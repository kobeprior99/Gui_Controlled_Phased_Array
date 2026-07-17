'''
Purpose: This is the beam steering demonstration page that
allows you to experiment with an electronically steered
phased array in transmit and received mode.

Author: Kobe Prior
Last Edited: July 17 2026
'''
import asyncio
import time
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from nicegui import APIRouter, ui

import state
import helpers
from config import DX, DY, THETA_RANGE, PHI_RANGE
from AF_Calc import runAF_Calc
from PLUTO import get_energy, tx, stop_tx, discard_buffer
from create_default_rx_grid import DEFAULT_RX_GRID

router = APIRouter()

@router.page('/beam')
def beam_page():
    ui.button('⬅ Back', on_click=helpers.nav_back)
    with ui.row().classes('w-full justify-center items-center'):
        ui.button('Receive Mode', on_click=lambda: ui.navigate.to('/receive_mode')).\
            classes('w-64 h-24 text-xl')
        ui.button('Transmit Mode', on_click=lambda: ui.navigate.to('/transmit_mode')).\
            classes('w-64 h-24 text-xl')

    with ui.row().classes('w-full justify-center items-center'):
        ui.image('media/Beam_Explanation.png')


# ---- Transmit Mode Subpage ----
@router.page('/transmit_mode')
def transmit_mode():
    ui.button('⬅ Back', on_click=helpers.nav_back)
    with ui.column().classes('w-full'):
        ui.label('Transmit mode').classes('text-2xl font-bold text-center')
        with ui.row().classes('w-full justify-center items-center'):
            ui.label('Please connect the phase shifting network with the following port order, then define your array parameters and steer angle')\
                .classes('text-base text-gray-600 text-center')

        with ui.row().classes('w-full justify-center items-center'):
            ui.image('media/Default_Array.png').style('width: 35%;')
            ui.image('media/Default_Array2.png').style('width: 35%;')

        with ui.row().classes('w-full justify-center items-center'):
            dx = ui.number(label='dx (λ)', value=DX, min=0.1).style('width:20%')
            dy = ui.number(label='dy (λ)', value=DY, min=0.1).style('width:20%')
            theta = ui.number(label='Theta (deg)', value=0, min=0, max=90).style('width:20%')
            phi = ui.number(label='Phi (deg)', value=0, min=0, max=360).style('width:20%')
             
        with ui.row().classes('w-full justify-center items-center'):
            y_min = ui.number(label='Set Minimum Power for Graph', value=0, min=1).style('width:30%') 
            y_max = ui.number(label='Set Maximum Power for Graph', value=10, min=1).style('width:30%')

        # Added a toggle switch to let the user select between Linear and Logarithmic scales
        with ui.row().classes('w-full justify-center items-center m-2'):
            scale_type = ui.toggle({'linear': 'Linear', 'log': 'Logarithmic'}, value='linear')

        fig = go.Figure(go.Scatter(x=[], y=[], mode='lines', name='Received Energy'))
        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis_title='Time(s)',
            yaxis_title='Avg Power Received'
        )
        live_plot = ui.plotly(fig).classes('w-3/4 h-64')
        image_container = ui.row().classes('justify-center items-center').style('order:2; width:90%;')
        stop_event = asyncio.Event()
        
        def start_live_plot():
            phases = runAF_Calc(dx.value, dy.value, theta.value, phi.value)
            helpers.send_phases(phases)

            image_container.clear()
            with image_container:
                ui.image('media/AF.png').style('width:40%;').force_reload()
                ui.image('media/uv.png').style('width:40%;').force_reload()
            
            tx()
            stop_event.clear()
            asyncio.create_task(live_update())
            new_angle_button.visible = True
            stop_button.visible = True

        async def live_update():
            t_values = []
            energy_values = []
            start_time = time.time()

            while not stop_event.is_set():
                t = time.time() - start_time
                energy = get_energy()
                t_values.append(t)
                energy_values.append(energy)
                t_values = t_values[-100:]
                energy_values = energy_values[-100:]
                
                fig.data[0].x = t_values
                fig.data[0].y = energy_values
                
                try:
                    # Dynamically adjust type and range based on the scale type toggle
                    if scale_type.value == 'log':
                        import math
                        # Plotly logs require the log10 value of the boundaries when hardcoding ranges
                        # Also protecting against 0/negative values with max(0.001, ...)
                        low_bound = math.log10(max(0.001, float(y_min.value)))
                        high_bound = math.log10(max(0.001, float(y_max.value)))
                        fig.update_yaxes(type='log', range=[low_bound, high_bound])
                    else:
                        fig.update_yaxes(type='linear', range=[int(y_min.value), int(y_max.value)])
                except Exception:
                    pass
                
                live_plot.update()
                await asyncio.sleep(0.05)

        def send_current_phase():
            phases = runAF_Calc(dx.value, dy.value, theta.value, phi.value)
            helpers.send_phases(phases)
            image_container.clear()
            with image_container:
                ui.image('media/AF.png').style('width:40%;').force_reload()
                ui.image('media/uv.png').style('width:40%;').force_reload()

        def stop_live():
            stop_tx()
            stop_event.set()
            ui.notify("Live plot stopped", type='positive')

        # Control Panel
        with ui.row().classes('w-full justify-center gap-4 mt-4'):
            ui.button('Transmit & Live Plot', on_click=start_live_plot)
            new_angle_button = ui.button('New Angle', on_click=send_current_phase)
            new_angle_button.visible = False
            stop_button = ui.button('Stop', on_click=stop_live)
            stop_button.visible = False


# ---- Receive Mode Subpage ----
@router.page('/receive_mode')
def receive_mode():        
    ui.button('⬅ Back', on_click=helpers.nav_back)
    with ui.column().classes('w-full'):
        ui.label('Receive mode').classes('text-2xl font-bold text-center')
        with ui.row().classes('w-full justify-center items-center'):
            ui.label('Please connect the phase shifting network with the following port order')\
                .classes('text-base text-gray-600 text-center')

        with ui.row().classes('w-full justify-center items-center'):
            ui.image('media/Default_Array.png').style('width: 45%;')
            ui.image('media/Default_Array2.png').style('width: 45%;')
        with ui.row().classes('w-full justify-center items-center'): 
            ui.label('Place the transmitting antenna somewhere within line of sight of the receiving array, then press start when you are ready to scan')\
                .classes('text-base text-gray-600 text-center')
        with ui.row().classes('w-full justify-center items-center'): 
            ui.label('The coefficients are precomputed for the default array')\
                .classes('text-base text-gray-600 text-center')
    
    image_container = ui.row().classes('w-full justify-center items-center').style('order:2;')

    def Scan_Beam():
        with ui.dialog() as dialog, ui.card():
            label = ui.label('Starting beam scan...')
            ui.linear_progress(show_value=False).props('indeterminate')
            dialog.open()

        async def scan_task():
            tx()
            n_steps = len(DEFAULT_RX_GRID)
            energies = np.zeros(n_steps)

            for i, phases in enumerate(DEFAULT_RX_GRID):
                helpers.send_phases(phases)
                if i == 0:
                    for _ in range(10):
                        discard_buffer()
                energies[i] = get_energy()
                await asyncio.sleep(10e-6)
                label.set_text(f"Scanning {i+1}/{n_steps}")

            stop_tx()

            energies_2D = energies.reshape(len(THETA_RANGE), len(PHI_RANGE))
            energies_2D /= np.max(energies_2D)
            peak_idx = np.unravel_index(np.argmax(energies_2D), energies_2D.shape)
            theta_peak = THETA_RANGE[peak_idx[0]]
            phi_peak = PHI_RANGE[peak_idx[1]]

            fig, ax = plt.subplots(figsize=(8, 6))
            im = ax.imshow(
                energies_2D,
                extent=[PHI_RANGE[0], PHI_RANGE[-1], THETA_RANGE[0], THETA_RANGE[-1]],
                origin='lower',
                aspect='auto',
                cmap='plasma'
            )

            ax.plot(phi_peak, theta_peak, 'ro', markersize=10)
            ax.annotate(
                fr"$\phi$: {phi_peak:.1f}°,$\theta$: {theta_peak:.1f}°",
                xy=(phi_peak, theta_peak),
                xytext=(0, 10),
                ha='center',
                va='center',
                textcoords='offset points',
                color='white',
                fontsize=10,
                bbox=dict(boxstyle="round,pad=0.2", fc="black", alpha=0.5),
                zorder=100
            )
            plt.colorbar(im, ax=ax, label='Received energy')
            ax.set_xlabel('Phi [deg]')
            ax.set_ylabel('Theta [deg]')
            ax.set_title('Beam Scan')
            plt.savefig('media/rx_heat.png', dpi=300)
            plt.close()

            image_container.clear()
            with image_container:
                ui.image('media/rx_heat.png').style('width:65%;').force_reload()

            dialog.close()

        asyncio.create_task(scan_task()) 

    ui.button('Start', on_click=Scan_Beam)
