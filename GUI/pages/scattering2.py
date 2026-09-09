'''
Purpose: Run a scattering experiment 2 to find 
the existance of an orientation angle theta for a scattering object,
that when illuminated by a structured waveform produces higher back 
scattered power.
Author: Kobe Prior
Last Modified: September 8, 2026
'''
# pages/scattering.py
import asyncio
import time
import plotly.graph_objects as go
from nicegui import APIRouter, ui
import state
import helpers
from config import OAM_PHASES, RX_GAIN, TX_GAIN, SETTLE_TIME_S, N_DISCARD_BUFFERS, N_AVG_BUFFERS
from PLUTO import tx, stop_tx, discard_buffer, get_dBFS, set_gain
import numpy as np

router = APIRouter()


async def oam_mode(mode: str, phase_confirmed: dict):
    phases = OAM_PHASES * int(mode)
    try:
        confirmed = await asyncio.to_thread(helpers.send_phases, phases, True)
    except Exception as e:
        confirmed = False
        ui.notify(f'Failed to send phases: {e}', color='red')
    phase_confirmed['value'] = confirmed
    if confirmed:
        ui.notify('Successfully sent phases', type='positive')
    else:
        ui.notify('Phases sent but not confirmed by MCU!', color='red')


async def hermite_mode(mode: str, phase_confirmed: dict):
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
        confirmed = await asyncio.to_thread(helpers.send_phases, phases, True)
    except Exception as e:
        confirmed = False
        ui.notify(f'Failed to send phases: {e}', color='red')
    phase_confirmed['value'] = confirmed
    if confirmed:
        ui.notify('Successfully sent phases', type='positive')
    else:
        ui.notify('Phases sent but not confirmed by MCU!', color='red')


