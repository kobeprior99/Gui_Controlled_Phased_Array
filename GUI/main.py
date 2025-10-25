"""
===============================================================================
 Title:        main.py
 Author:       Kobe Prior
 Description:  Main control interface for a low-cost 16-element phase shifter.
               
               This program provides a graphical user interface (GUI) built 
               with NiceGUI for calibrating and controlling an Arduino-driven
               phase shifting network.

               Users can:
                 - Manually set phase values for each element
                 - Load and save calibration data
                 - Generate predefined phase profiles for OAM and Hermite modes
                 - Perform beam steering and visualization
                    -Receive Mode (DOA Approximation)
                    -Transmit Mode (Psuedo Gain Pattern analysis)
               
               The system communicates with the Arduino over a serial interface,
               sending phase commands as packed bytes. 

               Designed for educational and research applications in phased array
               beamforming and the generation of structured waveforms.
===============================================================================
"""
#import all necessary libraries
import time, serial, struct, serial.tools.list_ports,json
from nicegui import ui
import numpy as np 
from config import *
import asyncio
from AF_Calc import *

#global serial handler
ser = None
#Phase offsets stored globally to be used across the program
PHASE_OFFSETS =np.zeros(16,dtype=int)
#flag to tell the user to calibrate if they haven't already
PHASE_CORRECTED = False 
#store reference to phase_input number boxes
phase_inputs = [] 

def update_phase(index:int, value:int):
    global PHASE_CORRECTED, PHASE_OFFSETS
    if value is None or value == '':
        return #ignore empty or None inputs
    try:
        PHASE_OFFSETS[index] = int(value) 
        PHASE_CORRECTED = True #set flag to true 

    except ValueError:
        pass #ignore invalid inputs

def update_phase_inputs():
    '''Referesh displayed UI numbers when phase_offsets changes.'''
    #only update changed fields 
    for i, (field, val) in enumerate(zip(phase_inputs, PHASE_OFFSETS)):
        if field.value !=val:
            field.value = val
def save_calibration(filename:str):
    '''
    Save the calibration as a json file to be used on later runs
    '''
    with open(f'{filename}.json', 'w') as f:
        json.dump(PHASE_OFFSETS.tolist(), f)
    ui.notify(f'Calibration saved successfully into {filename}.json!')

def use_calibration_file(filename:str):
    '''
    apply the calibration data from a json file
    '''
    global PHASE_OFFSETS, PHASE_CORRECTED
    try:
        with open(f'{filename}.json', 'r') as f:
            loaded_offsets = json.load(f)
        PHASE_OFFSETS = np.array(loaded_offsets,dtype = int)
        PHASE_CORRECTED = True
        update_phase_inputs() #refresh ui
        ui.notify(f'Calibration file: {filename}.json loaded and applied!')
    except FileNotFoundError:
        ui.notify(f"no calibration file: {filename}.json found")


SELECTED_COM_PORT = 'SELECT ARDUINO PORT' #global variable to store com selection
async def set_com_port(port:str):
    global SELECTED_COM_PORT,ser
    SELECTED_COM_PORT = port
    #debug
    #print(f'COM port set to {SELECTED_COM_PORT}')
    try:
        ser = serial.Serial(SELECTED_COM_PORT,BAUDRATE)
        await asyncio.sleep(3)#allow arduino to reset
    except Exception as e:
        print(f'Failed to open serial port: {e}')

# <TODO>: MAKE THIS THREADED SO ITS FASTER
def send_phases(phases: np.ndarray):
    """
    Connects to Arduino over serial and sends a list of 16 phase values.
    Phases are wrapped to 0-360 to ensure unsigned 2-byte transmission
    Args:
        phases (numpy array): List of 16 floats (0-360) for each element
    """
    #vectorized conversion to 8-bit 
    #scales degrees 0-360 to phase_words 0-255
    #snaps to nearest integer and modulo is implicit in type delcaration (handles negatives, and wrapping)
    #adding 0.5 ensures when type conversion happens we round to the nearest integer instead of truncating
    hardware_phases = np.uint8(((phases - PHASE_OFFSETS) * (255/360)) + 0.5)
    #send the phases
    ser.write(hardware_phases.tobytes()) 




