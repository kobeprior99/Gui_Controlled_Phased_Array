'''
Purpose: the calibration page is used to remove any persistent phase
offset induced on each channel due to mismatched electrical lengths
Author: Kobe Prior
Last Edited: July 17 2026
'''
import numpy as np
from nicegui import APIRouter, ui
import state
import helpers
from pathlib import Path
from config import DEFAULT_CAL
CAL_DIR = Path(__file__).resolve().parent.parent / 'Phase_Corrections'
router = APIRouter()

@router.page('/calibrate')
def calibrate():
    ui.button('⬅ Back', on_click=ui.navigate.back)
    try: 
        helpers.send_phases(np.zeros(16, dtype=int))
    except Exception as e:
        ui.notify(f'Failed to send phases: {e}', color='red')
    else:
        ui.notify('Zero phase sent successfully')

    with ui.column().classes('w-full'):
        with ui.row().classes('w-full justify-center items-center'):
            ui.label('Phase Calibration').classes('text-2xl font-bold text-center')
        with ui.row().classes('w-full justify-center items-center'):
            ui.label('The phase of each shifter is set to 0°.').classes('text-base text-gray-600 text-center')
            ui.label('Please Load Default Calibration File...').classes('text-base text-gray-600 text-center')

    def prompt_save_calibration():
        with ui.dialog() as dialog, ui.card():
            ui.label('Enter filename to save calibration:')
            filename_input = ui.input(label='Filename')
            with ui.row():
                ui.button('Cancel', on_click=dialog.close)
                ui.button('Save', on_click=lambda: (
                    helpers.save_calibration(filename_input.value.strip()),
                    dialog.close()
                ))
        dialog.open()


    def prompt_use_calibration():
        files = sorted(p.name for p in CAL_DIR.glob('*.json'))  # adjust the extension/pattern

        with ui.dialog() as dialog, ui.card():
            ui.label('Select calibration file:')
            file_select = ui.select(
                options=files,
                label='Filename',
                with_input=True,   # lets you type to filter the list
            ).classes('w-64')

            with ui.row():
                ui.button('Cancel', on_click=dialog.close)
                ui.button('Load', on_click=lambda: (
                    helpers.use_calibration_file(file_select.value),
                    dialog.close()
                ) if file_select.value else ui.notify('Pick a file first', type='warning'))
        dialog.open()

    with ui.row().classes('justify-center gap-4 my-2'):
        ui.button('Save Calibration', on_click=prompt_save_calibration)
        ui.button('Load Calibration', on_click=prompt_use_calibration)
        ui.button('Generate Calibration from S2P Folder', on_click=helpers.gen_Cal_from_S2P)

    state.phase_inputs.clear()
    with ui.grid(columns=4).classes("gap-4"):
        for i in range(16):
            num = ui.number(
                label=f"Phase {i+1}",
                value=state.PHASE_OFFSETS[i],
                on_change=lambda e, i=i: helpers.update_phase(i, e.value),
            ).props("outlined dense step=0.1").style("width:100px;")
            state.phase_inputs.append(num)
