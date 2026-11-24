'''
menu.py
Description: chose from trnasmit and receive mode
Author: Kobe Prior
Date Last Modified: Nov24, 2026
'''
import helpers
from nicegui import ui
from ._router import router

@router.page('/beam')
def beam_page():
    ui.button('⬅ Back', on_click=helpers.nav_back)
    with ui.row().classes('w-full justify-center items-center'):
        ui.button('Receive Mode', on_click=lambda: ui.navigate.to('/receive_mode')).classes('w-64 h-24 text-xl')
        ui.button('Transmit Mode', on_click=lambda: ui.navigate.to('/transmit_mode')).classes('w-64 h-24 text-xl')
    with ui.row().classes('w-full justify-center items-center'):
        ui.image('media/Beam_Explanation.png')
