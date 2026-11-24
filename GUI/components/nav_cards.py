'''
nav_cards.py
Description: navigate between cards
Author: Kobe Prior
Date Last Modified: November 24, 2026
'''
import asyncio
from nicegui import ui
import state
from config import NAV_ITEMS
from create_default_rx_grid import ensure_default_rx_lut

BLINK_CSS = '''
<style>
  @keyframes blink { 0%,100%{opacity:1} 50%{opacity:.4} }
  .blink { animation: blink 1.2s ease-in-out infinite; }
</style>
'''

async def navigate_if_ready(target: str):
    if state.SELECTED_COM_PORT == 'SELECT MCU PORT':
        ui.notify("Please Select MCU Port before proceeding.", color='red')
        return
    if target == '/beam':
        try:
            _, ok = await asyncio.to_thread(ensure_default_rx_lut)
        except Exception:
            ok = False
        if not ok:
            ui.notify("MCU did not confirm the receive-scan table; scan will retry",
                      color='orange')
    ui.navigate.to(target)

def nav_cards():
    ui.add_head_html(BLINK_CSS)
    base = 'w-1/5 cursor-pointer hover:scale-105 transition-transform duration-200'
    with ui.row().classes('w-full justify-center items-center gap-4'):
        for i, (target, filename) in enumerate(NAV_ITEMS):
            needs_cal = (i == 0 and not state.PHASE_CORRECTED)
            ui.image(f'media/{filename}') \
                .classes(f'{base} blink' if needs_cal else base) \
                .on('click', lambda t=target: navigate_if_ready(t))
