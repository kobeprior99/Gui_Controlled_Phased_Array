from nicegui import ui
from nicegui import ui

# ---- LANDING PAGE ----
@ui.page('/')
def main_page():
#<TODO> Make these button images that describe what we will be doing for each and make thsoe images clickable
    with ui.column():
        ui.label('Antenna Array Control').classes('text-3xl font-bold mb-8')
        ui.button('Manually Control Phase of each Element',
                  on_click=lambda: ui.navigate.to('/manual')).classes('nav-button')
        ui.button('Generate OAM',
                  on_click=lambda: ui.navigate.to('/oam')).classes('nav-button')
        ui.button('Generate Hermite Gaussian',
                  on_click=lambda: ui.navigate.to('/hermite')).classes('nav-button')
        ui.button('Beam Scanning (Receive Mode)',
                  on_click=lambda: ui.navigate.to('/beam')).classes('nav-button')


# ---- SUBPAGES ----
@ui.page('/manual')
def manual_page():
    #<TODO> Add 16 sliders to controll the phase of each output port
    ui.label('Manually Control Phase of each Element')
    ui.button('⬅ Back', on_click=ui.navigate.back)


#<TODO> Describe visually that the last 3 options default settings for a specific array
@ui.page('/oam')
def oam_page():
    ui.label('Generate OAM')
    ui.button('⬅ Back', on_click=ui.navigate.back)

@ui.page('/hermite')
def hermite_page():
    ui.label('Generate Hermite Gaussian')
    ui.button('⬅ Back', on_click=ui.navigate.back)

@ui.page('/beam')
def beam_page():
    ui.label('Beam Scanning (Receive Mode)')
    ui.button('⬅ Back', on_click=ui.navigate.back)


# ---- RUN APP ----
ui.run(title="Phase Network Control Dashboard")

