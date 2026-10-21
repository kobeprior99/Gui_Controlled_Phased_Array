import numpy as np
#contains constants used throughout the program
BAUDRATE = 115200 
C = 299792458 #m/s 
FREQ = int(2.1e9)
LAMBDA = C/FREQ
NUM_ELEMENTS = 16
NSIDE = 4

#RX grid 
#spacing in meters
dx_m = 48.3e-3
dy_m = 56.4e-3

##dx dy in wavelengths is:
DX = dx_m/LAMBDA 
DY = dy_m/LAMBDA

#We're limited to the resolution of our array, the half power beam width is rather large
num_theta = 8
num_phi = 32
#8 values
THETA_RANGE = np.linspace(0,45, num_theta)
#32 values
PHI_RANGE = np.linspace(0, 360, num_phi, endpoint=False)
#Total of 256 locations to scan through

#PLUTO config
BASE_BAND = 100e3
SAMP_RATE = 5e6  # Hz e.g. 5 MHz
TX_GAIN = -7 # -7 is -7dBm measured with spectrum analyzer and about 10 dBm with the inline amplifier.RX_GAIN = 5 # adjust as needed 0-74 be careful you don't wanna blow out frent end
RX_GAIN = 20 # 
#2 ms to fill buffer
BUFFER_SIZE = 4*2048 
NUM_AVG = 1
SETTLE_TIME = 1 #time to transmit before capturing burst

OAM_PHASES = np.array([
        130.58, 105.93, 74.07, 49.42,
        158.73, 130.58, 49.42, 21.27,
        -158.73, -130.58, -49.42, -21.27,
        -130.58, -105.93, -74.07, -49.42,
    ]) 

#calibration directory
S2PDIR = 'S2P-SEP9-2026'


#Scattering test
SETTLE_TIME_S = 3
N_DISCARD_BUFFERS = 100
N_AVG_BUFFERS = 30
