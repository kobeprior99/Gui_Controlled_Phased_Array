"""
Filename: config.py
Author: Kobe Prior
Date Last Modified: November 20 2026 
Description: Holds important constants that are used across the program
"""

import numpy as np

BAUDRATE = 115200 

#PHYSICAL CONSTANTS
C = 299792458 #m/s 
FREQ = int(2.1e9)
LAMBDA = C/FREQ

#LINEAR POLARIZED ARRAY PARAMETERS
NUM_ELEMENTS = 16
NSIDE = 4
#element spacing in meters
dx_m = 57.5e-3
dy_m = 50.0e-3

#dx dy in wavelengths is:
DX = dx_m/LAMBDA 
DY = dy_m/LAMBDA

#CP ARRAY PARAMETERS
CP_PHASES = np.array([
        270.0, 0.0, 270.0, 90.0,
        180.0, 90.0, 180.0, 0.0,
        270.0, 0.0, 270.0, 90.0,
        180.0, 90.0, 180.0, 0.0
    ]) 
dx_m_cp = 59.592e-3
dy_m_cp = 59.592e-3
##dx dy in wavelengths is:
DX_CP = dx_m_cp/LAMBDA 
DY_CP = dy_m_cp/LAMBDA

#BEAM SCANNING PARAMETERS
HPBW_DEG = 30        # full -3 dB width measured
SCAN_MAX_DEG = 45

hpbw_u = 2 * np.sin(np.deg2rad(HPBW_DEG / 2))   # beam width in uv, ~0.52
UV_STEP = hpbw_u / 2                            # ~0.26, crossover loss ~1 dB

r_max = np.sin(np.deg2rad(SCAN_MAX_DEG))
n = int(np.ceil(r_max / UV_STEP))
g = np.arange(-n, n + 1) * UV_STEP
U, V = np.meshgrid(g, g)
mask = U**2 + V**2 <= r_max**2 + 1e-9
u_pts, v_pts = U[mask], V[mask]

THETA_LIST = np.degrees(np.arcsin(np.hypot(u_pts, v_pts)))
PHI_LIST   = np.degrees(np.arctan2(v_pts, u_pts)) % 360


#PLUTO config
BASE_BAND = 100e3
SAMP_RATE = int(5e6)  # Hz e.g. 5 MHz
TX_GAIN = -7 # -7 is -7dBm measured with spectrum analyzer and about 10 dBm with the inline amplifier.
RX_GAIN = 20  

#used for dBFS reading
FULL_SCALE = 2**11
BUFFER_SIZE = 4*2048 

# Tone-detection reference: windowed single-bin DFT at BASE_BAND
_n = np.arange(BUFFER_SIZE)
_w = np.hanning(BUFFER_SIZE)
TONE_WREF = _w * np.exp(-2j * np.pi * BASE_BAND / SAMP_RATE * _n)
TONE_WSUM = float(np.sum(_w))
del _n, _w
SETTLE_TIME = 1 #time to transmit before capturing burst


#calibration directory
S2PDIR = 'S2P-SEP9-2026'

#Scattering test
SETTLE_TIME_S = 3
N_DISCARD_BUFFERS = 100
N_AVG_BUFFERS = 30