# ---- LANDING PAGE ----
@ui.page('/')
def main_page():
    '''
    Main Page: where the user starts
    User can enter the arduino port at the very start
    The calibrate button will be blinking until the user performs calibration.
    ''' 
    #connect to arduino part one time at the main screen:

    ports = serial.tools.list_ports.comports()
    portsList = {p.device:f'{p.device} - {p.description}'for p in ports} 
    # COM port
    com_input = ui.select(
        options = portsList, 
        label =SELECTED_COM_PORT,
        on_change=lambda e: asyncio.create_task(set_com_port(e.value))
    ).style('width: 300px')

    images = [
    ('/manual', 'Manual_Phase_Control.png'), 
    ('/oam', 'OAM_Control.png'),
    ('/hermite', 'Hermite_Control.png'),
    ('/beam', 'Beam_Control.png'),
    ('/calibrate', 'Calibration.png')
    ]

    with ui.column().classes('w-full items-center'):
        ui.label('Antenna Array Control').classes('text-3xl font-bold mb-8')
    
    ui.add_head_html('''
        <style>
            /* === Subtle Blink Animation (opacity only) === */
            @keyframes blink {
              0%, 100% {
                opacity: 1;
              }
              50% {
                opacity: 0.4;
              }
            }

            /* === Blink Class === */
            .blink {
              animation: blink 1.2s ease-in-out infinite;
            }
        </style>
    ''')

    with ui.row().classes('w-full justify-center items-center gap-4'):
        for target, filename in images:
            classes_style = 'w-1/5 cursor-pointer hover:scale-105 transition-transform duration-200' 
            if target == images[len(images) - 1][0] and not PHASE_CORRECTED: 
                ui.image(f'media/{filename}')\
                    .classes(f'{classes_style} blink') \
                    .on('click', lambda t=target: navigate_if_ready(t))
            else:
                ui.image(f'media/{filename}')\
                    .classes(classes_style) \
                    .on('click', lambda t=target: navigate_if_ready(t))
    
    def navigate_if_ready(target):
        """Navigate only if a valid com is selected"""
        if SELECTED_COM_PORT == 'SELECT ARDUINO PORT':
            ui.notify("Please Select Arduino Port before proceeding.",color = 'red')
            return
        ui.navigate.to(target)

#---- END MAIN PAGE ----




# ---- SUBPAGES ----


# ---- manual phase shift page ----
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
            'Select Arduino Port from drop down menu'
            'Unused elements should remain at 0.'
        ).classes('text-base text-gray-600 text-center')
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

                                slider = ui.slider(min=0, max=360, value=0, step=(360/256)).classes('w-64')

                                textbox = ui.number(min=0, max=360, value=0, step=(360/256))\
                                    .props('dense underlined') \
                                    .classes('w-14 text-center text-sm align-middle')

                                textbox.bind_value(slider)

                                sliders.append(slider)

            # Submit button
            ui.button('Submit', on_click=lambda: submit(sliders)).classes('mt-6')

    def submit(sliders):
        #ensure integer values
        values = np.array([s.value for s in sliders])
        #debug 
        #print(f'values are {values}')
        #SEND values to arduino
        try: 
            send_phases(values)
        except Exception as e:
            ui.notify(f'Failed to send phases: {e}', color = 'red')
        else:
            ui.notify('Sucessfully sent phases')

#---- END Manual PAGE ----


