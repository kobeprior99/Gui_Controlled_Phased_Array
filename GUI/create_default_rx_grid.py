from config import THETA_RANGE, PHI_RANGE, NSIDE, DX,DY
import numpy as np
def create_default_rx_search_grid(dx: float, dy: float)->None:
    '''
    compute a list of phase shift lists for each search loaction for rx doa est.
    originally was a nested for loop but vectorized it for speed
    args:
        dx,dy(float): element spacing
    returns:
    phases (np.ndarray): vshape = (len(theta_range)*len(phi_range), num_elements)
    each row = num_elements phase values
    '''
    theta = np.deg2rad(THETA_RANGE)
    phi = np.deg2rad(PHI_RANGE)
    theta,phi = np.meshgrid(theta, phi, indexing='ij')
    #compute betas 
    beta_x = -2 * np.pi * dx * np.sin(theta) * np.cos(phi) 
    beta_y = -2 * np.pi * dy * np.sin(theta) * np.sin(phi)
    #element indexing
    nx_idx = np.arange(NSIDE)
    ny_idx = np.arange(NSIDE)

    # compute total phase shift (broadcasted)
    # shape: (nside, nside, len(theta), len(phi))
    total_phase = (nx_idx[:, None, None, None] * beta_x[None,None, :, :] +
        ny_idx[None, :, None, None] * beta_y[None, None, None, :])

    # convert to degrees and wrap to 0–360
    phases_deg = np.degrees(total_phase) % 360
    return phases_deg.reshape(NSIDE * NSIDE, -1).T

DEFAULT_RX_GRID = create_default_rx_search_grid(DX,DY)
#debug
'''
for i, phase_row in enumerate(default_rx_grid):
    print(f'Direction {i}: {phase_row}')
'''
