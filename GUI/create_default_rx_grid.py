from config import THETA_LIST, PHI_LIST, NSIDE, DX, DY, DX_CP, DY_CP
import numpy as np
import state
import helpers

def create_default_rx_search_grid(dx: float, dy: float) -> np.ndarray:
    '''
    Phase shift list for each search location (paired theta/phi).
    args:
        dx, dy (float): element spacing (fraction of wavelength)
    returns:
        phases (np.ndarray): shape (K, NSIDE*NSIDE), K = len(THETA_LIST)
        each row = per-element phases in degrees, same ordering as
        AF_Calc.get_phase_shifts (row-major, element 0 = top-left)
    '''
    theta = np.deg2rad(THETA_LIST)          # (K,)
    phi = np.deg2rad(PHI_LIST)              # (K,)

    beta_x = -2 * np.pi * dx * np.sin(theta) * np.cos(phi)   # (K,)
    beta_y = -2 * np.pi * dy * np.sin(theta) * np.sin(phi)   # (K,)

    m = np.arange(NSIDE)   # rows, down = -y
    n = np.arange(NSIDE)   # columns, +x

    # (K, M, N)
    total_phase = (beta_x[:, None, None] * n[None, None, :]
                   - beta_y[:, None, None] * m[None, :, None])

    phases_deg = np.degrees(total_phase) % 360
    return phases_deg.reshape(len(theta), NSIDE * NSIDE)

# precomputed grids, one per array type
DEFAULT_RX_GRID = create_default_rx_search_grid(DX, DY)
DEFAULT_RX_GRID_CP = create_default_rx_search_grid(DX_CP, DY_CP)

def get_default_rx_grid(cp: bool | None = None)->np.ndarray:
    '''Grid for the selected array. cp=None follows the main page toggle.'''
    if cp is None:
        cp = state.CP_ARRAY
    return DEFAULT_RX_GRID_CP if cp else DEFAULT_RX_GRID

def ensure_default_rx_lut(cp: bool | None = None) -> tuple[np.ndarray, bool]:
    '''Make sure the MCU table matches the selected default grid.'''
    grid = get_default_rx_grid(cp)
    include_cp = state.CP_ARRAY if cp is None else cp
    return grid, helpers.ensure_lut(grid, include_cp=include_cp)
