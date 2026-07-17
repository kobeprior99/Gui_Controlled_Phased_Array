import numpy as np
from nicegui import APIRouter, ui
import helpers

router = APIRouter()

@router.page('/manual')
def manual_page():
    ui.button('⬅ Back', on_click=ui.navigate.back)
    
    with ui.column().classes('w-full items-center gap-6 mt-6'):
        ui.label('Manually Control Phase of Each Element').classes('text-2xl font-bold text-center')

        sliders = []
        with ui.row().classes('gap-12 mt-6'):
            for col in range(2):
                with ui.column().classes('gap-4'):
                    for i in range(8):
                        element_index = col * 8 + i
                        with ui.row().classes('items-center gap-4'):
                            ui.label(f'Element {element_index + 1}').classes('w-28')
                            slider = ui.slider(min=0, max=360, value=0, step=(360/256)).classes('w-64')
                            textbox = ui.number(min=0, max=360, value=0, step=(360/256)).props('dense underlined').classes('w-14 text-center text-sm')
                            textbox.bind_value(slider)
                            sliders.append(slider)

        ui.button('Submit', on_click=lambda: submit(sliders)).classes('mt-6')

    def submit(sliders):
        values = np.array([float(s.value) for s in sliders])
        try: 
            helpers.send_phases(values)
        except Exception as e:
            ui.notify(f'Failed to send phases: {e}', color='red')
        else:
            ui.notify('Successfully sent phases', timeout=1)
