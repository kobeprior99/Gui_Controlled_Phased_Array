'''
Global variables shared across files
'''
import numpy as np

ser = None
PHASE_OFFSETS = np.zeros(16, dtype=float)
PHASE_CORRECTED = False
phase_inputs = []  # references to UI input elements
selected = None
burst_data_oam = {}
burst_data_hermite = {}
SELECTED_COM_PORT = 'SELECT MCU PORT'
PHASE_STEP = 360 / 256
