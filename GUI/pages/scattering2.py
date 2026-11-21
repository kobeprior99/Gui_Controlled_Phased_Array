'''
Purpose: Run a scattering experiment 2 to find 
the existance of an orientation angle theta for a scattering object,
that when illuminated by a structured waveform produces higher back 
scattered power.
Author: Kobe Prior
Last Modified: November 20, 2026
'''
# pages/scattering.py
import asyncio
import csv
import io
import time
import numpy as np
from nicegui import APIRouter, ui
import plotly.graph_objects as go

from config import N_AVG_BUFFERS, N_DISCARD_BUFFERS, RX_GAIN, SETTLE_TIME_S, TX_GAIN
import helpers
from oam_phases import get_oam_phases
from PLUTO import discard_buffer, get_dBFS, set_gain, stop_tx, tx
import state

router = APIRouter()

#Columns
THETA_ANGLES = [-45.0,-30.0,-15.0,0.0, 15.0, 30.0, 45.0]
#Rows
WAVEFORM_ROWS = [
    {'id': 'LG_0_0', 'label': 'OAM 0 (PW)', 'kind': 'oam', 'code': '0'},
    {'id': 'LG_0_1', 'label': 'OAM 1', 'kind': 'oam', 'code': '1'},
    {'id': 'LG_0_-1', 'label': 'OAM -1', 'kind': 'oam', 'code': '-1'},
    {'id': 'LG_0_2', 'label': 'OAM 2', 'kind': 'oam', 'code': '2'},
    {'id': 'LG_0_-2', 'label': 'OAM -2', 'kind': 'oam', 'code': '-2'},
    {'id': 'HG_10',  'label': 'Hermite 10', 'kind': 'hermite', 'code': '10'},
]

async def oam_mode(mode: str, phase_confirmed: dict) -> bool:
    phases = get_oam_phases(mode)
    try:
        confirmed = await asyncio.to_thread(helpers.send_phases, phases, True)
    except Exception as e:
        confirmed = False
        ui.notify(f'Failed to send phases: {e}', color='red')
    phase_confirmed['value'] = confirmed
    if confirmed:
        ui.notify(f'Configured OAM mode {mode}', type='positive')
    else:
        ui.notify('Phases sent but not confirmed by MCU!', color='red')
    return confirmed


async def hermite_mode(mode: str, phase_confirmed: dict) -> bool:
    if mode == '01':
        phases = np.array([
            0, 0, 0, 0, 0, 0, 0, 0, 180, 180, 180, 180, 180, 180, 180, 180
        ])
    elif mode == '10':
        phases = np.array([
            0, 0, 180, 180, 0, 0, 180, 180, 0, 0, 180, 180, 0, 0, 180, 180
        ])
    else:
        phases = np.array([
            0, 0, 180, 180, 0, 0, 180, 180, 180, 180, 0, 0, 180, 180, 0, 0
        ])

    try:
        confirmed = await asyncio.to_thread(helpers.send_phases, phases, True)
    except Exception as e:
        confirmed = False
        ui.notify(f'Failed to send phases: {e}', color='red')
    phase_confirmed['value'] = confirmed
    if confirmed:
        ui.notify(f'Configured Hermite mode {mode}', type='positive')
    else:
        ui.notify('Phases sent but not confirmed by MCU!', color='red')
    return confirmed


