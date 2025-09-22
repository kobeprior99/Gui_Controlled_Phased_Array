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
from mpl_toolkits import mplot3d
#config file contains some useful constants that we'll make use of 
from config import *

def find_phase_shift(theta_0, phi_0, dx, dy):
    '''
    Calculate the phase shifts required to steer in certain direction

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
     
    beta_X = -2 * np.pi * dx * np.sin(theta_0)*np.cos(phi_0) 
    beta_Y = -2 * np.pi * dy * np.sin(theta_0)*np.sin(phi_0)

    return beta_X, beta_Y

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
        Progressive phase shift in y direction

    Returns
    -------
    none
    plots the array factor magnitude 
    '''
   
    #TODO define THETA and PHI meshgrid
    theta = np.linspace(0, np.pi/2, 300)
    phi = np.linspace(0, np.pi * 2, 600)
    THETA, PHI = np.meshgrid(theta, phi)
    Nside = int(np.sqrt(NUM_ELEMENTS))
    Sxm = 0
    for m in range(Nside):
        Sxm += np.exp(1j*m*(2*np.pi*dx*np.sin(THETA)*np.cos(PHI) + beta_x)) 
    
    Syn = 0 
    for n in range(Nside): 
        Syn += np.exp(1j*n*(2*np.pi*dy*np.sin(THETA)*np.sin(PHI) + beta_y)) 

    AF = Sxm * Syn
    AF_mag = np.abs(AF) 
    AF_mag_norm = AF_mag/np.max(AF_mag)
    #convert to cartesian coords
    X = AF_mag_norm * np.sin(THETA) * np.cos(PHI)
    Y = AF_mag_norm * np.sin(THETA) * np.sin(PHI)
    Z = AF_mag_norm * np.cos(THETA)
    fig = plt.figure()
    ax = fig.add_subplot(111, projection = '3d')
    surf = ax.plot_surface(X,Y,Z,cmap ='plasma', 
    linewidth = 0, antialiased =False) 
    ax.set_xlim(-1.01, 1.01)
    ax.set_ylim(-1.01, 1.01)
    ax.set_zlim(0, 1.01)
    ax.set_title('Array Factor')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    fig.colorbar(surf)
    plt.show()

def main():
    dx = float(input('enter the horizontal spacing dx in terms of wavelengths: '))
    dy = float(input('enter the vertical spacing dy in terms of wavelengths: '))
    desired_phi = float(input('enter the azimuthal steering direction (degrees): '))
    desired_theta = float(input('enter the elevation steering direction (degrees): '))
    beta_x, beta_y = find_phase_shift(desired_theta, desired_phi, dx, dy)
    dispAF(dx,dy,beta_x,beta_y)


#run that shit
if __name__ == '__main__':
    main()
