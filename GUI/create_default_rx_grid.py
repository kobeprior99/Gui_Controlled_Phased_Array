from config import theta_range, phi_range, nside, dx,dy
import numpy as np
def create_default_rx_search_grid(dx: float, dy: float)->none:
    '''
    compute a list of phase shift lists for each search loaction for rx doa est.
    originally was a nested for loop but vectorized it for speed
    args:
        dx,dy(float): element spacing
    returns:
    phases (np.ndarray): vshape = (len(theta_range)*len(phi_range), num_elements)
    each row = num_elements phase values
    '''
    theta = np.deg2rad(theta_range)
    phi = np.deg2rad(phi_range)
    theta,phi = np.meshgrid(theta, phi, indexing='ij')
    #compute betas 
    beta_x = -2 * np.pi * dx * np.sin(theta) * np.cos(phi) 
    beta_y = -2 * np.pi * dy * np.sin(theta) * np.sin(phi)
    #element indexing
    nx_idx = np.arange(nside)
    ny_idx = np.arange(nside)

    # compute total phase shift (broadcasted)
    # shape: (nside, nside, len(theta), len(phi))
    total_phase = (nx_idx[:, none, none, none] * beta_x[none,none, :, :] +
        ny_idx[none, :, none, none] * beta_y[none, none, none, :])

    # convert to degrees and wrap to 0–360
    phases_deg = np.degrees(total_phase) % 360
    return phases_deg.reshape(nside * nside, -1).t

default_rx_grid = create_default_rx_search_grid(dx,dy)
#debug
'''
for i, phase_row in enumerate(default_rx_grid):
    print(f'Direction {i}: {phase_row}')
'''
