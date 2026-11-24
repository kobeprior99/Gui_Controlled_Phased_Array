'''
main.py
Description:Entry point into gui 
Last Modified: Nov 24, 2026
'''
from nicegui import ui, app
from pages import home_router,calibrate_router, manual_router, beam_router, scattering_router2
import lifecycle

for r in (home_router, calibrate_router, manual_router, beam_router, scattering_router2):
    app.include_router(r)

lifecycle.register(app)

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="Phase Network Control Dashboard", reload=False)
