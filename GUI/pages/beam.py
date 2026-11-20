'''
Purpose: This is the beam steering demonstration page that
allows you to experiment with an electronically steered
phased array in transmit and received mode.

Author: Kobe Prior
Last Edited: Nov 18 2026
'''
import asyncio
import time
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from nicegui import APIRouter, ui

import state
import helpers
from config import THETA_LIST, PHI_LIST, RX_GAIN, TX_GAIN,UV_STEP,r_max
from AF_Calc import runAF_Calc, get_spacing
from PLUTO import get_tone_energy,get_dBFS, tx, stop_tx, discard_buffer, set_gain
from create_default_rx_grid import ensure_default_rx_lut 

N_SETTLE_BUFFERS = 5
N_AVG_SCAN = 3
def refine_peak(u_pts, v_pts, powers, step=UV_STEP, half_width=1.0, n_fine=81):
    '''
    Sinc-interpolate the sampled power surface near the coarse peak and
    return the off-grid peak (u, v) and whether it is near the scan edge.
    '''
    k = np.argmax(powers)
    uc, vc = u_pts[k], v_pts[k]
    uf = np.linspace(uc - half_width * step, uc + half_width * step, n_fine)
    vf = np.linspace(vc - half_width * step, vc + half_width * step, n_fine)

    Ku = np.sinc((uf[:, None] - u_pts[None, :]) / step)   # (n_fine, K)
    Kv = np.sinc((vf[:, None] - v_pts[None, :]) / step)   # (n_fine, K)
    surf = np.einsum('ik,jk,k->ji', Ku, Kv, powers)       # rows = v, cols = u

    j, i = np.unravel_index(np.argmax(surf), surf.shape)
    near_edge = np.hypot(uc, vc) > r_max - step
    return uf[i], vf[j], near_edge
def sinc_surface(u_pts, v_pts, powers, step=UV_STEP, n=121):
    '''Sinc-interpolate the whole scan region onto a fine (u, v) grid.'''
    g = np.linspace(-r_max, r_max, n)
    U, V = np.meshgrid(g, g)
    Ku = np.sinc((g[:, None] - u_pts[None, :]) / step)   # (n, K)
    Kv = np.sinc((g[:, None] - v_pts[None, :]) / step)   # (n, K)
    S = np.einsum('jk,ik,k->ji', Kv, Ku, powers)         # rows = v, cols = u
    S = np.ma.masked_where(U**2 + V**2 > r_max**2, S)    # only show inside the scan circle
    return U, V, S
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


def add_tx_gain_slider():
    '''Adds a TX gain slider + live label, no notifications on change.'''
    def update_tx_gain(e):
        try:
            set_gain(tx_gain=e.value)
        except Exception as err:
            ui.notify(f'Failed to set TX gain: {err}', color='red')

    with ui.card().classes('w-full max-w-2xl mx-auto p-4 mt-2'):
        with ui.row().classes('w-full items-center justify-between'):
            ui.label('TX Gain (dB):').classes('font-semibold text-lg')
            tx_label = ui.label(f'{TX_GAIN:.1f} dB').classes('font-mono text-lg')

        tx_slider = ui.slider(
            min=-89.75, max=0.0, step=0.25, value=TX_GAIN,
            on_change=update_tx_gain
        ).classes('w-full')
        tx_slider.bind_value_to(tx_label, 'text', forward=lambda v: f'{v:.1f} dB')


