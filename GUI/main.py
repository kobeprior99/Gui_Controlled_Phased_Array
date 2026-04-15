"""
===============================================================================
 Title:        main.py
 Author:       Kobe Prior
 Description:  Main control interface for a low-cost 16-element phase shifter.
               
               This program provides a graphical user interface (GUI) built 
               with NiceGUI for calibrating and controlling an MCU-driven
               phase shifting network.

               Users can:
                 - Manually set phase values for each element
                 - Load and save calibration data
                 - Generate predefined phase profiles for OAM and Hermite modes
                 - Perform beam steering and visualization
                    -Receive Mode (AOA Approximation)
                    -Transmit Mode (Psuedo Gain Pattern analysis)
               
               The system communicates with the MCU over a serial interface,
               sending phase commands as packed bytes. 

               Designed for educational and research applications in phased array
               beamforming and the generation of structured waveforms.

===============================================================================
"""
#import all necessary libraries
import time, serial, struct, serial.tools.list_ports, json, os
from nicegui import ui,app
import numpy as np 
from config import OAM_PHASES,BAUDRATE, DX, DY, THETA_RANGE, PHI_RANGE, FREQ,SETTLE_TIME
import matplotlib
import matplotlib.pyplot as plt
import asyncio
from AF_Calc import runAF_Calc
from READ_S2P import get_phase_at_freq
from create_default_rx_grid import DEFAULT_RX_GRID
from PLUTO import get_energy,get_mean_dev, get_energy_fast,discard_buffer, tx, stop_tx, moving_average
import plotly.graph_objects as go
MEDIA_DIR = os.path.join(os.path.dirname(__file__), 'media')
#global serial handler
ser = None
#Phase offsets stored globally to be used across the program
PHASE_OFFSETS =np.zeros(16,dtype=float)
#flag to tell the user to calibrate if they haven't already
PHASE_CORRECTED = False 
#store reference to phase_input number boxes
phase_inputs = [] 
#for highlighting selected mode hg lg section 
selected = None
#for scattering experiment global dictionary
burst_data_oam = {}
burst_data_hermite ={}
PHASE_STEP = 360/256

#----HELPER FUNCTIONS----
def update_phase(index:int, value:int):
    global PHASE_CORRECTED, PHASE_OFFSETS
    if value is None or value == '':
        return #ignore empty or None inputs
    try:
        PHASE_OFFSETS[index] = float(value) 
        PHASE_CORRECTED = True #set flag to true 

    except ValueError:
        pass #ignore invalid inputs

def update_phase_inputs():
    '''Referesh displayed UI numbers when phase_offsets changes.'''
    #only update changed fields 
    for i, (field, val) in enumerate(zip(phase_inputs, PHASE_OFFSETS)):
        if not np.isclose(field.value, val):
            field.value = val
def save_calibration(filename:str):
    '''
    Save the calibration as a json file to be used on later runs
    '''
    rounded_offsets = (np.round(PHASE_OFFSETS / PHASE_STEP)* PHASE_STEP).tolist()
    with open(f'{filename}.json', 'w') as f:
        json.dump(rounded_offsets, f)
    ui.notify(f'Calibration saved successfully into {filename}.json!')

def use_calibration_file(filename:str):
    '''
    apply the calibration data from a json file
    '''
    global PHASE_OFFSETS, PHASE_CORRECTED
    try:
        with open(f'{filename}.json', 'r') as f:
            loaded_offsets = json.load(f)
        PHASE_OFFSETS = np.round(np.array(loaded_offsets) / PHASE_STEP) * PHASE_STEP
        PHASE_CORRECTED = True
        update_phase_inputs() #refresh ui
        ui.notify(f'Calibration file: {filename}.json loaded and applied!')
    except FileNotFoundError:
        ui.notify(f"no calibration file: {filename}.json found")


def gen_Cal_from_S2P() -> None:
    """
    Computes PHASE_OFFSETS from a directory of S2P files.
    Use helper function from READ_S2P module
    Find the most negative phase and make that the reference
    """
    global PHASE_OFFSETS
    #numpy array of phases at FREQ for each port 
    phases = get_phase_at_freq()
    #ref phase is the longest port (most negative phase):
    ref_phase = np.min(phases)  
    #if its the ref phase the offset should be 0:
    #ref_phase - ref_phase = 0 
    #the other phases are less negative than ref phase
    #portx_phase - ref_phase = positive check  
    PHASE_OFFSETS = (phases - ref_phase)
    ui.notify("Phase offsets computed and applied")
    # update UI or display fields
    update_phase_inputs()



SELECTED_COM_PORT = 'SELECT MCU PORT' #global variable to store com selection
async def set_com_port(port:str):
    global SELECTED_COM_PORT,ser
    SELECTED_COM_PORT = port
    #debug
    #print(f'COM port set to {SELECTED_COM_PORT}')
    try:
        ser = serial.Serial(SELECTED_COM_PORT,BAUDRATE, bytesize=serial.EIGHTBITS,parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)
        ser.dtr = True
        ser.rts =True
        await asyncio.sleep(3)#allow arduino to reset
    except Exception as e:
        print(f'Failed to open serial port: {e}')

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
    total_phase = (phases + PHASE_OFFSETS)
    normalized_phase = total_phase % 360
    
    hardware_phases = np.uint8(np.round(normalized_phase* (256 / 360)))
    #send the phases
    ser.write(hardware_phases.tobytes()) 
    # ser.flush()
    #print(f'hardwarephases: {hardware_phases}')
    # #debug: echo
    # echo = ser.read(32)  # 16 words × 2 bytes each
    # control_words = np.frombuffer(echo, dtype=np.uint16)
    # print(f"Control words: {[f'0x{w:04x}' for w in control_words]}")
    # if echo != hardware_phases.tobytes():
    #     print('WARNING: PHASE missmatch detected')
    # else:
    #     print(f'echo{echo.hex(' ')}')


