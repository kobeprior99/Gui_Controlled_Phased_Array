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
from matplotlib import cm
from matplotlib.colors import ListedColormap
#config file contains some useful constants that we'll make use of 
from config import *
DEFAULT_RX_GRID = None
def find_betas(theta_0: float, phi_0: float, dx: float, dy: float)->tuple:
    '''
    Calculate the phase shifts required to steer in certain direction

    Parameters
    ----------
    theta_0: float 
        elevation steer direction in degrees
    phi_0: float
        azimuthal steer direction in degrees
    dx: float
        x spacing between elements (fraction of wavelength)
    dy: float
        y spacing between elements (fraction of wavelength)
    Returns
    -------
    (beta_x, beta_y): float tuple
        progressive phase shifts to be applied in radians 
    '''
    #used Balanis
    # k = 2pi/lam, and dx/y are represented in terms of fractions of a wavelength 
    theta_0 = np.deg2rad(theta_0) 
    phi_0 = np.deg2rad(phi_0) 
    beta_X = -2 * np.pi * dx * np.sin(theta_0) * np.cos(phi_0) 
    beta_Y = -2 * np.pi * dy * np.sin(theta_0) * np.sin(phi_0)

    return beta_X, beta_Y


def get_phase_shifts(beta_x: float, beta_y: float)->np.ndarray:
    '''
    Get the phase shifts to apply to each element in a N element array
    Parameter:
        beta_x(float):
        beta_y(float):
    Returns:
        1D array of phases in degrees size =NUM_ELEMENTS defined in config fil
    '''
    #create index grids
    M, N = np.meshgrid(np.arange(NSIDE), np.arange(NSIDE), indexing='ij')
    #compute phase shifts for each element
    phases = (beta_x * M + beta_y * N)
    phases = np.degrees(phases) % 360
    return phases.flatten()