def add_rx_gain_slider():
    '''Adds an RX gain slider + live label, no notifications on change.'''
    def update_rx_gain(e):
        try:
            set_gain(rx_gain=e.value)
        except Exception as err:
            ui.notify(f'Failed to set RX gain: {err}', color='red')

    with ui.card().classes('w-full max-w-2xl mx-auto p-4 mt-2'):
        with ui.row().classes('w-full items-center justify-between'):
            ui.label('RX Gain (dB):').classes('font-semibold text-lg')
            rx_label = ui.label(f'{RX_GAIN:.1f} dB').classes('font-mono text-lg')

        rx_slider = ui.slider(
            min=-1, max=73, step=1, value=RX_GAIN,
            on_change=update_rx_gain
        ).classes('w-full')
        rx_slider.bind_value_to(rx_label, 'text', forward=lambda v: f'{v:.1f} dB')


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
            ui.image('media/Array_Configuration.png').style('width: 75%;')

        default_dx, default_dy = get_spacing()  # DX_CP/DY_CP when CP array is selected
        with ui.row().classes('w-full justify-center items-center'):
            dx = ui.number(label='dx (λ)', value=default_dx, min=0.1).style('width:20%')
            dy = ui.number(label='dy (λ)', value=default_dy, min=0.1).style('width:20%')
            theta = ui.number(label='Theta (deg)', value=0, min=0, max=90).style('width:20%')
            phi = ui.number(label='Phi (deg)', value=0, min=0, max=360).style('width:20%')

        with ui.row().classes('w-full justify-center items-center'):
            y_min = ui.number(label='Set Minimum Power for Graph (dBFS)', value=-100, max=0).style('width:30%')
            y_max = ui.number(label='Set Maximum Power for Graph (dBFS)', value=0, max=10).style('width:30%')

        # ---- SDR Gain Controls ----
        ui.label('SDR Gain Controls').classes('text-2xl font-bold text-center mt-6')
        add_tx_gain_slider()

        fig = go.Figure(go.Scatter(x=[], y=[], mode='lines', name='Received Energy'))
        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis_title='Time(s)',
            yaxis_title='Avg Power Received (dBFS)'
        )
        with ui.row().classes('w-full justify-center items-center no-wrap'):
            live_plot = ui.plotly(fig).classes('w-3/4 h-64')
            with ui.card().classes('w-48 items-center p-4'):
                ui.label('Current Level').classes('text-sm text-gray-600')
                dbfs_label = ui.label('-- dBFS').classes('font-mono text-3xl font-bold')
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
            dBFS_values = []
            start_time = time.time()

            while not stop_event.is_set():
                t = time.time() - start_time
                dBFS = get_dBFS()
                dbfs_label.set_text(f'{dBFS:.1f} dBFS')
                t_values.append(t)
                dBFS_values.append(dBFS)
                t_values = t_values[-100:]
                dBFS_values = dBFS_values[-100:]

                fig.data[0].x = t_values
                fig.data[0].y = dBFS_values

                try:
                    fig.update_yaxes(type='linear', range=[float(y_min.value), float(y_max.value)])
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
            ui.image('media/Array_Configuration.png').style('width: 70%;')

        with ui.row().classes('w-full justify-center items-center'):
            ui.label('Place the transmitting antenna somewhere within line of sight of the receiving array, then press start when you are ready to scan')\
                .classes('text-base text-gray-600 text-center')
        with ui.row().classes('w-full justify-center items-center'):
            ui.label('The coefficients are precomputed for the default array')\
                .classes('text-base text-gray-600 text-center')

        # ---- SDR Gain Controls ----
        ui.label('SDR Gain Controls').classes('text-2xl font-bold text-center mt-6')
        add_rx_gain_slider()

    image_container = ui.row().classes('w-full justify-center items-center').style('order:2;')
    scan_running = {'value': False}
    def Scan_Beam():
        if scan_running['value']:
            ui.notify('A scan is already running', type='warning')
            return
        scan_running['value'] = True

        with ui.dialog() as dialog, ui.card():
            label = ui.label('Starting beam scan...')
            ui.linear_progress(show_value=False).props('indeterminate')
            dialog.open()

        def measure(i):
            '''Blocking: runs in a worker thread, never touches the UI.'''
            if not helpers.apply_lut(i):
                raise RuntimeError(f'MCU did not confirm array state {i}')
            for _ in range(N_SETTLE_BUFFERS):
                discard_buffer()
            return get_tone_energy(N_AVG_SCAN)

        async def scan_task():
            try:
                # Table on the MCU must match the current grid, calibration, and CP setting
                rx_grid, ok = await asyncio.to_thread(ensure_default_rx_lut)
                if not ok:
                    ui.notify('MCU did not confirm LUT upload', color='red')
                    return

                n_steps = len(rx_grid)
                powers = np.zeros(n_steps)

                tx()
                await asyncio.sleep(1.0)  # Tx power / local oscillator stabilization

                for i in range(n_steps):
                    powers[i] = await asyncio.to_thread(measure, i)
                    label.set_text(f"Scanning {i+1}/{n_steps}")
            except Exception as e:
                ui.notify(f'Scan failed: {e}', color='red')
                return
            finally:
                stop_tx()
                scan_running['value'] = False
                # dialog is closed below on success, or here on failure
                if not (locals().get('powers') is not None and np.any(powers)):
                    dialog.close()

            # ---- normalize and plot ----
            peak_val = np.max(powers)
            if peak_val <= 0:
                ui.notify('No signal detected, check TX/RX gain and connections', color='red')
                dialog.close()
                return
            powers /= peak_val

            u_pts = np.sin(np.deg2rad(THETA_LIST)) * np.cos(np.deg2rad(PHI_LIST))
            v_pts = np.sin(np.deg2rad(THETA_LIST)) * np.sin(np.deg2rad(PHI_LIST))

            # grid peak (no interpolation)
            peak = np.argmax(powers)
            theta_grid, phi_grid = THETA_LIST[peak], PHI_LIST[peak]

            # refined peak (sinc interpolation)
            u_pk, v_pk, near_edge = refine_peak(u_pts, v_pts, powers)
            rho = min(np.hypot(u_pk, v_pk), 1.0)
            theta_ref = np.degrees(np.arcsin(rho))
            phi_ref = np.degrees(np.arctan2(v_pk, u_pk)) % 360

            def label_box(ax, x, y, text):
                ax.annotate(text, xy=(x, y), xytext=(0, 14), ha='center', va='center',
                            textcoords='offset points', color='white', fontsize=10,
                            bbox=dict(boxstyle="round,pad=0.2", fc="black", alpha=0.5), zorder=100)

            levels = np.linspace(0, 1, 21)   # same color scale on both plots