#----OAM PAGE ----
@ui.page('/oam')
def oam_page():
    ui.button('⬅ Back', on_click = ui.navigate.back)
    # Main content centered horizontally
    with ui.column().classes('w-full items-center  gap-6 mt-6'):
        # Header
        ui.label('Generate OAM Beams') \
            .classes('text-2xl font-bold text-center')

        # Instructions
        ui.label('Attach provided 4x4 antenna array port 1 to top left ascending going down and to the right').classes('text-base text-gray-600 text-center')
        with ui.row().classes('w-full justify-center items-center'):
            ui.image('media/Default_Array_OAM.png').style('width: 35%;')
        ui.label('Create a Psuedo Circular Array by only attaching the highlighted elements').classes('text-base text-gray-600 text-center')

    
    images = [
    ('-3', 'oam-3.png'),
    ('-2', 'oam-2.png'), 
    ('-1', 'oam-1.png'),
    ('1', 'oam1.png'),
    ('2', 'oam2.png'),
    ('3', 'oam3.png')
    ]

    with ui.row().classes('w-full justify-center items-center gap-4'):
        for target, filename in images:
            ui.image(f'media/{filename}')\
                .classes('w-1/5 cursor-pointer hover:scale-105 transition-transform duration-200') \
                .on('click', lambda t=target: oam_mode(t))

        def oam_mode(mode: str):
            '''
            sends appropriate phases to generate oam beam
            Args: 
                mode(str): e.g. '-1' or '2'
            '''
            #default oam_1
            phases = np.array([
                0, 90, 45, 0, 135, 0, 0, 0, 180, 0, 0, 315, 0, 225, 270, 0
            ]) 
            if mode == '-3':
                phases *= -3

            if mode == '-2':
                #Mode =-2 
                phases *= -2

            elif mode == '-1':
                #Mode = -1
                phases *= -1

            elif mode == '1':
                #OAM mode 1
                pass 
            elif mode =='2':
                # Mode 2 
                phases *= 2

            else:
                #Mode = 3
                phases *= 3

            #send the appropriate phase
            try: 
                send_phases(phases)
            except Exception as e:
                ui.notify(f'Failed to send phases: {e}', color = 'red')
            else:
                ui.notify('Sucessfully sent phases')

#----END OAM MODE ----


#----HERMITE PAGE-----
@ui.page('/hermite')
def hermite_page():
    ui.button('⬅ Back', on_click=ui.navigate.back)
    with ui.column().classes('w-full items-center  gap-6 mt-6'):
        # Header
        ui.label('Generate Hermite Beams') \
            .classes('text-2xl font-bold text-center')

        # Instructions
        ui.label('Attach provided 4x4 antenna array port 1 to top left ascending going down and to the right').classes('text-base text-gray-600 text-center')
        with ui.row().classes('w-full justify-center items-center'):
            ui.image('media/Default_Array.png').style('width: 35%;')
            ui.image('media/Default_Array2.png').style('width: 35%;')

    images = [
    ('01', '01.png'), 
    ('10', '10.png'),
    ('11', '11.png'),
    ]
    with ui.row().classes('w-full justify-center items-center gap-4'):
        for target, filename in images:
            ui.image(f'media/{filename}')\
                .classes('w-1/5 cursor-pointer hover:scale-105 transition-transform duration-200') \
                .on('click', lambda t=target: hermite_mode(t))
    def hermite_mode(mode:str):
        '''
        sends the appropriate phases to generate hermite gaussian beam 
        Args: 
            mode (str) - requested hermite mode
        ''' 
        if mode == '01':
            '''
            mode 01 
            top 8 elements 0 degrees
            bottom 8 elements 180 degrees
            '''
            phases = np.array(
                [0,0,0,0,0,0,0,0,180,180,180,180,180,180,180,180
            ])
        elif mode == '10':
            '''
            mode 10
            left 8 elements 0 degrees
            right 8 elements 180 degrees
            '''
            phases = np.array(
                [0,0,180,180,0,0,180,180,0,0,180,180,0,0,180,180
            ])
        else:
            '''
            mode 11
            top-left 4 elements 0 degrees
            top-right 4 elements 180 degrees
            bottom-left 4 elements 180 degrees
            bottom-right 4 elements 0 degrees
            '''
            phases = np.array([
                0,0,180,180,0,0,180,180,180,180,0,0,180,180,0,0
            ]) 
    
        try: 
            send_phases(phases)
        except Exception as e:
            ui.notify(f'Failed to send phases: {e}', color = 'red')
        else:
            ui.notify('Sucessfully sent phases')
   
#---- END Hermite ----