@router.page('/scattering2')
def scattering2():
    ui.button('⬅ Back', on_click=helpers.nav_back)

    # ---- Busy state (locks controls while a measurement is in flight) ----
    busy = {'value': False}
    lockable_elements = []  # sliders/buttons with .disable()/.enable()

    # ---- Phase confirmation state (locks measurements if last send unconfirmed) ----
    phase_confirmed = {'value': True}  # True until a send fails to confirm

    def set_busy(is_busy: bool):
        busy['value'] = is_busy
        for el in lockable_elements:
            el.disable() if is_busy else el.enable()

    def guard_busy() -> bool:
        '''Returns True (and notifies) if a measurement is currently running.'''
        if busy['value']:
            ui.notify('A measurement is in progress, please wait', type='warning')
            return True
        return False

    def guard_unconfirmed() -> bool:
        '''Returns True (and notifies) if the last phase send wasn't confirmed by the MCU.'''
        if not phase_confirmed['value']:
            ui.notify('Last phase update was not confirmed by the MCU — reselect a mode before measuring', color='red')
            return True
        return False

    with ui.column().classes('w-full items-center gap-6 mt-6'):
        ui.label('Scattering Mode Selection').classes('text-2xl font-bold text-center')
        ui.label('Attach provided 4x4 antenna array port 1 to top left ascending going down and to the right').classes('text-base text-gray-600 text-center')
        
        with ui.row().classes('w-full justify-center items-center'):
            ui.image('media/Default_Array.png').style('width: 35%;')
            ui.image('media/Default_Array2.png').style('width: 35%;')

    # ---- SDR Gain Controls ----
    ui.label('SDR Gain Controls').classes('text-2xl font-bold text-center mt-6')

    def update_rx_gain(e):
        if guard_busy():
            return
        try:
            set_gain(rx_gain=e.value)
        except Exception as err:
            ui.notify(f'Failed to set RX gain: {err}', color='red')

    def update_tx_gain(e):
        if guard_busy():
            return
        try:
            set_gain(tx_gain=e.value)
        except Exception as err:
            ui.notify(f'Failed to set TX gain: {err}', color='red')

    with ui.card().classes('w-full max-w-2xl mx-auto p-4 mt-2'):
        with ui.column().classes('w-full gap-4'):
            # RX Gain Slider (-1 dB to 73 dB)
            with ui.row().classes('w-full items-center justify-between'):
                ui.label('RX Gain (dB):').classes('font-semibold text-lg')
                rx_label = ui.label(f'{RX_GAIN:.1f} dB').classes('font-mono text-lg')

            rx_slider = ui.slider(
                min=-1, max=73, step=1, value=RX_GAIN,
                on_change=update_rx_gain
            ).classes('w-full')
            rx_slider.bind_value_to(rx_label, 'text', forward=lambda v: f'{v:.1f} dB')
            lockable_elements.append(rx_slider)

            # TX Gain Slider (-89.75 dB to 0 dB)
            with ui.row().classes('w-full items-center justify-between mt-2'):
                ui.label('TX Gain (dB):').classes('font-semibold text-lg')
                tx_label = ui.label(f'{TX_GAIN:.1f} dB').classes('font-mono text-lg')

            tx_slider = ui.slider(
                min=-89.75, max=0.0, step=0.25, value=TX_GAIN,
                on_change=update_tx_gain
            ).classes('w-full')
            tx_slider.bind_value_to(tx_label, 'text', forward=lambda v: f'{v:.1f} dB')
            lockable_elements.append(tx_slider)

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

    async def select_oam_image(t):
        if guard_busy():
            return
        if state.selected is not None and state.selected in image_elements:
            image_elements[state.selected].classes(remove='ring-4 ring-red-500')
        image_elements[t].classes('ring-4 ring-red-500')
        state.selected = t
        await oam_mode(t, phase_confirmed)

    async def select_hermite_image(t):
        if guard_busy():
            return
        if state.selected is not None and state.selected in image_elements:
            image_elements[state.selected].classes(remove='ring-4 ring-red-500')
        image_elements[t].classes('ring-4 ring-red-500')
        state.selected = t
        await hermite_mode(t, phase_confirmed)

    ui.label('OAM Modes').classes('text-xl font-bold text-center mt-4')
    with ui.row().classes('w-full justify-center items-center gap-4'):
        for target, filename in oam_images:
            # Pass async function directly to .on('click', ...) without asyncio.create_task
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

    # ---- Live dBFS Power Plot ----
    # Replaces the old "Record Noise" / "Record Backscattered Power" buttons: instead of two
    # discrete averaged snapshots, transmit continuously and watch a live dBFS trace. Read the
    # noise/coupling floor off the trace before the target is illuminated, then read the
    # backscattered level once it is — both come off the same live plot.
    ui.label('Backscattered Power (Live)').classes('text-2xl font-bold text-center mt-6')
    ui.label('Press Start to transmit and stream live received power. Watch the trace settle to '
             'read the noise/coupling floor, then read the scattered level once the target is illuminated. '
             'Press Stop when done.').classes('text-base text-gray-600 text-center')

    dbfs_fig = go.Figure(go.Scatter(x=[], y=[], mode='lines', name='Received Power'))
    dbfs_fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis_title='Time (s)',
        yaxis_title='Power (dBFS)'
    )
    dbfs_live_plot = ui.plotly(dbfs_fig).classes('w-3/4 h-64 mx-auto')
    dbfs_current_label = ui.label('').classes('text-xl font-bold text-center mt-2')
    dbfs_stop_event = asyncio.Event()

    async def live_dbfs_update():
        t_values = []
        dbfs_values = []
        start_time = time.time()

        # Flush stale buffers before the first fresh reading, same as the old averaged measurement.
        for _ in range(N_DISCARD_BUFFERS):
            discard_buffer()

        while not dbfs_stop_event.is_set():
            t = time.time() - start_time
            try:
                dbfs = get_dBFS()
            except Exception as e:
                ui.notify(f'Failed to read dBFS: {e}', color='red')
                break

            t_values.append(t)
            dbfs_values.append(dbfs)
            t_values = t_values[-200:]
            dbfs_values = dbfs_values[-200:]

            dbfs_fig.data[0].x = t_values
            dbfs_fig.data[0].y = dbfs_values
            dbfs_live_plot.update()
            dbfs_current_label.set_text(f'Current: {dbfs:.2f} dBFS')

            await asyncio.sleep(0.05)

    def start_live_dbfs():
        if guard_unconfirmed():
            return
        if busy['value']:
            ui.notify('A live measurement is already running', type='warning')
            return
        try:
            tx()
        except Exception as e:
            ui.notify(f'Failed to start transmit: {e}', color='red')
            return
        set_busy(True)
        dbfs_stop_event.clear()
        asyncio.create_task(live_dbfs_update())
        start_dbfs_button.visible = False
        stop_dbfs_button.visible = True

    def stop_live_dbfs():
        stop_tx()
        dbfs_stop_event.set()
        set_busy(False)
        start_dbfs_button.visible = True
        stop_dbfs_button.visible = False
        ui.notify('Live measurement stopped', type='positive')

    with ui.row().classes('w-full justify-center gap-4 mt-4'):
        start_dbfs_button = ui.button('Start Live dBFS Plot', on_click=start_live_dbfs)
        lockable_elements.append(start_dbfs_button)
        stop_dbfs_button = ui.button('Stop', on_click=stop_live_dbfs)
        stop_dbfs_button.visible = False
