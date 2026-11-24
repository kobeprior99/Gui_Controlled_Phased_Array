#transmit.py
import asyncio
import time
import plotly.graph_objects as go
from nicegui import ui, background_tasks

import helpers
from AF_Calc import runAF_Calc, get_spacing
from PLUTO import get_dBFS, tx, stop_tx
from components.gain_slider import tx_gain_slider
from ._router import router


@router.page('/transmit_mode')
def transmit_mode():
    ui.button('⬅ Back', on_click=helpers.nav_back)
    with ui.column().classes('w-full'):
        ui.label('Transmit mode').classes('text-2xl font-bold text-center')
        with ui.row().classes('w-full justify-center items-center'):
            ui.label('Please connect the phase shifting network with the following port order, '
                     'then define your array parameters and steer angle') \
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

        ui.label('SDR Gain Controls').classes('text-2xl font-bold text-center mt-6')
        tx_gain_slider()

        fig = go.Figure(go.Scatter(x=[], y=[], mode='lines', name='Received Energy'))
        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis_title='Time(s)',
            yaxis_title='Avg Power Received (dBFS)',
        )
        with ui.row().classes('w-full justify-center items-center no-wrap'):
            live_plot = ui.plotly(fig).classes('w-3/4 h-64')
            with ui.card().classes('w-48 items-center p-4'):
                ui.label('Current Level').classes('text-sm text-gray-600')
                dbfs_label = ui.label('-- dBFS').classes('font-mono text-3xl font-bold')

        image_container = ui.row().classes('justify-center items-center').style('order:2; width:90%;')
        stop_event = asyncio.Event()
        running = {'value': False}

        def refresh_images():
            image_container.clear()
            with image_container:
                ui.image('media/AF.png').style('width:40%;').force_reload()
                ui.image('media/uv.png').style('width:40%;').force_reload()

        def send_current_phase():
            phases = runAF_Calc(dx.value, dy.value, theta.value, phi.value)
            helpers.send_phases(phases)
            refresh_images()

        async def live_update():
            t_values, dBFS_values = [], []
            start_time = time.time()

            while not stop_event.is_set():
                dBFS = get_dBFS()
                dbfs_label.set_text(f'{dBFS:.1f} dBFS')
                t_values.append(time.time() - start_time)
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

        def start_live_plot():
            if running['value']:
                send_current_phase()   # already transmitting: just steer
                return
            send_current_phase()
            tx()
            running['value'] = True
            stop_event.clear()
            background_tasks.create(live_update())
            new_angle_button.visible = True
            stop_button.visible = True

        def stop_live():
            stop_tx()
            stop_event.set()
            running['value'] = False
            ui.notify('Live plot stopped', type='positive')

        def on_disconnect():
            '''Page closed or navigated away: don't leave the transmitter on.'''
            stop_event.set()
            if running['value']:
                running['value'] = False
                stop_tx()

        ui.context.client.on_disconnect(on_disconnect)

        with ui.row().classes('w-full justify-center gap-4 mt-4'):
            ui.button('Transmit & Live Plot', on_click=start_live_plot)
            new_angle_button = ui.button('New Angle', on_click=send_current_phase)
            new_angle_button.visible = False
            stop_button = ui.button('Stop', on_click=stop_live)
            stop_button.visible = False
