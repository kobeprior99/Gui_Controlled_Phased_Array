'''
Purpose: Global variables shared cross graphical user interface to keep track of 
phase correction com port selection and lookuptable status
'''
import numpy as np

ser = None
PHASE_OFFSETS = np.zeros(16, dtype=float)
PHASE_CORRECTED = False
phase_inputs = []  # references to UI input elements
selected = None
SELECTED_COM_PORT = 'SELECT MCU PORT'
PHASE_STEP = 360 / 256
CP_ARRAY = False  # False: linear Tx array, True: circularly polarized array
LUT_BYTES = None #bytes of the table last confirmed by the MCU or None
