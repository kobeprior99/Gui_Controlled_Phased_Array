# beam_tools/
'''
math.py
Description:Pure numpy helpers for beam scan analysis: (u, v) <-> (theta, phi)
conversions and sinc interpolation of the sampled power surface.
No UI or SDR imports.
Author:Kobe Prior
Date Last Modified: Nov 24,2026
'''
import numpy as np
from config import UV_STEP, r_max


def uv_from_angles(theta_deg, phi_deg):
    t, p = np.deg2rad(np.asarray(theta_deg)), np.deg2rad(np.asarray(phi_deg))
    return np.sin(t) * np.cos(p), np.sin(t) * np.sin(p)


def uv_to_angles(u, v):
    rho = min(np.hypot(u, v), 1.0)
    return np.degrees(np.arcsin(rho)), np.degrees(np.arctan2(v, u)) % 360


def refine_peak(u_pts, v_pts, powers, step=UV_STEP, half_width=1.0, n_fine=81):
    '''
    Sinc-interpolate the sampled power surface near the coarse peak and
    return the off-grid peak (u, v) and whether it is near the scan edge.
    '''
    k = np.argmax(powers)
    uc, vc = u_pts[k], v_pts[k]
    uf = np.linspace(uc - half_width * step, uc + half_width * step, n_fine)
    vf = np.linspace(vc - half_width * step, vc + half_width * step, n_fine)

    Ku = np.sinc((uf[:, None] - u_pts[None, :]) / step)   # (n_fine, K)
    Kv = np.sinc((vf[:, None] - v_pts[None, :]) / step)   # (n_fine, K)
    surf = np.einsum('ik,jk,k->ji', Ku, Kv, powers)       # rows = v, cols = u

    j, i = np.unravel_index(np.argmax(surf), surf.shape)
    near_edge = np.hypot(uc, vc) > r_max - step
    return uf[i], vf[j], near_edge


def sinc_surface(u_pts, v_pts, powers, step=UV_STEP, n=121):
    '''Sinc-interpolate the whole scan region onto a fine (u, v) grid.'''
    g = np.linspace(-r_max, r_max, n)
    U, V = np.meshgrid(g, g)
    Ku = np.sinc((g[:, None] - u_pts[None, :]) / step)   # (n, K)
    Kv = np.sinc((g[:, None] - v_pts[None, :]) / step)   # (n, K)
    S = np.einsum('jk,ik,k->ji', Kv, Ku, powers)         # rows = v, cols = u
    S = np.ma.masked_where(U**2 + V**2 > r_max**2, S)    # only show inside the scan circle
    return U, V, S