#----Beam Steering----
@ui.page('/beam')
def beam_page():
    ui.label('Beam Scanning (Receive Mode)')
    ui.button('⬅ Back', on_click=ui.navigate.back)
    with ui.row().classes('w-full justify-center items-center'):
        ui.button('Receive Mode', on_click=lambda: ui.navigate.to('/receive_mode')).\
        classes('w-64 h-24 text-xl')
        ui.button('Transmit Mode', on_click=lambda: ui.navigate.to('/transmit_mode')).\
        classes('w-64 h-24 text-xl')
    
    
    #----Sub Pages----    

    #----Transmit Mode ----
    @ui.page('/transmit_mode')
    def transmit_mode():
        
        # Back button in the top-left
        ui.button('⬅ Back', on_click=ui.navigate.back)
        with ui.column().classes('w-full'):
            # Header
            ui.label('Transmit mode') \
                .classes('text-2xl font-bold text-center')
            with ui.row().classes('w-full justify-center items-center'):
                ui.label('Please connect the phase shifting network\
                with the following port order, then define your array parameters and steer angle')\
                .classes('text-base text-gray-600 text-center')


            with ui.row().classes('w-full justify-center items-center'):
                ui.image('media/Default_Array.png').style('width: 35%;')
                ui.image('media/Default_Array2.png').style('width: 35%;')
        

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
                    ui.image('media/AF.png').style('width:65%;').force_reload()

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
                phases = np.zeros(16)
                for M in range(4):
                    #iterate across a row with constant dx*M offset (0-3)
                    for N in range(4):
                        #iterate across columns with constant dy*N offset (0-3)
                        #example N = 3 M = 2 element address = 3 +4*2 = 11 ->index of 10th   
                        phases[N + 4*M] = (np.rad2deg(beta_x) * M + np.rad2deg(beta_y) * N) % 360
                try: 
                    send_phases(phases)
                except Exception as e:
                    ui.notify(f'Failed to send phases: {e}', color = 'red')
                else:
                    ui.notify('Sucessfully sent phases')
    #----END transmit page----


    #----Receive Mode page----

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
            # Header
            ui.label('Receive mode') \
                .classes('text-2xl font-bold text-center')
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
        

        #----Receive Mode page----



#----END BEAM Steering PAGE ----


#----Calibration Page----

@ui.page('/calibrate')
def calibrate():
    global phase_inputs
    #implement calibration page
    ui.button('⬅ Back', on_click=ui.navigate.back)
    #start by sending 0 phase to each port 
    try: 
        send_phases(np.zeros(16))
    except Exception as e:
        ui.notify(f'Failed to send phases: {e}', color = 'red')
    else:
        ui.notify('Zero phase sent successfully')

    with ui.column().classes('w-full'):
        with ui.row().classes('w-full justify-center items-center'):
            ui.label('Phase Calibration') \
                .classes('text-2xl font-bold text-center')
        with ui.row().classes('w-full justify-center items-center'):
            ui.label('The phase of each shifter is set to 0°.').classes('text-base text-gray-600 text-center')
            ui.label('Please connect the phase shifting network with to a VNA: Port 1 -> RFin and Port 2 ->  one of the 16 output ports.').classes('text-base text-gray-600 text-center')
            
            ui.label('Enter the phase (in degrees) from the S21 measurement for each port.').classes('text-base text-gray-600 text-center')
            
    def prompt_save_calibration():
        with ui.dialog() as dialog, ui.card():
            ui.label('Enter filename to save calibration (".json" will be added automatically):')
            filename_input = ui.input(label='Filename')
            with ui.row():
                ui.button('Cancel', on_click=dialog.close)
                ui.button('Save', on_click=lambda: (
                    save_calibration(filename_input.value.strip()),
                    dialog.close()
                ))
        dialog.open()

    def prompt_use_calibration():
        with ui.dialog() as dialog, ui.card():
            ui.label('Enter calibration filename (without ".json" if you prefer):')
            filename_input = ui.input(label='Filename')
            with ui.row():
                ui.button('Cancel', on_click=dialog.close)
                ui.button('Load', on_click=lambda: (
                    use_calibration_file(filename_input.value.strip()),
                    dialog.close()
                ))
        dialog.open()

    with ui.row().classes('justify-center gap-4 my-2'):
        ui.button('Save Calibration', on_click=prompt_save_calibration)
        ui.button('Load Calibration', on_click=prompt_use_calibration)
    #clear so we don't get more than 16 in phase_inputs
    phase_inputs.clear()
    # Display inputs in a 4x4 grid
    with ui.grid(columns=4).classes("gap-4"):
        for i in range(16):
            num = ui.number(
                label=f"Phase {i+1}",
                value=PHASE_OFFSETS[i],
                on_change=lambda e, i=i: update_phase(i, e.value),
            ).props("outlined dense step=0.1").style("width:100px;")
            phase_inputs.append(num)

#----END Calibration Page

# ---- RUN APP ---
ui.run(title="Phase Network Control Dashboard",reload=False)
#set reload=TRUE only during development, for deployment set false
