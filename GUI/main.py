from nicegui import ui
from nicegui import ui

# ---- GLOBAL STYLE ----
ui.add_head_html('''
<style>
    body {
        background: #f8f9fa;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .center-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 90vh;
        gap: 20px;
    }
    .nav-button {
        width: 400px;
        height: 100px;
        font-size: 1.3rem;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .nav-button:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.25);
    }
</style>
''')

# ---- LANDING PAGE ----
@ui.page('/')
def main_page():
    with ui.column().classes('center-container'):
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
    ui.label('Manually Control Phase of each Element').classes('text-2xl font-bold m-4')
    ui.button('⬅ Back', on_click=ui.navigate.back).classes('m-4')

@ui.page('/oam')
def oam_page():
    ui.label('Generate OAM').classes('text-2xl font-bold m-4')
    ui.button('⬅ Back', on_click=ui.navigate.back).classes('m-4')

@ui.page('/hermite')
def hermite_page():
    ui.label('Generate Hermite Gaussian').classes('text-2xl font-bold m-4')
    ui.button('⬅ Back', on_click=ui.navigate.back).classes('m-4')

@ui.page('/beam')
def beam_page():
    ui.label('Beam Scanning (Receive Mode)').classes('text-2xl font-bold m-4')
    ui.button('⬅ Back', on_click=ui.navigate.back).classes('m-4')


# ---- RUN APP ----
ui.run(title="Phase Network Control Dashboard")

