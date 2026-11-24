from nicegui import ui
from config import RX_GAIN, TX_GAIN
from PLUTO import set_gain


def gain_slider(name, kwarg, lo, hi, step, initial):
    def on_change(e):
        try:
            set_gain(**{kwarg: e.value})
        except Exception as err:
            ui.notify(f'Failed to set {name} gain: {err}', color='red')

    with ui.card().classes('w-full max-w-2xl mx-auto p-4 mt-2'):
        with ui.row().classes('w-full items-center justify-between'):
            ui.label(f'{name} Gain (dB):').classes('font-semibold text-lg')
            label = ui.label(f'{initial:.1f} dB').classes('font-mono text-lg')
        slider = ui.slider(min=lo, max=hi, step=step, value=initial,
                           on_change=on_change).classes('w-full')
        slider.bind_value_to(label, 'text', forward=lambda v: f'{v:.1f} dB')


def tx_gain_slider():
    gain_slider('TX', 'tx_gain', -89.75, 0.0, 0.25, TX_GAIN)


def rx_gain_slider():
    gain_slider('RX', 'rx_gain', -1, 73, 1, RX_GAIN)
