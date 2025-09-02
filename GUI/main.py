from nicegui import ui
import serial
import struct
from config import *

def send_array(ser, arr):
    """
    Sends array over serial to arduino
    Args:
        ser(Serial):serial connection between computer and arduino
        arr(list): 16 phases for each element
    """
    #send each value as 2 bytes (big-endian) 2-byte integer
    for val in arr:       
        ser.write(struct.pack('>H', v))#'>H' = big-endian unsigned short

def connect_serial(port, data):
    """
    Connects to serial and sends data to arduino in byte format
    Args:
        port (string): the port to connect to the arduino
        data (list): 16 phases in degrees
    """ 
    baudrate = 115200
    try:
        ser = serial.Serial(port, BAUDRATE, timeout=1)
        ui.notify(f'Successfully connected to {port}')
        #send data
        send_array(ser, data) 
        #close serial
        ser.close() 
    except Exception as e:
         ui.notify(f'Failed to connect: {e}', color='red')


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
    # Back button in the top-left
    ui.button('⬅ Back', on_click=ui.navigate.back)

    # Main content centered horizontally
    with ui.column().classes('w-full items-center  gap-6 mt-6'):
        # Header
        ui.label('Manually Control Phase of Each Element') \
            .classes('text-2xl font-bold text-center')

        # Instructions
        ui.label(
            'Enter the phase in degrees (0–360) for each element. '
            'Unused elements should remain at 0.'
            'Find the COM port of Arduino (Easliy found in arduino ide or device manager)'
        ).classes('text-base text-gray-600 text-center')
        # COM port
        com_input = ui.input(label = 'Enter Arduino Port',placeholder = 'e.g. COM3 or /dev/cu.usbmodem21201').style('width: 300px')
        # Sliders in two columns
        sliders = []
        with ui.column().classes('w-full items-center gap-6 mt-6'):
            with ui.row().classes('gap-12 mt-6'):
                for col in range(2):
                    with ui.column().classes('gap-4'):
                        for i in range(8):
                            element_index = col * 8 + i
                            with ui.row().classes('items-center gap-4'):
                                ui.label(f'Element {element_index + 1}').classes('w-28')

                                slider = ui.slider(min=0, max=360, value=0, step=1).classes('w-64')

                                textbox = ui.number(min=0, max=360, value=0) \
                                    .props('dense underlined') \
                                    .classes('w-14 text-center text-sm align-middle')

                                slider.bind_value(textbox)
                                textbox.bind_value(slider)

                                sliders.append(slider)

            # Submit button
            ui.button('Submit', on_click=lambda: submit(sliders)).classes('mt-6')

    def submit(sliders):
        values = [s.value for s in sliders]
        port = com_input.value
        print(f'values are {values}')
        #SEND values to arduino
        connect_serial(port, values) 
        ui.notify(f'values sent to Arduino: {values}')


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

