'''
File: AF_Calc.py 
Author: Kobe Prior
Date: 2025-09-21
Description:
    Brief description of what this script/module does.
    Include any important details or functionality.
    
Usage:
    Example of how to run or use the script/module, if applicable.

Dependencies:
'''

#add libraries

import numpy as np
import matplotlib.pyplot as plt

#config file contains some useful constants that we'll make use of 
from config import *

def find_phase_shift(theta_0, phi_0, dx, dy):
    '''
    Calculate the phase shifts required to steer in certain direction
    
    Notes
    -----
    This program uses the config file which gives parameters for default array

    Parameters
    ----------
    theta_0: float 
        elevation steer direction in degrees
    phi_0: float
        azimuthal steer direction in degrees
    dx: float
        horizontal spacing between elements (fraction of wavelength)
    dx: float
        vertical spacing between elements (fraction of wavelength)
    Returns
    -------
    (beta_x, beta_y): float tuple
        progressive phase shifts to be applied in radians 
    '''
    #used Balanis
    # k = 2pi/lam, and dx/y are represented in terms of fractions of a wavelength 
    beta_X = -2*np.pi*dx*np.sin(np.deg2rad(theta_0))*np.cos(np.deg2rad(phi_0)) 
    beta_Y = -2*np.pi*dy*np.sin(np.deg2rad(theta_0))*np.sin(np.deg2rad(phi_0))

    return (beta_X, beta_y)

def dispAF(dx, dy, beta_x, beta_y):
    '''
    Plots the array factor for a default square array defined in config file 
    Notes
    -----
    This function uses the config file which gives parameters for default array

    Parameters
    ----------
    dx: float
        horizontal spacing between elements (fraction of wavelength)
    dx: float
        vertical spacing between elements (fraction of wavelength)
    beta_X: float 
        Progressive phase shift in x direction
    beta_Y: float 
        Progressive phase shift in X direction

    Returns
    -------
    none
    plots the array factor magnitude 
    '''
   
    #TODO define THETA and PHI meshgrid
    theta = np.linspace(0, np.pi, 300)
    phi = np.linspace(0, np.pi * 2, 600)
    THETA, PHI = np.meshgrid(theta, phi)
    Sxm = 1
    for m in range(0,np.sqrt(NUM_ELEMENTS)+1):
        Sxm += np.exp(1j*m*(2*np.pi*dx*np.sin(THETA)*np.cos(PHI) + beta_x)) 
    
    Syn = 1 
    for n in range(0, np.sqrt(NUM_ELEMENTS)+1): 
        Syn += np.exp(1j*n*(2*np.pi*np.sin(THETA)*np.sin(PHI) + beta_y)) 

    AF = Sxm*Syn
    AF_mag = np.abs(AF)
    AF_mag_norm = AF_mag/np.max(AF_mag)
    AF_mag_norm_dB = 20*np.log10(AF_mag_norm)
    #convert to cartesian coords
    X = AF_mag_norm_dB * np.sin(THETA) * np.cos(PHI)
    Y = AF_mag_norm_dB * np.sin(THETA) * np.sin(PHI)
    Z = AF_mag_norm_dB * np.cos(THETA)
    plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.plot_surface(X,Y,Z, cmap = 'viridis', edgecolor = 'none')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title('3D Array Factor')
    plt.show()

def main():
    dx = input('enter the horizontal spacing dx in terms of wavelengths: ')
    dy = input('enter the horizontal spacing dx in terms of wavelengths: ')
    desired_phi = input('enter the azimuthal steering direction (degrees): ')
    desired_theta = input('enter the elevation steering direction (degrees): ')
    beta_x, beta_y = find_phase_shift(desired_theta, desired_phi, dx, dy)
    AF_Calc(dx,dy,beta_x,beta_y)


#run that shit
if __name__ == '__main__':
    main()
