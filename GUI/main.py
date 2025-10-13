import time, serial, struct, serial.tools.list_ports
from nicegui import ui
from config import *
from AF_Calc import *

ui.add_head_html('''
<style>
    body {
        background-color: #f5f5f5;
    }
    .card {
        width: 25%;
        cursor: pointer;
        transition: opacity 0.2s;
    }
    .card:hover {
        opacity: 0.7;
    }
</style>
''')

def send_phases(port: str, phases: list[int]):
    """
    Connects to Arduino over serial and sends a list of 16 phase values.
    Args:
        port (str): Serial port, e.g., 'COM3' or '/dev/cu.usbmodem21201'
        phases (list[int]): List of 16 integers (0-360) for each element
    """
    try: 
        ser = serial.Serial(port, BAUDRATE)
        time.sleep(3)#wait for Arduino to reset
        
        # Send each phase as 2 bytes (big-endian unsigned short)
        packed = bytearray() 
        for val in phases:
            packed += val.to_bytes(2, byteorder='big') #b'x12/x34'
        #debug
        print(packed)
        ser.write(packed)    
        ui.notify(f'Successfully sent phases to Arduino on {port}')
    except Exception as e:
        ui.notify(f"failed to connect/send: {e}", color='red')
        print(e) 

# ---- LANDING PAGE ----
@ui.page('/')
def main_page():
#<TODO> Make these button images that describe what we will be doing for each and make thsoe images clickable
    images = [
    ('/manual', 'Manual_Phase_Control.png'), 
    ('/oam', 'OAM_Control.png'),
    ('/hermite', 'Hermite_Control.png'),
    ('/beam', 'Beam_Control.png')
    ]
    with ui.column().classes('w-full items-center'):
        ui.label('Antenna Array Control').classes('text-3xl font-bold mb-8')
    with ui.row().classes('w-full justify-center items-center gap-4'):
        for target, filename in images:
            ui.image(f'media/{filename}')\
                .classes('w-1/5 cursor-pointer hover:scale-105 transition-transform duration-200') \
                .on('click', lambda t=target: ui.navigate.to(t))

# ---- SUBPAGES ----
@ui.page('/manual')
def manual_page():
    ports = serial.tools.list_ports.comports()
    portsList = {p.device:f'{p.device} - {p.description}'for p in ports} 
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
            'Select Arduino Port from drop down menu'
            'Unused elements should remain at 0.'
        ).classes('text-base text-gray-600 text-center')
        # COM port
        com_input = ui.select(options = portsList, label = 'Select Arduino Port').style('width: 300px')
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

                                textbox.bind_value(slider)

                                sliders.append(slider)

            # Submit button
            ui.button('Submit', on_click=lambda: submit(sliders)).classes('mt-6')

    def submit(sliders):
        #ensure integer values
        values = [int(s.value) for s in sliders]
        port = com_input.value
        print(f'values are {values}')
        #SEND values to arduino
        send_phases(port, values)


#<TODO> Describe visually that the last 3 options default settings for a specific array
@ui.page('/oam')
def oam_page():
    ui.button('⬅ Back', on_click=ui.navigate.back)
    # Main content centered horizontally
    with ui.column().classes('w-full items-center  gap-6 mt-6'):
        # Header
        ui.label('Generate OAM') \
            .classes('text-2xl font-bold text-center')

        # Instructions
        ui.label('Attach provided 4x4 antenna array port 1 to top left ascending going down and to the right').classes('text-base text-gray-600 text-center')
@ui.page('/hermite')
def hermite_page():
    ui.label('Generate Hermite Gaussian')
    ui.button('⬅ Back', on_click=ui.navigate.back)