def dispAF(dx: float, dy: float, beta_x: float, beta_y: float, disp:bool):
    '''
    Plots the array factor for a default square array defined in config file 
    Notes
    -----
    Parameters
    ----------
    dx: float
        X spacing between elements (fraction of wavelength)
    dx: float
        Y spacing between elements (fraction of wavelength)
    beta_X: float 
        Progressive phase shift in x direction
    beta_Y: float 
        Progressive phase shift in y direction
    disp: bool
       True: show or False: save
    Returns
    -------
    none
    plots the array factor magnitude 
    plot uv
    '''
    # define theta phi mesh grid 
    theta = np.linspace(0, np.pi/2, 300)
    phi = np.linspace(0, np.pi * 2, 600)
    THETA, PHI = np.meshgrid(theta, phi)
    # used multiple times 
    sinTH =np.sin(THETA) 
    cosPH = np.cos(PHI)
    sinPH = np.sin(PHI)
    
    # Define x part of array factor 
    Nside = int(np.sqrt(NUM_ELEMENTS))
    m_idx = np.arange(Nside).reshape(-1, 1, 1)
    Sxm = np.sum(np.exp(1j * m_idx * (2*np.pi*dx*sinTH*cosPH + beta_x)), axis=0)
      
    # Define y part of array factor 
    n_idx = np.arange(Nside).reshape(-1, 1, 1)
    Syn = np.sum(np.exp(1j * n_idx * (2*np.pi*dy*sinTH*sinPH + beta_y)), axis=0)

    AF = Sxm * Syn
    AF_mag = np.abs(AF) 
    AF_mag_norm = AF_mag/np.max(AF_mag)
    #convert to cartesian coords
    X = AF_mag_norm * sinTH * cosPH
    Y = AF_mag_norm * sinTH * sinPH
    Z = AF_mag_norm * np.cos(THETA)
    fig = plt.figure(figsize = (9,7))
    ax = fig.add_subplot(111, projection='3d')  
    cmap = cm.jet
    custom_cmap = ListedColormap(cmap(np.linspace(0.3, 1, 256)))
    surf = ax.plot_surface(
        X,Y,Z,
        rstride=3, cstride=3,
        cmap=custom_cmap,
        edgecolors='k', 
        linewidth=0.2,
        antialiased=True
    )
    #color bar
    m = cm.ScalarMappable(cmap=custom_cmap)
    m.set_array(AF_mag_norm)
    cbar = fig.colorbar(m, ax=ax, shrink=0.6, aspect=15)
    cbar.set_label('Normalized Array Factor (linear scale)', fontsize=10)

    ax.set_xlim(-1,1)
    ax.set_ylim(-1,1)
    ax.set_zlim(0,1)
    ax.set_box_aspect([1,1,1])
    ax.set_axis_off()

    #Redraw Custon Axes through the origin
    #X
    ax.plot([-1,1], [0,0], [0,0], color = 'k', lw=2)
    ax.text(1.2,0,0,'X', color='k', fontsize=12, fontweight = 'bold')
    #Y
    ax.plot([0,0], [-1,1], [0,0], color = 'k', lw=2)
    ax.text(0,1.2,0,'Y', color='k', fontsize=12, fontweight = 'bold')
    #Z
    ax.plot([0,0], [0,0], [0,1], color = 'k', lw=2)
    ax.text(0,0,1.1,'Z', color='k', fontsize=12, fontweight = 'bold')

    ax.grid(True, linestyle = '--', linewidth = 0.5)
    ax.set_title('Normalized Array Factor (Spherical Format)', pad=20)
    ax.view_init(elev=25, azim=30)
    if not disp:
        plt.savefig('media/AF.png', bbox_inches='tight', dpi = 300)
    else:
        plt.show()
    # ax.dist = 9
    u=sinTH*cosPH
    v=sinTH*sinPH
    fig_uv, ax_uv= plt.subplots( figsize=(7,6))
    uv_plot = ax_uv.pcolormesh(
        u, v, AF_mag_norm,
        shading='auto',
        cmap=custom_cmap
    )

    cbar_uv = plt.colorbar(uv_plot, ax=ax_uv)
    cbar_uv.set_label('Normalized Array Factor (linear scale)', fontsize=10)

    ax_uv.set_xlabel('u = sin(θ)cos(φ)')
    ax_uv.set_ylabel('v = sin(θ)sin(φ)')
    ax_uv.set_title('Normalized Array Factor (UV Plot)')
    ax_uv.set_aspect('equal', adjustable='box')
    ax_uv.set_xlim(-1, 1)
    ax_uv.set_ylim(-1, 1)
    ax_uv.grid(True, linestyle='--', linewidth=0.5)

    if not disp:
        plt.savefig('media/uv.png', bbox_inches='tight', dpi=300)
        plt.close(fig_uv)
    else:
        plt.show()

def main():
    dx = float(input('enter the horizontal spacing dx in terms of wavelengths: '))
    dy = float(input('enter the vertical spacing dy in terms of wavelengths: '))
    desired_phi = float(input('enter the azimuthal steering direction (degrees): '))
    desired_theta = float(input('enter the elevation steering direction (degrees): '))
    beta_x, beta_y = find_betas(desired_theta, desired_phi, dx, dy)
    dispAF(dx, dy, beta_x, beta_y,disp=True)

def runAF_Calc(dx: float,dy: float,theta: float,phi: float)->np.ndarray:
    '''
    run the array factor calculation to get progressive phase shifts
    and generate plot
    Parameters:
        dx: float
            horizontal spacing between elements (fraction of wavelength)
        dx: float
            vertical spacing between elements (fraction of wavelength)
        theta: float
            desired elevaiton steering angle
        phi:
            desired azimuthal steering angle
    Returns: phases an array of the phases that go to each element 
    '''
    betaX,betaY = find_betas(theta, phi, dx,dy) 
    phases = get_phase_shifts(betaX, betaY)
    dispAF(dx,dy,betaX,betaY,disp=False)
    #return betax and y to be used in actually shifting the array
    return phases 
    
#run that shit
if __name__ == '__main__':
    main()