# ---- plot 1: raw grid ----
            fig, ax = plt.subplots(figsize=(8, 6))
            cf = ax.tricontourf(u_pts, v_pts, powers, levels=levels, cmap='plasma')
            ax.scatter(u_pts, v_pts, c='k', s=8, alpha=0.4)
            ax.plot(u_pts[peak], v_pts[peak], 'ro', markersize=10)
            label_box(ax, u_pts[peak], v_pts[peak], fr"$\phi$: {phi_grid:.1f}°, $\theta$: {theta_grid:.1f}°")
            fig.colorbar(cf, ax=ax, label='Received tone power (normalized)')
            ax.set_xlabel('u = sin(θ)cos(φ)'); ax.set_ylabel('v = sin(θ)sin(φ)')
            ax.set_aspect('equal', adjustable='box'); ax.set_title('Beam Scan')
            fig.savefig('media/rx_heat.png', dpi=300)
            plt.close(fig)

# ---- plot 2: sinc-interpolated ----
            U, V, S = sinc_surface(u_pts, v_pts, powers)
            fig2, ax2 = plt.subplots(figsize=(8, 6))
            cf2 = ax2.contourf(U, V, np.clip(S, 0, 1), levels=levels, cmap='plasma')
            ax2.scatter(u_pts, v_pts, c='k', s=8, alpha=0.4)
            ax2.plot(u_pts[peak], v_pts[peak], 'wo', markersize=8, mfc='none')   # grid max
            ax2.plot(u_pk, v_pk, 'ro', markersize=10)                            # refined peak
            label_box(ax2, u_pk, v_pk,
                      fr"$\phi$: {phi_ref:.1f}°, $\theta$: {theta_ref:.1f}°" + ("*" if near_edge else ""))
            fig2.colorbar(cf2, ax=ax2, label='Received tone power (normalized)')
            ax2.set_xlabel('u = sin(θ)cos(φ)'); ax2.set_ylabel('v = sin(θ)sin(φ)')
            ax2.set_aspect('equal', adjustable='box'); ax2.set_title('Beam Scan (Sinc-interpolated)')
            fig2.savefig('media/rx_heat_interp.png', dpi=300)
            plt.close(fig2)

            image_container.clear()
            with image_container:
                ui.image('media/rx_heat.png').style('width:65%;').force_reload()
                ui.image('media/rx_heat_interp.png').style('width:65%;').force_reload()

            dialog.close()

        asyncio.create_task(scan_task())

    ui.button('Start', on_click=Scan_Beam)