@router.page('/scattering2')
def scattering2():
    ui.button('⬅ Back', on_click=helpers.nav_back)

    # ---- Busy & phase state ----
    busy = {'value': False}
    lockable_elements = []
    phase_confirmed = {'value': True}

    # ---- Live & peak dBFS tracking ----
    latest_dbfs = {'value': None}
    session_peak_dbfs = {'value': None}

    # ---- Measurement data store: keyed by (row_id, theta) ----
    # Each entry: {'peak_dbfs': float|None, 'psi_prime': float|None, 'noise_dbfs': float|None}
    measurements = {
        (row['id'], theta): {'peak_dbfs': None, 'psi_prime': None, 'noise_dbfs': None}
        for row in WAVEFORM_ROWS
        for theta in THETA_ANGLES
    }

    active_cell = {
        'row_id': WAVEFORM_ROWS[0]['id'],
        'theta': THETA_ANGLES[0],
    }
    noise_mode_enabled = {'value': False}
    image_elements = {}

    def set_busy(is_busy: bool):
        busy['value'] = is_busy
        for el in lockable_elements:
            el.disable() if is_busy else el.enable()
        for img in image_elements.values():
            if is_busy:
                img.classes('pointer-events-none opacity-50')
            else:
                img.classes(remove='pointer-events-none opacity-50')

    def guard_busy() -> bool:
        if busy['value']:
            ui.notify('A measurement is in progress, please wait', type='warning')
            return True
        return False

    def guard_unconfirmed() -> bool:
        if not phase_confirmed['value']:
            ui.notify('Last phase update was not confirmed by the MCU — reselect a mode before measuring', color='red')
            return True
        return False

    def get_row_meta(row_id: str) -> dict:
        return next(r for r in WAVEFORM_ROWS if r['id'] == row_id)

    def format_cell_display(row_id: str, theta: float) -> str:
        rec = measurements[(row_id, theta)]
        peak = rec['peak_dbfs']
        psi = rec['psi_prime']
        noise = rec['noise_dbfs']

        peak_str = f'{peak:.2f}' if peak is not None else '--'
        psi_str = f'{psi:.1f}°' if psi is not None else '--°'

        if peak is not None and noise is not None:
            above = peak - noise
            return f'{peak_str} ({above:+.2f} dB) | Ψ′={psi_str}'
        if noise is not None:
            return f'{peak_str} [N:{noise:.2f}] | Ψ′={psi_str}'
        return f'{peak_str} | Ψ′={psi_str}'

    def build_table_rows() -> list[dict]:
        rows = []
        for r in WAVEFORM_ROWS:
            entry = {'id': r['id'], 'waveform': r['label']}
            for theta in THETA_ANGLES:
                col_key = f'theta_{theta:g}'
                marker = '▶ ' if (active_cell['row_id'] == r['id'] and active_cell['theta'] == theta) else ''
                entry[col_key] = f'{marker}{format_cell_display(r["id"], theta)}'
            rows.append(entry)
        return rows

    # ---- Header & Array Diagram ----
    with ui.column().classes('w-full items-center gap-4 mt-4'):
        ui.label('Scattering Analysis').classes('text-2xl font-bold text-center')
        ui.label('Attach provided 4x4 antenna array port 1 to top left ascending going down and to the right').classes(
            'text-base text-gray-600 text-center'
        )
        with ui.row().classes('w-full justify-center items-center'):
            ui.image('media/Array_Configuration.png').style('width: 55%; max-width: 640px;')

    # ---- SDR Gain Controls ----
    ui.label('SDR Gain Controls').classes('text-xl font-bold text-center mt-4')

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

    with ui.card().classes('w-full max-w-2xl mx-auto p-4 mt-1'):
        with ui.column().classes('w-full gap-3'):
            with ui.row().classes('w-full items-center justify-between'):
                ui.label('RX Gain (dB):').classes('font-semibold')
                rx_label = ui.label(f'{RX_GAIN:.1f} dB').classes('font-mono')
            rx_slider = ui.slider(min=-1, max=73, step=1, value=RX_GAIN, on_change=update_rx_gain).classes('w-full')
            rx_slider.bind_value_to(rx_label, 'text', forward=lambda v: f'{v:.1f} dB')
            lockable_elements.append(rx_slider)

            with ui.row().classes('w-full items-center justify-between mt-1'):
                ui.label('TX Gain (dB):').classes('font-semibold')
                tx_label = ui.label(f'{TX_GAIN:.1f} dB').classes('font-mono')
            tx_slider = ui.slider(
                min=-89.75, max=0.0, step=0.25, value=TX_GAIN, on_change=update_tx_gain
            ).classes('w-full')
            tx_slider.bind_value_to(tx_label, 'text', forward=lambda v: f'{v:.1f} dB')
            lockable_elements.append(tx_slider)

    # ---- Beam Synthesizer (synced with active mode) ----
    oam_images = [
        ('-3', 'oam--3.png'),
        ('-2', 'oam-2.png'),
        ('-1', 'oam-1.png'),
        ('1', 'oam1.png'),
        ('2', 'oam2.png'),
        ('3', 'oam3.png'),
        ('0', 'plane_wave.png'),
    ]
    hermite_images = [
        ('01', '01.png'),
        ('10', '10.png'),
        ('11', '11.png'),
    ]

    def highlight_mode_card(kind: str, code: str):
        key = f'{kind}:{code}'
        if state.selected is not None and state.selected in image_elements:
            image_elements[state.selected].classes(remove='ring-4 ring-red-500')
        if key in image_elements:
            image_elements[key].classes('ring-4 ring-red-500')
        state.selected = key

    async def apply_waveform(kind: str, code: str):
        if guard_busy():
            return False
        highlight_mode_card(kind, code)
        if kind == 'oam':
            return await oam_mode(code, phase_confirmed)
        return await hermite_mode(code, phase_confirmed)

    ui.label('Beam synthesizer').classes('text-lg font-bold text-center mt-4')
    with ui.row().classes('w-full justify-center items-center gap-2 flex-wrap'):
        for target, filename in oam_images:
            img = (
                ui.image(f'media/{filename}')
                .classes('w-28 cursor-pointer hover:scale-105 transition-transform duration-200')
                .on('click', lambda _, t=target: apply_waveform('oam', t))
            )
            image_elements[f'oam:{target}'] = img

        for target, filename in hermite_images:
            img = (
                ui.image(f'media/{filename}')
                .classes('w-28 cursor-pointer hover:scale-105 transition-transform duration-200')
                .on('click', lambda _, t=target: apply_waveform('hermite', t))
            )
            image_elements[f'hermite:{target}'] = img

    # ---- Measurement Matrix Table & Noise/Coupling Workflow ----
    ui.separator().classes('my-6')
    ui.label('Theta (Θ) × Waveform Measurement Matrix').classes('text-2xl font-bold text-center')
    ui.label(
        'Click any cell to select it and configure its waveform on the MCU. '
        'Record peak backscattered dBFS and array angle Ψ′, then toggle Noise/Coupling Mode after removing the scatterer.'
    ).classes('text-sm text-gray-600 text-center max-w-3xl mx-auto')

    columns = [{'name': 'waveform', 'label': 'Waveform', 'field': 'waveform', 'align': 'left'}] + [
        {
            'name': f'theta_{theta:g}',
            'label': f'Θ = {theta:g}°',
            'field': f'theta_{theta:g}',
            'align': 'center',
        }
        for theta in THETA_ANGLES
    ]

    matrix_table = ui.table(
        columns=columns,
        rows=build_table_rows(),
        row_key='id',
    ).classes('w-full max-w-5xl mx-auto mt-2')
    lockable_elements.append(matrix_table)

    # Forward-declared UI updaters for active cell & noise guide
    active_cell_badge = ui.label('').classes('text-base font-bold text-blue-700')
    peak_input = ui.number(label='Peak Backscattered (dBFS)', step=0.01, format='%.2f').classes('w-64')
    psi_input = ui.number(label='Array Angle Ψ′ (deg)', step=1.0, format='%.1f').classes('w-60')
    noise_input = ui.number(label='Noise / Coupling (dBFS)', step=0.01, format='%.2f').classes('w-64')
    above_noise_label = ui.label('Above Noise/Coupling: -- dB').classes('font-mono text-sm font-semibold')
    noise_guide_banner = ui.label('').classes('text-sm font-semibold text-amber-800')
    psi_targets_summary = ui.label('').classes('text-xs text-gray-700 font-mono')

    def sync_editor_from_active_cell():
        r_id = active_cell['row_id']
        th = active_cell['theta']
        row_meta = get_row_meta(r_id)
        rec = measurements[(r_id, th)]

        active_cell_badge.set_text(f'Active Cell: {row_meta["label"]} @ Θ = {th:g}°')
        peak_input.value = rec['peak_dbfs']
        psi_input.value = rec['psi_prime']
        noise_input.value = rec['noise_dbfs']

        if rec['peak_dbfs'] is not None and rec['noise_dbfs'] is not None:
            diff = rec['peak_dbfs'] - rec['noise_dbfs']
            above_noise_label.set_text(f'Above Noise/Coupling: {diff:+.2f} dB')
        else:
            above_noise_label.set_text('Above Noise/Coupling: -- dB')

        if rec['psi_prime'] is not None:
            noise_guide_banner.set_text(
                f'Noise/Coupling Target for this cell: rotate array to Ψ′ = {rec["psi_prime"]:.1f}° (scatterer removed)'
            )
        else:
            noise_guide_banner.set_text(
                f'No Ψ′ recorded yet for {row_meta["label"]} @ Θ = {th:g}° — enter Ψ′ or pick a recorded angle below'
            )

        recorded_psis = []
        for r in WAVEFORM_ROWS:
            for t in THETA_ANGLES:
                p = measurements[(r['id'], t)]['psi_prime']
                if p is not None:
                    recorded_psis.append(f'{r["label"].split()[0]}/Θ{t:g}°→Ψ′={p:.1f}°')
        psi_targets_summary.set_text(
            'Recorded Ψ′ targets: ' + (', '.join(recorded_psis) if recorded_psis else 'None yet')
        )

    def refresh_table_and_editor():
        matrix_table.rows = build_table_rows()
        matrix_table.update()
        sync_editor_from_active_cell()

    async def select_matrix_cell(row_id: str, theta: float):
        if guard_busy():
            return
        active_cell['row_id'] = row_id
        active_cell['theta'] = theta
        refresh_table_and_editor()

        row_meta = get_row_meta(row_id)
        await apply_waveform(row_meta['kind'], row_meta['code'])

    for theta in THETA_ANGLES:
        col_key = f'theta_{theta:g}'
        slot_markup = f'''
            <q-td :props="props" class="cursor-pointer hover:bg-blue-50"
                  @click="() => $parent.$emit('select_cell', {{ row_id: props.row.id, theta: {theta} }})">
                {{{{ props.value }}}}
            </q-td>
        '''
        matrix_table.add_slot(f'body-cell-{col_key}', slot_markup)

    async def on_select_cell(e):
        args = e.args or {}
        if 'row_id' in args and 'theta' in args:
            await select_matrix_cell(args['row_id'], float(args['theta']))

    matrix_table.on('select_cell', on_select_cell)

    def save_active_cell_values():
        rec = measurements[(active_cell['row_id'], active_cell['theta'])]
        rec['peak_dbfs'] = float(peak_input.value) if peak_input.value is not None else None
        rec['psi_prime'] = float(psi_input.value) if psi_input.value is not None else None
        rec['noise_dbfs'] = float(noise_input.value) if noise_input.value is not None else None
        refresh_table_and_editor()
        ui.notify('Saved cell measurement', type='positive')

    def fill_noise_for_matching_psi():
        target_psi = (
            float(psi_input.value)
            if psi_input.value is not None
            else measurements[(active_cell['row_id'], active_cell['theta'])]['psi_prime']
        )
        noise_val = (
            float(noise_input.value)
            if noise_input.value is not None
            else measurements[(active_cell['row_id'], active_cell['theta'])]['noise_dbfs']
        )

        if target_psi is None:
            ui.notify('Enter or record a Ψ′ angle first before filling matching Ψ′ noise', type='warning')
            return
        if noise_val is None:
            ui.notify('Enter or capture a Noise/Coupling dBFS value first', type='warning')
            return

        active_rec = measurements[(active_cell['row_id'], active_cell['theta'])]
        if psi_input.value is not None:
            active_rec['psi_prime'] = target_psi
        active_rec['noise_dbfs'] = noise_val

        updated_count = 0
        active_row_id = active_cell['row_id']
        for r in WAVEFORM_ROWS:
            if r['id'] != active_row_id:
                continue
            for th in THETA_ANGLES:
                rec = measurements[(r['id'], th)]
                if rec['psi_prime'] is not None and abs(rec['psi_prime'] - target_psi) < 1e-6:
                    rec['noise_dbfs'] = noise_val
                    updated_count += 1

        refresh_table_and_editor()
        ui.notify(
            f'Applied noise {noise_val:.2f} dBFS to {updated_count} cell(s) with Ψ′ = {target_psi:.1f}°',
            type='positive',
        )

    def capture_dbfs_to_active(use_peak: bool):
        val = session_peak_dbfs['value'] if use_peak else latest_dbfs['value']
        if val is None:
            ui.notify('No dBFS reading available yet — start the live plot first or enter manually', type='warning')
            return
        if noise_mode_enabled['value']:
            noise_input.value = round(val, 2)
            measurements[(active_cell['row_id'], active_cell['theta'])]['noise_dbfs'] = round(val, 2)
        else:
            peak_input.value = round(val, 2)
            measurements[(active_cell['row_id'], active_cell['theta'])]['peak_dbfs'] = round(val, 2)
        refresh_table_and_editor()
        ui.notify(f'Captured {val:.2f} dBFS', type='positive')

    def on_noise_switch_change(e):
        noise_mode_enabled['value'] = bool(e.value)
        sync_editor_from_active_cell()
        if e.value:
            ui.notify(
                'Noise & Coupling mode ON: remove scatterer and rotate array to target Ψ′ angle(s)',
                type='info',
            )
        else:
            ui.notify('Scattering peak measurement mode ON', type='info')

    def export_csv():
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            'Waveform', 'Theta_deg', 'Psi_prime_deg',
            'Peak_dBFS', 'Noise_Coupling_dBFS', 'Above_Noise_Coupling_dB'
        ])
        for r in WAVEFORM_ROWS:
            for theta in THETA_ANGLES:
                rec = measurements[(r['id'], theta)]
                above = (
                    f'{rec["peak_dbfs"] - rec["noise_dbfs"]:.4f}'
                    if rec['peak_dbfs'] is not None and rec['noise_dbfs'] is not None
                    else ''
                )
                writer.writerow([
                    r['label'],
                    theta,
                    rec['psi_prime'] if rec['psi_prime'] is not None else '',
                    rec['peak_dbfs'] if rec['peak_dbfs'] is not None else '',
                    rec['noise_dbfs'] if rec['noise_dbfs'] is not None else '',
                    above,
                ])
        ui.download(buf.getvalue().encode('utf-8'), filename='scattering_measurements.csv')

    with ui.card().classes('w-full max-w-5xl mx-auto p-4 mt-4'):
        with ui.row().classes('w-full items-center justify-between flex-wrap gap-4'):
            active_cell_badge
            noise_switch = ui.switch(
                'Noise & Coupling Mode (Scatterer Removed)',
                value=False,
                on_change=on_noise_switch_change,
            )
            lockable_elements.append(noise_switch)

        noise_guide_banner
        psi_targets_summary

        with ui.row().classes('w-full items-end gap-3 flex-wrap mt-3'):
            peak_input
            psi_input
            noise_input
            above_noise_label

        with ui.row().classes('w-full items-center gap-2 flex-wrap mt-3'):
            cap_peak_btn = ui.button('Capture Session Peak', on_click=lambda: capture_dbfs_to_active(True))
            cap_curr_btn = ui.button('Capture Current dBFS', on_click=lambda: capture_dbfs_to_active(False))
            save_cell_btn = ui.button('Save Cell', on_click=save_active_cell_values).props('color=primary')
            fill_psi_noise_btn = ui.button(
                'Fill Noise for Matching Ψ′',
                on_click=fill_noise_for_matching_psi,
            ).props('color=secondary')
            export_btn = ui.button('Export CSV', on_click=export_csv).props('outline')
            lockable_elements.extend([cap_peak_btn, cap_curr_btn, save_cell_btn, fill_psi_noise_btn])

    # ---- Live dBFS Power Plot ----
    ui.label('Backscattered Power (Live)').classes('text-2xl font-bold text-center mt-6')
    ui.label(
        'Press Start to transmit and stream live received power. Rotate the array to find peak power (Ψ′) '
        'with the scatterer present, or measure background noise/coupling with the scatterer removed.'
    ).classes('text-base text-gray-600 text-center max-w-3xl mx-auto')

    with ui.row().classes('w-full justify-center items-center gap-4 mt-2'):
        y_min = ui.number(label='Set Minimum Power for Graph (dBFS)', value=-100, max=0).style('width:28%')
        y_max = ui.number(label='Set Maximum Power for Graph (dBFS)', value=0, max=10).style('width:28%')

    fig = go.Figure(go.Scatter(x=[], y=[], mode='lines', name='Received Energy'))
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis_title='Time(s)',
        yaxis_title='Avg Power Received (dBFS)',
    )
    with ui.row().classes('w-full justify-center items-center no-wrap mt-2'):
        live_plot = ui.plotly(fig).classes('w-3/4 h-64')
        with ui.card().classes('w-52 items-center p-4 gap-2'):
            ui.label('Current Level').classes('text-xs text-gray-600')
            dbfs_label = ui.label('-- dBFS').classes('font-mono text-2xl font-bold')
            ui.separator()
            ui.label('Session Peak').classes('text-xs text-gray-600')
            peak_readout_label = ui.label('-- dBFS').classes('font-mono text-lg font-semibold text-blue-700')
            reset_peak_btn = ui.button(
                'Reset Peak',
                on_click=lambda: (
                    session_peak_dbfs.update({'value': latest_dbfs['value']}),
                    peak_readout_label.set_text(
                        f'{latest_dbfs["value"]:.1f} dBFS' if latest_dbfs['value'] is not None else '-- dBFS'
                    ),
                ),
            ).props('flat dense size=sm')

    dbfs_stop_event = asyncio.Event()

    async def live_dbfs_update():
        t_values = []
        dBFS_values = []
        start_time = time.time()
        session_peak_dbfs['value'] = None
        peak_readout_label.set_text('-- dBFS')

        for _ in range(N_DISCARD_BUFFERS):
            discard_buffer()

        while not dbfs_stop_event.is_set():
            t = time.time() - start_time
            try:
                dBFS = get_dBFS()
            except Exception as e:
                ui.notify(f'Failed to read dBFS: {e}', color='red')
                break

            latest_dbfs['value'] = dBFS
            if session_peak_dbfs['value'] is None or dBFS > session_peak_dbfs['value']:
                session_peak_dbfs['value'] = dBFS
                peak_readout_label.set_text(f'{dBFS:.1f} dBFS')

            dbfs_label.set_text(f'{dBFS:.1f} dBFS')
            t_values = (t_values + [t])[-100:]
            dBFS_values = (dBFS_values + [dBFS])[-100:]

            fig.data[0].x = t_values
            fig.data[0].y = dBFS_values

            try:
                fig.update_yaxes(type='linear', range=[float(y_min.value), float(y_max.value)])
            except Exception:
                pass

            live_plot.update()
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

    with ui.row().classes('w-full justify-center gap-4 mt-4 mb-8'):
        start_dbfs_button = ui.button('Start Live dBFS Plot', on_click=start_live_dbfs)
        lockable_elements.append(start_dbfs_button)
        stop_dbfs_button = ui.button('Stop', on_click=stop_live_dbfs)
        stop_dbfs_button.visible = False

    sync_editor_from_active_cell()
