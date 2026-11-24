'''
Purpose: Solve for the element phases that generate an OAM mode of topological
charge l on the square array, instead of hard-coding them.

Each element is fed the phase  l * phi_n  where phi_n is the azimuthal angle of
element n measured about the array center.

Element ordering (matches the port order):
    index 0  = top-left element, read left->right, then top->bottom,
    index 15 = bottom-right element.
Coordinates: +x to the right, +y up, origin at the array center.
'''
import numpy as np
from config import NSIDE
from AF_Calc import get_spacing


def element_positions(dx: float, dy: float, nside: int = NSIDE) -> tuple:
    '''
    Element coordinates relative to the array center, ordered top-left -> bottom-right.
    dx, dy: element spacing (any consistent unit; only the ratio matters for phases)
    Returns (x, y) arrays of length nside**2
    '''
    idx = np.arange(nside * nside)
    row, col = idx // nside, idx % nside
    x = (col - (nside - 1) / 2) * dx
    y = ((nside - 1) / 2 - row) * dy
    return x, y


def element_azimuth_deg(dx: float, dy: float, nside: int = NSIDE) -> np.ndarray:
    '''Azimuthal angle (deg, -180..180) of each element about the array center.'''
    x, y = element_positions(dx, dy, nside)
    return np.degrees(np.arctan2(y, x))


def compute_oam_phases(mode: int, dx: float, dy: float, nside: int = NSIDE) -> np.ndarray:
    '''
    Phases (deg, wrapped to 0..360) for OAM mode l = mode.
    Even-sized array => no element sits on the atan2 branch cut, and since l is an
    integer, l*phi is continuous modulo 360.
    '''
    return (int(mode) * element_azimuth_deg(dx, dy, nside)) % 360


def get_oam_phases(mode, cp: bool | None = None) -> np.ndarray:
    '''
    OAM phases for the selected array (DX_CP/DY_CP if circularly polarized,
    else DX/DY). cp=None follows the main page toggle.
    '''
    dx, dy = get_spacing(cp)
    return compute_oam_phases(int(mode), dx, dy)


if __name__ == '__main__':
    np.set_printoptions(precision=2, suppress=True)
    for cp in (False, True):
        print('CP array' if cp else 'Linear array')
        for l in (1, 2):
            print(f'  l={l}:', get_oam_phases(l, cp))