def hermite_mode(mode:str):
    '''
    Sends the appropriate phases to generate hermite gaussian beam 
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

def oam_mode(mode: str):
    '''
    sends appropriate phases to generate oam beam
    Args: 
        mode(str): e.g. '-1' or '2'
    '''
    phases = OAM_PHASES * int(mode)
    #send the appropriate phase
    try: 
        send_phases(phases)
    except Exception as e:
        ui.notify(f'Failed to send phases: {e}', color = 'red')
    else:
        ui.notify('Sucessfully sent phases')

def nav_back():
    '''
    navigate back and terminate transmission iff applicable
    ''' 
    global selected
    stop_tx() #this checks if tx is active before terminating 
    #for selected box on scattering experiment pages
    selected = None
    ui.navigate.back()

#----END HELPER FUNCTIONS----
   


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
    ('/calibrate', 'Calibration.png'),
    ('/manual', 'Manual_Phase_Control.png'), 
    ('/oam', 'OAM_Control1.png'),
    ('/hermite', 'Hermite_Control1.png'),
    ('/beam', 'Beam_Control.png')
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
            if target == images[0][0] and not PHASE_CORRECTED: 
                ui.image(f'media/{filename}')\
                    .classes(f'{classes_style} blink') \
                    .on('click', lambda t=target: navigate_if_ready(t))
            else:
                ui.image(f'media/{filename}')\
                    .classes(classes_style) \
                    .on('click', lambda t=target: navigate_if_ready(t))
    
    def navigate_if_ready(target):
        """Navigate only if a valid com is selected"""
        if SELECTED_COM_PORT == 'SELECT MCU PORT':
            ui.notify("Please Select MCU Port before proceeding.",color = 'red')
            return
        ui.navigate.to(target)

#---- END MAIN PAGE ----


# ---- SUBPAGES ----


# ---- Manual Phase Shift Page ----
@ui.page('/manual')
def manual_page():
    # Back button in the top-left
    ui.button('⬅ Back', on_click=ui.navigate.back)
    
    # Main content centered horizontally
    with ui.column().classes('w-full items-center  gap-6 mt-6'):
        # Header
        ui.label('Manually Control Phase of Each Element') \
            .classes('text-2xl font-bold text-center')

        with ui.column().classes('items-left gap-2 text-base text-gray-600'):
            ui.label('1. Enter the desired phase (0–360°) for each active element.')
            ui.label('2. Leave unused elements at 0°.')
            ui.label('3. Press "SUBMIT" to send the configuration to the controller.')
            ui.label('4. Energize the input port and measure farfield pattern in antenna chamber.')

            ui.label('Example Uses: multi fed antenna or phasing non default array')
        
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
        print('enter submit button')
        values = np.array([float(s.value) for s in sliders])
        
        #debug 
        print(f'values are {values}')
        #SEND values to arduino
        try: 
            send_phases(values)
        except Exception as e:
            ui.notify(f'Failed to send phases: {e}', color = 'red')
        else:
            ui.notify('Sucessfully sent phases', timeout=1)

#---- END Manual PAGE ----


#----OAM PAGE ----
@ui.page('/oam')
def oam_page():
    ui.button('⬅ Back', on_click=nav_back)

    with ui.column().classes('w-full items-center  gap-6 mt-6'):
        # Header
        ui.label('Generate Laguerre Guassian Beams') \
            .classes('text-2xl font-bold text-center')

        # Instructions
        ui.label('Attach provided 4x4 antenna array port 1 to top left ascending going down and to the right').classes('text-base text-gray-600 text-center')
        with ui.row().classes('w-full justify-center items-center'):
            ui.image('media/Default_Array.png').style('width: 35%;')
            ui.image('media/Default_Array2.png').style('width: 35%;')

    with ui.row().classes('w-full justify-center items-center'):
        ui.button('Measure Only', on_click=lambda: ui.navigate.to('/measure')).\
        classes('w-64 h-24 text-xl')
        ui.button('Scattering Experiment', on_click=lambda: ui.navigate.to('/scattering_experiment')).\
        classes('w-64 h-24 text-xl')

    images = [
    ('-3', 'oam--3.png'),
    ('-2', 'oam-2.png'), 
    ('-1', 'oam-1.png'),
    ('1', 'oam1.png'),
    ('2', 'oam2.png'),
    ('3', 'oam3.png'),
    ('0', 'plane_wave.png')
    ]

    image_elements = {} # store references to each image ui element
    def select_image(t):
        '''add red box around selected image and remove from old one'''
        global selected
        #remove from previously selected
        if selected is not None:
            image_elements[selected].classes(remove='ring-4 ring-red-500')
        #add red boarder to new image
        image_elements[t].classes('ring-4 ring-red-500')
        selected = t
        #call function to transmit that oam mode
        oam_mode(t)

    @ui.page('/measure')
    def measure():
        #header
        ui.label('Measure Laguerre Gaussian Beams') \
            .classes('text-2xl font-bold text-center')

        ui.button('⬅ Back', on_click=nav_back)
        with ui.column().classes('w-full items-center  gap-6 mt-6'):
            ui.label('Select your desired mode.').classes('text-base text-gray-600 text-center')
            ui.label('Phases are applied to ports appropriatly.').classes('text-base text-gray-600 text-center')
            ui.label('Energize the input port and measure.').classes('text-base text-gray-600 text-center')
        with ui.row().classes('w-full justify-center items-center gap-4'):
            for target, filename in images:
                img = ui.image(f'media/{filename}')\
                    .classes('w-1/5 cursor-pointer hover:scale-105 transition-transform duration-200') \
                    .on('click', lambda _, t=target: select_image(t))
                image_elements[target] = img #store reference

    @ui.page('/scattering_experiment')
    def scattering_experiment():
        ui.button('⬅ Back', on_click=nav_back)
        #header
        ui.label('Scattering Experiment Laguerre Gaussian Beams') \
            .classes('text-2xl font-bold text-center')
        ui.image('media/scat_instruct.png').style('width:30%')
        #Step 1: Choose Mode 
        ui.label("Step 1: Choose The Mode")\
            .classes('text-2xl font-bold text-center')

        with ui.row().classes('w-full justify-center items-center gap-4'):
            for target, filename in images:
                img = ui.image(f'media/{filename}')\
                    .classes('w-1/5 cursor-pointer hover:scale-105 transition-transform duration-200') \
                    .on('click', lambda _, t=target: select_image(t))
                image_elements[target] = img #store reference

        ui.label('Step 2: Probe for Main Beam Direction') \
            .classes('text-2xl font-bold text-center')
        with ui.row().classes('w-full justify-center items-center gap-4'):
            ui.image('media/probe_beam_dir.png').style('width:50%')
        ui.label('Rotate the transmit antenna until maximum average received power is achieved') 

        with ui.row().classes('w-full justify-center items-center'):
            y_min = ui.number(
                label ='Set Minimum Power for Graph',
                value=0,
                min=1
            ).style('width:30%') 
            y_max = ui.number(
                label ='Set Maximum Power for Graph',
                value=10,
                min=1
            ).style('width:30%')
        #live tx plot 
        fig = go.Figure(
            go.Scatter(x=[], y=[],mode = 'lines', name='Received Energy')
        )

        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis_title='Time(s)',
            yaxis_title='Avg Power Received (abr.)'
        )
        live_plot = ui.plotly(fig).classes('w-3/4 h-64')
        image_container = ui.row()\
            .classes('justify-center items-center')\
        .style('order:2; width:90%;')
        stop_event = asyncio.Event()
        
        def start_live_plot():
            # Start continuous TX
            tx()
            # Reset stop_event
            stop_event.clear()
            # Launch async update
            asyncio.create_task(live_update())
            stop_button.visible = True

        async def live_update():
            t_values = []
            energy_values = []
            start_time = time.time()

            while not stop_event.is_set():
                t = time.time()-start_time
                energy = get_energy()  # sample SDR
                t_values.append(t)
                energy_values.append(energy)
                t_values = t_values[-100:]
                energy_values = energy_values[-100:]
                # Update the figure's data
                fig.data[0].x = t_values
                fig.data[0].y = energy_values
                try:
                    fig.update_yaxes(range=[y_min.value,y_max.value])
                except Exception:
                    pass #temporary invalid values
                live_plot.update()  # NiceGUI triggers plot update

                await asyncio.sleep(0.05)  # ~20 Hz refresh
                
        def stop_live():
            #stop transmitting 
            stop_tx()
            stop_event.set()
            ui.notify("Live plot stopped", type='positive')

        # Buttons
        ui.button('Transmit & Live Plot', on_click=start_live_plot)
        stop_button = ui.button(
            'Stop',
            on_click=stop_live
        )
        stop_button.visible = False            
     
# ─── Step 3: Noise Floor ───────────────────────────────────────────────────
        _ts_data = {'copol': None, 'xpol': None, 'noise': None}

        ui.label('Step 3: Measure Noise Floor') \
            .classes('text-2xl font-bold text-center')
        ui.label(
            'With TX off, record the receiver noise floor. '
            'No transmission should occur during this step.'
        ).classes('text-base')

        noise_plot = ui.image('').style('width:50%; display:none')

        async def record_noise_floor():
            ui.notify('Recording noise floor (TX off) …', type='info')
            num_samples = 100
            for _ in range(10):
                discard_buffer()
            power_samples = [get_energy_fast() for _ in range(num_samples)]
            noise_mean = np.mean(power_samples)
            noise_std = np.std(power_samples)
            _ts_data['noise'] = {'mean': noise_mean, 'std': noise_std}

            fig, ax = plt.subplots(figsize=(5, 4))
            ax.errorbar(
                [0], [noise_mean],
                yerr=[[3 * noise_std], [3 * noise_std]],
                fmt='o',
                color='#888',
                ecolor='#888',
                elinewidth=2,
                capsize=12,
                capthick=2,
                markersize=10,
                label=f'mean = {noise_mean:.4g}\n±3σ = {3 * noise_std:.4g}'
            )
            ax.set_xlim(-0.5, 0.5)
            ax.set_xticks([])
            ax.set_ylabel('Received Power (arb.)')
            ax.set_title(f'Noise Floor — Mean Received Power\n(over n = {num_samples} sample buffers, TX off)')
            ax.legend(fontsize=9, loc='upper right')
            ax.grid(True, axis='y', alpha=0.3)
            fig.tight_layout()

            path = 'media/ts_noise.png'
            fig.savefig(path, dpi=120)
            plt.close(fig)

            noise_plot.set_source(path)
            noise_plot.force_reload()
            noise_plot.style('width:50%; display:block')
            ui.notify('Noise floor recorded!', type='positive')

        ui.button('Record Noise Floor', on_click=record_noise_floor)
        noise_plot
        


# ─── Step 3 / 4: avg+errorbar-series measurement ─────────────────────────────────────
        ui.label('Step 4: Record Backscattered Power ') \
            .classes('text-2xl font-bold text-center')
        with ui.row().classes('w-full justify-center items-center gap-4'):
            ui.image('media/scatterer_location.png').style('width:40%')
            ui.image('media/monostatic.png').style('width:40%')

        ts_plot_co    = ui.image('').style('width:80%; display:none')
        ts_plot_cross = ui.image('').style('width:80%; display:none')


        async def gen_average_received_power(channel_label: str, plot_widget, store_key: str):
            noise = _ts_data.get('noise')
            num_samples = 100
            if noise is None:
                ui.notify('Please record the noise floor first!' , type='warning')
                return

            ui.notify('Starting TX — warming up for 2s …', type='info')
            tx()
            await asyncio.sleep(2)

            for _ in range(10):
                discard_buffer()

            ui.notify('Recording …', type='positive')
            power_samples = [get_energy_fast() for _ in range(num_samples)]
            raw_mean = np.mean(power_samples)
            raw_std = np.std(power_samples)
            stop_tx()

            # Power above noise floor; uncertainties add in quadrature
            average_power      = raw_mean - noise['mean']
            # uncertainty adds in quadrature
            standard_deviation = np.sqrt(raw_std**2 + noise['std']**2)


            _ts_data[store_key] = {'mean': average_power, 'std': standard_deviation}

            fig, ax = plt.subplots(figsize=(5, 4))
            ax.errorbar(
                [0], [average_power],
                yerr=[[3 * standard_deviation], [3 * standard_deviation]],
                fmt='o',
                color='steelblue',
                ecolor='steelblue',
                elinewidth=2,
                capsize=12,
                capthick=2,
                markersize=10,
                label=f'mean = {average_power:.4g}\n±3σ = {3 * standard_deviation:.4g}'
            )

            # Shade the noise floor ±3σ band for reference
            ax.axhspan(
                -3 * noise['std'], 3 * noise['std'],
                color='#888', alpha=0.12, label=f'noise ±3σ'
            )
            ax.axhline(0, color='#888', linewidth=0.8, linestyle='--')

            ax.set_xlim(-0.5, 0.5)
            ax.set_xticks([])
            ax.set_ylabel('Power above noise floor (arb.)')
            ax.set_title(f'{channel_label} — Average Backscattered Power\n(over n = {num_samples} sample buffers, noise-subtracted)')
            ax.legend(fontsize=9, loc='upper right')
            ax.grid(True, axis='y', alpha=0.3)
            fig.tight_layout()

            path = f'media/ts_{store_key}.png'
            fig.savefig(path, dpi=120)
            plt.close(fig)

            plot_widget.set_source(path)
            plot_widget.force_reload()
            plot_widget.style('width:50%; display:block')
            ui.notify(f'{channel_label} recording complete!', type='positive')

        ui.label('Press to record co-polarized (receive array aligned with transmit):') \
            .classes('text-lg')
        async def record_copol():
            await gen_average_received_power('Co-polarized', ts_plot_co, 'copol')
        ui.button('Record Co-pol Scattering', on_click=record_copol)
        ts_plot_co

        ui.label('Step 5: Rotate Receive Array and Record Cross-polarized Power') \
            .classes('text-2xl font-bold text-center')
        with ui.row().classes('w-full justify-center items-center gap-4'):
            ui.image('media/cross_pol_meas.png').style('width:50%')

        ui.label('Press to record cross-polarized (receive array rotated 90°):') \
            .classes('text-lg')
        async def record_xpol():
            await gen_average_received_power('Cross-polarized', ts_plot_cross, 'xpol')
        ui.button('Record Cross-pol Scattering', on_click=record_xpol)
        ts_plot_cross

# ─── Step 6: Polarization vector ─────────────────────────────────────────────

        ui.label('Step 6: View Mean Polarization State') \
            .classes('text-2xl font-bold text-center')
        ui.label(
            'After both measurements are recorded, generate the polarization diagram. '
            'The circle shows the mean polarization state: co-pole on Y, '
            'cross-pole on X, and the resultant vector with 3σ uncertainty cone.'
        )

        pol_image = ui.image('').style('width:60%; display:none')

        def gen_polarization_diagram():
            num_samples = 100
            copol = _ts_data.get('copol')
            xpol  = _ts_data.get('xpol')

            if copol is None or xpol is None:
                ui.notify('Please record BOTH co-pol and cross-pol measurements first.', type='warning')
                return

            cx_mean, cx_std = xpol['mean'],  xpol['std']   # cross-pole → X
            cy_mean, cy_std = copol['mean'], copol['std']  # co-pole    → Y

            # Normalise to unit circle
            max_val = max(cx_mean, cy_mean) or 1.0
            cx_n, cx_sn = cx_mean / max_val, cx_std / max_val
            cy_n, cy_sn = cy_mean / max_val, cy_std / max_val

            angle_mean = np.degrees(np.arctan2(cy_n, cx_n))
            angle_lo   = np.degrees(np.arctan2(cy_n - 3*cy_sn, cx_n + 3*cx_sn))
            angle_hi   = np.degrees(np.arctan2(cy_n + 3*cy_sn, cx_n - 3*cx_sn))

            fig, ax = plt.subplots(figsize=(5, 5))
            ax.set_aspect('equal')
            ax.set_xlim(-1.35, 1.35)
            ax.set_ylim(-1.35, 1.35)
            ax.set_facecolor('#e3e3e1')
            fig.patch.set_facecolor('#e3e3e3')

            # Unit circle
            theta = np.linspace(0, 2 * np.pi, 300)
            ax.plot(np.cos(theta), np.sin(theta), color='#444', linewidth=0.8)
            ax.axhline(0, color='#000', linewidth=0.5)
            ax.axvline(0, color='#000', linewidth=0.5)

            ax.text( 1.28, 0.04, 'cross-pole', color='#000', fontsize=7, ha='right')
            ax.text( 0.04, 1.28, 'co-pole',    color='#000', fontsize=7, ha='left')

            # 1σ uncertainty cone (shaded wedge between lo/hi angles)
            wedge_angles = np.linspace(np.radians(angle_lo), np.radians(angle_hi), 60)
            wedge_x = np.concatenate([[0], np.cos(wedge_angles)])
            wedge_y = np.concatenate([[0], np.sin(wedge_angles)])
            ax.fill(wedge_x, wedge_y, color='#D85A30', alpha=0.18, label='3σ uncertainty')
            arc = plt.matplotlib.patches.Arc(
                (0, 0), 0.45, 0.45, angle=0,
                theta1=min(angle_lo, angle_hi), theta2=max(angle_lo, angle_hi),
                color='#D85A30', linewidth=1.5
            )
            ax.add_patch(arc)

            # Component vectors
            ax.annotate('', xy=(cx_n, 0), xytext=(0, 0),
                        arrowprops=dict(arrowstyle='->', color='#378ADD', lw=2.5))
            ax.annotate('', xy=(0, cy_n), xytext=(0, 0),
                        arrowprops=dict(arrowstyle='->', color='#1D9E75', lw=2.5))

            # Component error bars
            ax.errorbar([cx_n], [0],  xerr=3*cx_sn, fmt='none', ecolor='#378ADD', elinewidth=1.5, capsize=6)
            ax.errorbar([0], [cy_n],  yerr=3*cy_sn, fmt='none', ecolor='#1D9E75', elinewidth=1.5, capsize=6)

            # Resultant vector
            ax.annotate('', xy=(cx_n, cy_n), xytext=(0, 0),
                        arrowprops=dict(arrowstyle='->', color='#EF9F27', lw=2.2, linestyle='dashed'))

            ax.text(0, -1.28,
                    f'θ = {angle_mean:.1f}°  |  n = {num_samples} sample buffers',
                    color='#000', fontsize=8, ha='center', va='top', fontweight='bold')

            legend_elements = [
                plt.matplotlib.lines.Line2D([0], [0], color='#378ADD', lw=2, label='Cross-pole'),
                plt.matplotlib.lines.Line2D([0], [0], color='#1D9E75', lw=2, label='Co-pole'),
                plt.matplotlib.lines.Line2D([0], [0], color='#EF9F27', lw=2,
                                            linestyle='--', label='Resultant'),
                plt.matplotlib.patches.Patch(color='#D85A30', alpha=0.35, label='±3σ cone'),
            ]
            ax.legend(handles=legend_elements, fontsize=7, loc='lower right')
            ax.set_title('Mean Scattered Polarization State', fontweight='bold')

            fig.tight_layout()
            path = 'media/polarization_diagram.png'
            fig.savefig(path, dpi=150)
            plt.close(fig)

            pol_image.set_source(path)
            pol_image.force_reload()
            pol_image.style('width:60%; display:block')
            ui.notify('Polarization diagram ready!', type='positive')

        ui.button('Generate Polarization Diagram', on_click=gen_polarization_diagram)
        pol_image
#----END OAM MODE ----




#----HERMITE PAGE-----
@ui.page('/hermite')
def hermite_page():

    ui.button('⬅ Back', on_click=nav_back)
    with ui.column().classes('w-full items-center  gap-6 mt-6'):
        # Header
        ui.label('Generate Hermite Beams') \
            .classes('text-2xl font-bold text-center')

        # Instructions
        ui.label('Attach provided 4x4 antenna array port 1 to top left ascending going down and to the right').classes('text-base text-gray-600 text-center')
        with ui.row().classes('w-full justify-center items-center'):
            ui.image('media/Default_Array.png').style('width: 35%;')
            ui.image('media/Default_Array2.png').style('width: 35%;')

    with ui.row().classes('w-full justify-center items-center'):
        ui.button('Measure Only', on_click=lambda: ui.navigate.to('/measure')).\
        classes('w-64 h-24 text-xl')
        ui.button('Scattering Experiment', on_click=lambda: ui.navigate.to('/scattering_experiment')).\
        classes('w-64 h-24 text-xl')
      

    images = [
    ('01', '01.png'), 
    ('10', '10.png'),
    ('11', '11.png'),
    ]
    image_elements = {} # store references to each image ui element
    def select_image(t):
        '''add red box around selected image and remove from old one'''
        global selected
        #remove from previously selected
        if selected is not None:
            image_elements[selected].classes(remove='ring-4 ring-red-500')
        #add red boarder to new image
        image_elements[t].classes('ring-4 ring-red-500')
        selected = t
        #call function to transmit that hermite mode
        hermite_mode(t)

    @ui.page('/measure')
    def measure():
        #header
        ui.label('Measure Hermite Gaussian Beams') \
            .classes('text-2xl font-bold text-center')

        ui.button('⬅ Back', on_click=nav_back)
        with ui.column().classes('w-full items-center  gap-6 mt-6'):
            ui.label('Select your desired mode.').classes('text-base text-gray-600 text-center')
            ui.label('Phases are applied to ports appropriatly.').classes('text-base text-gray-600 text-center')
            ui.label('Energize the input port and measure.').classes('text-base text-gray-600 text-center')
        with ui.row().classes('w-full justify-center items-center gap-4'):
            for target, filename in images:
                img = ui.image(f'media/{filename}')\
                    .classes('w-1/5 cursor-pointer hover:scale-105 transition-transform duration-200') \
                    .on('click', lambda _, t=target: select_image(t))
                image_elements[target] = img #store reference

    @ui.page('/scattering_experiment')
    def scattering_experiment():
        ui.button('⬅ Back', on_click=nav_back)
        #header
        ui.label('Scattering Experiment Hermite Gaussian Beams') \
            .classes('text-2xl font-bold text-center')
        ui.image('media/scat_instruct.png').style('width:30%')
        #Step 1: Choose Mode 
        ui.label("Step 1: Choose The Mode")
        with ui.row().classes('w-full justify-center items-center gap-4'):
            for target, filename in images:
                img = ui.image(f'media/{filename}')\
                    .classes('w-1/5 cursor-pointer hover:scale-105 transition-transform duration-200') \
                    .on('click', lambda _, t=target: select_image(t))
                image_elements[target] = img #store reference
        #Step 2: Find Beam Direction
        ui.label('Step 2: Confirm Main Beam Direction')
        ui.image('media/Step1.jpeg').style('width:30%')  

        with ui.row().classes('w-full justify-center items-center'):
            y_min = ui.number(
                label ='Set Minimum Power for Graph',
                value=0,
                min=1
            ).style('width:30%') 
            y_max = ui.number(
                label ='Set Maximum Power for Graph',
                value=10,
                min=1
            ).style('width:30%')

        #live tx plot 
        fig = go.Figure(
            go.Scatter(x=[], y=[],mode = 'lines', name='Received Energy')
        )

        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis_title='Time(s)',
            yaxis_title='Avg Power Received'
        )
        live_plot = ui.plotly(fig).classes('w-3/4 h-64')
        image_container = ui.row()\
            .classes('justify-center items-center')\
        .style('order:2; width:90%;')
        stop_event = asyncio.Event()
        
        
        def start_live_plot():
            # Start continuous TX
            tx()
            # Reset stop_event
            stop_event.clear()

            # Launch async update
            asyncio.create_task(live_update())
            stop_button.visible = True

        async def live_update():
            t_values = []
            energy_values = []
            start_time = time.time()

            while not stop_event.is_set():
                t = time.time()-start_time
                energy = get_energy()  # sample SDR
                t_values.append(t)
                energy_values.append(energy)
                t_values = t_values[-100:]
                energy_values = energy_values[-100:]
                # Update the figure's data
                fig.data[0].x = t_values
                fig.data[0].y = energy_values
                try:
                    fig.update_yaxes(range=[y_min.value,y_max.value])
                except Exception:
                    pass #temporary invalid values
                live_plot.update()  # NiceGUI triggers plot update

                await asyncio.sleep(0.05)  # ~20 Hz refresh
                

        def stop_live():
            #stop transmitting 
            stop_tx()
            stop_event.set()
            ui.notify("Live plot stopped", type='positive')

        # Buttons
        ui.button('Transmit & Live Plot', on_click=start_live_plot)
        stop_button = ui.button(
            'Stop',
            on_click=stop_live
        )
        stop_button.visible = False            


        def record_burst(trial_name, duration=1.0, sample_interval=0.01):
            '''
            transmit a burst of continuous wave and record recieved "power"
            '''
            global burst_data_hermite
            #start trasmission
            tx()
            time.sleep(SETTLE_TIME)

            energy_values = []

            num_samples = int(duration/sample_interval)
            for _ in range(num_samples):
                energy = get_energy()
                energy_values.append(energy)
                time.sleep(sample_interval)
            #end transmission
            stop_tx()
            #store the data
            burst_data_hermite[trial_name] ={
                'energy': np.array(energy_values)
            }
            ui.notify("successfully recorded burst")
    
        #Set up containers for images to be placed in later
        baseline_container=ui.row()\
            .classes('justify-center items-center')\
            .style('order:4; width:90%;')
        scatterer_container=ui.row()\
            .classes('justify-center items-center')\
            .style('order:8; width:90%;')
        difference_container=ui.row()\
            .classes('justify-center items-center')\
            .style('order:11; width:90%;')
        scatterer_container_plane=ui.row()\
            .classes('justify-center items-center')\
            .style('order:19; width:90%;')
        difference_container_plane=ui.row()\
            .classes('justify-center items-center')\
            .style('order:22; width:90%;')

        comparison_container=ui.row()\
            .classes('justify-center items-center')\
            .style('order:25; width: 90%')
        
        def plot_no_scatterer():
            '''
            Record burst data then plot it
            '''
            global burst_data_hermite
            record_burst('baseline')
            e_b = burst_data_hermite['baseline']['energy']
            #number of samples
            x = np.arange(len(e_b))

            plt.figure(figsize=(8,5))
            plt.plot(x[1:], e_b[1:], '-o', label='Average Power Recieved')
            plt.xlabel("Samples")
            plt.ylabel("Average Power Received")
            plt.title('Energy Burst Measurement - Baseline')
            plt.grid(True)
            plt.savefig('media/baseline.png')
            plt.close()
            #update ui image
            baseline_container.clear()
            with baseline_container:
                ui.image('media/baseline.png').style('width:60%;').force_reload()

        def plot_scatterer(plane=False):
            '''
            Record burst data then plot it 
            '''
            global burst_data_hermite
            if not plane:
                record_burst('scatterer')
                e_s = burst_data_hermite['scatterer']['energy']
            else:
                record_burst('scatterer_plane')
                e_s = burst_data_hermite['scatterer_plane']['energy']
            #number of samples
            x = np.arange(len(e_s))
            plt.figure(figsize=(8,5))
            plt.plot(x[1:], e_s[1:], '-o', label='Average Power Recieved')
            plt.xlabel("Samples") 
            plt.ylabel("Average Power Received") 
            plt.title('Energy Burst Measurement - Scatterer') 
            plt.grid(True)
            if not plane:
                plt.savefig('media/scatterer_burst.png')
            else:
                plt.savefig('media/scatterer_burst_plane.png')
            plt.close()
            #update ui image
            if not plane:
                scatterer_container.clear()
                with scatterer_container:
                    ui.image('media/scatterer_burst.png').style('width:60%;').force_reload()
            else:
                scatterer_container_plane.clear()
                with scatterer_container_plane:
                    ui.image('media/scatterer_burst_plane.png').style('width:60%').force_reload()

        def plot_difference(plane =False):
            '''
            Plot scattered - baseline
            '''
            if not plane:
                e_diff = burst_data_hermite['scatterer']['energy'] - burst_data_hermite['baseline']['energy'] 
            else:
                e_diff = burst_data_hermite['scatterer_plane']['energy'] - burst_data_hermite['baseline']['energy'] 
            x = np.arange(len(e_diff))
            plt.figure(figsize=(8,5))
            plt.plot(x[1:], e_diff[1:], '-o', label='Average Power Recieved')
            plt.xlabel("Samples")
            plt.ylabel("Average Power Received")
            plt.title('Energy Burst Measurement - Difference')
            plt.grid(True)
            if not plane:
                plt.savefig('media/power_diff.png')
            else:
                plt.savefig('media/power_diff_plane.png')
            plt.close()
            #update ui image
            if not plane:
                difference_container.clear()
                with difference_container:
                    ui.image('media/power_diff.png').style('width:60%;').force_reload()
            else:
                difference_container_plane.clear()
                with difference_container_plane:
                    ui.image('media/power_diff_plane.png').style('width:60%;').force_reload()

        def plot_comparison():
            e_diff_structured = burst_data_hermite['scatterer']['energy'] - burst_data_hermite['baseline']['energy']
            e_diff_plane = burst_data_hermite['scatterer_plane']['energy'] - burst_data_hermite['baseline']['energy']
            x = np.arange(len(e_diff_structured))
# Plot comparison
            plt.figure(figsize=(8,5))
            plt.plot(x[1:], e_diff_structured[1:], '-o', label='Scatterering from Structured Wave')
            plt.plot(x[1:], e_diff_plane[1:], '-o', label='Scatterer Plane from Plane Wave')

            plt.xlabel("Samples")
            plt.ylabel("Average Power Difference")
            plt.title("Energy Burst Measurement - Experiment Comparison")
            plt.grid(True)
            plt.legend(loc="best")

            # Save to file
            plt.savefig('media/power_diff_comparison.png')
            plt.close()

            # Update UI
            comparison_container.clear()
            with comparison_container:
                ui.image('media/power_diff_comparison.png').style('width:60%;').force_reload()



        def send_phases_for_planewave(theta, phi):

            phases = runAF_Calc(DX,DY,theta, phi)
            try: 
                send_phases(phases)
            except Exception as e:
                ui.notify(f'Failed to send phases: {e}', color = 'red')
            else:
                ui.notify('Sucessfully sent phases')

# Step 3: measure baseline
        ui.label("Step 3: Measure Baseline").style('order: 1;')
        ui.image('media/Step2.jpeg').style('order: 2; width: 30%;')
        ui.button("Start", on_click=plot_no_scatterer).style('order: 3;')
        # baseline_container has order: 4

        # Step 4: measure scattering
        ui.label("Step 4: Measure Scattering").style('order: 5;')
        ui.image('media/Step3.jpeg').style('order: 6; width: 30%;')
        ui.button("Start", on_click=plot_scatterer).style('order: 7;')
        # scatterer_container has order: 8

        # Step 5: show difference
        ui.label("Step 5: Show Difference").style('order: 9;')
        ui.button("Show Difference", on_click=plot_difference).style('order: 10;')
        # difference_container has order: 11
        # Step 6: User estimate the angle to the scatterer given the coordinate system: 
        ui.label("Step 6: Approximate Scatterer Location to Illuminate with Standard Plane Wave").style('order:12')
        ui.label("Use the following coordinate system to define your angles").style('order:13')
        with ui.row().classes('w-full justify-left items-center').style('order: 14'):
            ui.image('media/Default_Array.png').style('width: 35%;')
            ui.image('media/Default_Array2.png').style('width: 35%;')

        with ui.row().classes('w-full justify-center items-center').style('order: 15;'):
            theta = ui.number(
                label = 'Theta (deg)',
                value=0,
                min = 0, max=90
            ).style('width:20%')

            phi = ui.number(
                label = 'Phi (deg)',
                value=0,
                min = 0, max = 360
            ).style('width:20%')
             
            ui.button("Send Phases", on_click=lambda: send_phases_for_planewave(theta.value,phi.value))
    
        #Step 7 Measure Scattering
        ui.label("Step 7: Measure Scattering from Plane Wave").style('order: 16;')
        ui.image('media/Step3.jpeg').style('order: 17; width: 30%;')
        ui.button("Start", on_click=lambda:plot_scatterer(plane=True)).style('order: 18;')

        #Step 8 Perform Subtraction
        ui.label("Step 8: Show Difference (Planewave - Basline Scattering)").style('order: 20;')
        ui.button("Show Difference", on_click=lambda:plot_difference(plane=True)).style('order: 21;')

        #Step 9 Compre the plane wave illuminaiton and structured illumination scattering 
        ui.label("Step 9: Compare the scattering under different illuminations").style('order: 23;')
        ui.button('Compare', on_click=lambda:plot_comparison()).style('order: 24;')
        


#----Beam Steering----
@ui.page('/beam')
def beam_page():
    ui.button('⬅ Back', on_click=nav_back)
    with ui.row().classes('w-full justify-center items-center'):
        ui.button('Receive Mode', on_click=lambda: ui.navigate.to('/receive_mode')).\
        classes('w-64 h-24 text-xl')
        ui.button('Transmit Mode', on_click=lambda: ui.navigate.to('/transmit_mode')).\
        classes('w-64 h-24 text-xl')

    with ui.row().classes('w-full justify-center items-center'):
        ui.image('media/Beam_Explanation.png')
    
    #----Sub Pages----    

    #----Transmit Mode ----
    @ui.page('/transmit_mode')
    def transmit_mode():
        # Back button in the top-left
        ui.button('⬅ Back', on_click=nav_back)
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
                dx = ui.number(
                    label = 'dx (λ)',
                    value=DX,
                    min=0.1
                ).style('width:20%')

                dy = ui.number(
                    label = 'dy (λ)',
                    value=DY,
                    min=0.1
                ).style('width:20%')

                theta = ui.number(
                    label = 'Theta (deg)',
                    value=0,
                    min = 0, max=90
                ).style('width:20%')

                phi = ui.number(
                    label = 'Phi (deg)',
                    value=0,
                    min = 0, max = 360
                ).style('width:20%')
                 
            with ui.row().classes('w-full justify-center items-center'):
                y_min = ui.number(
                    label ='Set Minimum Power for Graph',
                    value=0,
                    min=1
                ).style('width:30%') 
                y_max = ui.number(
                    label ='Set Maximum Power for Graph',
                    value=10,
                    min=1
                ).style('width:30%')

            fig = go.Figure(
                go.Scatter(x=[], y=[],mode = 'lines', name='Received Energy')
            )

            fig.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                xaxis_title='Time(s)',
                yaxis_title='Avg Power Received'
            )
            live_plot = ui.plotly(fig).classes('w-3/4 h-64')
            image_container = ui.row()\
                .classes('justify-center items-center')\
            .style('order:2; width:90%;')
            stop_event = asyncio.Event()
            
            
            def start_live_plot():
                # Send initial phases
                phases = runAF_Calc(dx.value, dy.value, theta.value, phi.value)
                send_phases(phases)

                # Show AF image
                image_container.clear()
                with image_container:

                    ui.image('media/AF.png').style('width:40%;').force_reload()
                    ui.image('media/uv.png').style('width:40%;').force_reload()
                # Start continuous TX
                tx()

                # Reset stop_event
                stop_event.clear()

                # Launch async update
                asyncio.create_task(live_update())
                new_angle_button.visible = True
                stop_button.visible = True

            async def live_update():
                t_values = []
                energy_values = []
                start_time = time.time()
                last_theta = theta.value 
                last_phi = phi.value

                while not stop_event.is_set():
                    t = time.time()-start_time
                    energy = get_energy()  # sample SDR
                    t_values.append(t)
                    energy_values.append(energy)
                    t_values = t_values[-100:]
                    energy_values = energy_values[-100:]
                    # Update the figure's data
                    fig.data[0].x = t_values
                    fig.data[0].y = energy_values
                    try:
                        fig.update_yaxes(range=[int(y_min.value),int(y_max.value)])
                    except Exception:
                        pass #temporary invalid values
                    live_plot.update()  # NiceGUI triggers plot update

                    await asyncio.sleep(0.05)  # ~20 Hz refresh
            def send_current_phase():
                phases = runAF_Calc(
                    dx.value, 
                    dy.value, 
                    theta.value,
                    phi.value
                )
                send_phases(phases)
                # Show AF image
                image_container.clear()
                with image_container:
                    ui.image('media/AF.png')\
                    .style('width:40%;')\
                    .force_reload()
                    ui.image('media/uv.png')\
                    .style('width:40%;')\
                    .force_reload()

            def stop_live():
                #stop transmitting 
                stop_tx()
                stop_event.set()
                ui.notify("Live plot stopped", type='positive')

            # Buttons
            ui.button('Transmit & Live Plot', on_click=start_live_plot)
            new_angle_button = ui.button(
                'New Angle', 
                on_click = send_current_phase
            ) 
            new_angle_button.visible = False

            stop_button = ui.button(
                'Stop',
                on_click=stop_live
            )
            stop_button.visible = False            
    #----END transmit page----

    #----Receive Mode page----

    @ui.page('/receive_mode')
    def receive_mode():        
        # Back button in the top-left
        ui.button('⬅ Back', on_click=nav_back)
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
            with ui.row().classes('w-full justify-center items-center'): 
                ui.label('The coefficients are precomputed for the default array')\
                .classes('text-base text-gray-600 text-center')
        image_container = ui.row()\
            .classes('w-full justify-center items-center')\
            .style('order:2;')
            

        def Scan_Beam():
            """Launches beam scan in background with progress bar"""
            with ui.dialog() as dialog, ui.card():
                label = ui.label('Starting beam scan...')
                progress_bar = ui.linear_progress(show_value = False)\
                    .props('indeterminate')
                dialog.open()


            async def scan_task():
                # Launch the scan as an async background task
                tx()
                # clear receive buffer 
                n_steps = len(DEFAULT_RX_GRID)
                energies = np.zeros(n_steps)

                for i, phases in enumerate(DEFAULT_RX_GRID):
                    send_phases(phases)
                    if i == 0:
                        for _ in range(10):
                            discard_buffer()
                    energies[i] = get_energy() #time to sample ~410us
                    await asyncio.sleep(10e-6)
                    label.set_text(f"Scanning {i+1}/{n_steps}")

                stop_tx()

                # Reshape and plot
                energies_2D = energies.reshape(len(THETA_RANGE), len(PHI_RANGE))
                energies_2D /= np.max(energies_2D) #normalize
                # Find peak location
                peak_idx = np.unravel_index(np.argmax(energies_2D), energies_2D.shape)
                theta_peak = THETA_RANGE[peak_idx[0]]
                phi_peak = PHI_RANGE[peak_idx[1]]

                fig, ax = plt.subplots(figsize=(8, 6))

                im = ax.imshow(
                    energies_2D,
                    extent=[PHI_RANGE[0], PHI_RANGE[-1], THETA_RANGE[0], THETA_RANGE[-1]],
                    origin='lower',
                    aspect='auto',
                    cmap='plasma'
                )

                #mark the point                
                ax.plot(phi_peak, theta_peak, 'ro', markersize=10)  # Mark peak
                # Annotate with coordinates
                ax.annotate(
                    fr"$\phi$: {phi_peak:.1f}°,$\theta$: {theta_peak:.1f}°",
                    xy=(phi_peak, theta_peak),                 # point to annotate
                    xytext=(0, 10),                           # offset in pixels
                    ha='center',
                    va='center',
                    textcoords='offset points',
                    color='white',
                    fontsize=10,
                    bbox=dict(boxstyle="round,pad=0.2", fc="black", alpha=0.5),
                    zorder=100
                )
                plt.colorbar(im, ax=ax, label='Received energy')

                ax.set_xlabel('Phi [deg]')
                ax.set_ylabel('Theta [deg]')
                ax.set_title('Beam Scan')
                plt.savefig('media/rx_heat.png', dpi=300)
                plt.close()
                # Update UI with plot
                image_container.clear()
                with image_container:
                    ui.image('media/rx_heat.png').style('width:65%;').force_reload()

                # Hide progress bar after completion
                dialog.close()

            asyncio.create_task(scan_task()) 

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
        send_phases(np.zeros(16,dtype=int))
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
            ui.label('Please Load Defualt Calibration File by clicking load calibration and typing Default').classes('text-base text-gray-600 text-center')
            ui.label('If recalibration is needed please manually enter phases and save or redo s2p measurements for each port and create the new calibration').classes('text-base text-gray-600 text-center')
            
            ui.label('Note that when you load the calibration it will be rounded to the accuracy of the phase shifter 1.40625 degrees/LSB').classes('text-base text-gray-600 text-center')
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
        ui.button('Generate Calibration from S2P Folder', on_click=gen_Cal_from_S2P)
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