@ui.page('/beam')
def beam_page():
    ui.label('Beam Scanning (Receive Mode)')
    ui.button('⬅ Back', on_click=ui.navigate.back)
    with ui.row().classes('w-full justify-center items-center'):
        ui.button('Receive Mode', on_click=lambda: ui.navigate.to('/receive_mode')).\
        classes('w-64 h-24 text-xl')
        ui.button('Transmit Mode', on_click=lambda: ui.navigate.to('/transmit_mode')).\
        classes('w-64 h-24 text-xl')
     

    @ui.page('/transmit_mode')
    def transmit_mode():
        
        ports = serial.tools.list_ports.comports()
        portsList = {p.device:f'{p.device} - {p.description}'for p in ports}  


        # Back button in the top-left
        ui.button('⬅ Back', on_click=ui.navigate.back)
        with ui.column().classes('w-full'):
            with ui.row().classes('w-full justify-center items-center'):
                ui.label('Please connect the phase shifting network\
                with the following port order, then define your array parameters and steer angle')\
                .classes('text-base text-gray-600 text-center')


            with ui.row().classes('w-full justify-center items-center'):
                ui.image('media/Default_Array.png').style('width: 35%;')
                ui.image('media/Default_Array2.png').style('width: 35%;')
                com_input = ui.select(options = portsList, label = 'Select Arduino Port').style('width: 300px')
        

            with ui.row().classes('w-full justify-center items-center'):
                dx = ui.number(label = 'dx (λ)', value=0.5, min=0.1).style('width:20%')
                dy = ui.number(label = 'dy (λ)', value=0.5, min=0.1).style('width:20%')
                theta = ui.number(label = 'Theta (degrees)', value=0, min = 0, max=90).style('width:20%')
                phi = ui.number(label = 'Phi (degrees)', value=0, min = 0, max = 360).style('width:20%')
                 
            with ui.row().classes('w-full justify-center items-center'):
                submit_button = ui.button(
                    'Transmit',
                    on_click=lambda: Transmit()
                )
            image_container = ui.row().classes('w-full justify-center items-center').style('order:2;')

            def Transmit():
                '''
                Transmit with the main beam direction as defined by the user
                We should also have live elements where the user can move the rx antenna 
                to show relative magnitudes at different angles
                '''
                #show the user what the expected beam pattern
                beta_x, beta_y = runAF_Calc(dx.value,dy.value,theta.value,phi.value)
                
                image_container.clear() #remove any existing images
                with image_container:
                    ui.image('media/AF.png').style('width:45%;').force_reload()

                #TODO with beta_x and beta_y send the appropriate phases to the arduino
                '''  
                recall array elements are like
                1 2 3 4
                5 6 7 8
                9 10 11 12
                13 14 15 16
                where x goes down the rows and y goes across the columns
                ---->y
                |
                |
                |
                x
                ''' 
                phase_array = [None] * 16
                for M in range(4):
                    #iterate across a row with constant dx*M offset (0-3)
                    for N in range(4):
                        #iterate across columns with constant dy*N offset (0-3)
                        #example N = 3 M = 2 element address = 3 +4*2 = 11 ->index of 10th   
                        phase_array[N + 4*M] = int((np.rad2deg(beta_x) * M + np.rad2deg(beta_y) * N) % 360)
                send_phases(com_input.value, phase_array) 

    @ui.page('/receive_mode')
    def receive_mode():        
        
        def Scan_Beam():
            '''
            Scan through all combinations of theta and phi then report the direction
            of arival as a magnitude plot with a peak in the best link direction 
            '''
            pass
            


        # Back button in the top-left
        ui.button('⬅ Back', on_click=ui.navigate.back)
        with ui.column().classes('w-full'):
            with ui.row().classes('w-full justify-center items-center'):
                ui.label('Please connect the phase shifting network\
                with the following port order')\
                .classes('text-base text-gray-600 text-center')

            with ui.row().classes('w-full justify-center items-center'):
                ui.image('media/Default_Array.png').style('width: 45%;')
                ui.image('media/Default_Array2.png').style('width: 45%;')
            with ui.row().classes('w-full justify-center items-center'): 
                ui.label('Place the transmitting antenna somewhere within line\
                 of sight of the receiving array, then press start when you are ready to scan')\
                .classes('text-base text-gray-600 text-center')
                ui.button('Start', on_click=Scan_Beam)
    
# ---- RUN APP ----
ui.run(title="Phase Network Control Dashboard")

