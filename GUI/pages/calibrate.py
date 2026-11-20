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

CAL_DIR = Path(__file__).resolve().parent.parent / 'Phase_Corrections'
router = APIRouter()

@router.page('/calibrate')
def calibrate():
    # Keep the Back button aligned to the top-left of the page
    with ui.row().classes('w-full'):
        ui.button('⬅ Back', on_click=ui.navigate.back)

    try: 
        helpers.send_phases(np.zeros(16, dtype=int), include_cp=False)
    except Exception as e:
        ui.notify(f'Failed to send phases: {e}', color='red')
    else:
        ui.notify('Zero phase sent successfully')

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
        files = sorted(p.name for p in CAL_DIR.glob('*.json'))

        with ui.dialog() as dialog, ui.card():
            ui.label('Select calibration file:')
            file_select = ui.select(
                options=files,
                label='Filename',
                with_input=True,
            ).classes('w-64')

            with ui.row():
                ui.button('Cancel', on_click=dialog.close)
                ui.button('Load', on_click=lambda: (
                    helpers.use_calibration_file(file_select.value),
                    dialog.close()
                ) if file_select.value else ui.notify('Pick a file first', type='warning'))
        dialog.open()

    # Main centered container for the page content
    with ui.column().classes('w-full max-w-3xl mx-auto items-center gap-4 px-4'):
        ui.label('Phase Calibration').classes('text-2xl font-bold text-center')
        
        # Basic instructions outside the dropdown
        ui.label(
            'This page automatically sets the phase of all phase shifters to zero. '
            'If you are not performing a new calibration, click "Load Calibration" below and select an existing file.'
        ).classes('text-base text-gray-700 text-center')

        # Collapsible dropdown for new calibration measurement steps
        with ui.expansion('New Calibration Measurement Steps', icon='info').classes('w-full border rounded-lg bg-gray-50'):
            ui.markdown('''
1. **Measure S-Parameters:** Measure the 2-port S-parameters of the phase shifting network where **Port 1** is the input port and **Port 2** connects to each of the output ports.
2. **Label Files:** Save each measurement as `Port1.S2P`, `Port2.S2P`, up to `Port16.S2P`.
3. **Place Folder:** Put all `.S2P` files into a single folder and place that folder inside the same directory as `main.py`. Then set S2PDIR = 'folder_name' in config.py
4. **Generate:** Click **Generate Calibration from S2P Folder** below to process the files
5. **Save:** Click **Save Calibration** below to save phase offsets the files.

            ''').classes('text-sm text-gray-700 p-2')

        # Action Buttons
        with ui.row().classes('justify-center gap-4 my-2'):
            ui.button('Save Calibration', on_click=prompt_save_calibration)
            ui.button('Load Calibration', on_click=prompt_use_calibration)
            ui.button('Generate Calibration from S2P Folder', on_click=helpers.gen_Cal_from_S2P)

        # Centered 4x4 Grid of Phase Inputs
        state.phase_inputs.clear()
        with ui.grid(columns=4).classes('gap-4 justify-items-center'):
            for i in range(16):
                num = ui.number(
                    label=f"Phase {i+1}",
                    value=state.PHASE_OFFSETS[i],
                    on_change=lambda e, i=i: helpers.update_phase(i, e.value),
                ).props("outlined dense step=0.1").style("width:100px;")
                state.phase_inputs.append(num)
