import numpy as np
from matplotlib.figure import Figure
from .math import sinc_surface

LEVELS = np.linspace(0, 1, 21)   # same color scale on both plots
CBAR_LABEL = 'Received tone power (normalized)'


def _label_box(ax, x, y, text):
    ax.annotate(text, xy=(x, y), xytext=(0, 14), ha='center', va='center',
                textcoords='offset points', color='white', fontsize=10,
                bbox=dict(boxstyle='round,pad=0.2', fc='black', alpha=0.5), zorder=100)


def _finish(fig, ax, cf, title, path, dpi):
    fig.colorbar(cf, ax=ax, label=CBAR_LABEL)
    ax.set_xlabel('u = sin(θ)cos(φ)')
    ax.set_ylabel('v = sin(θ)sin(φ)')
    ax.set_aspect('equal', adjustable='box')
    ax.set_title(title)
    fig.savefig(path, dpi=dpi)


def save_raw_heatmap(u_pts, v_pts, powers, peak, theta_grid, phi_grid, path, dpi=300):
    fig = Figure(figsize=(8, 6))
    ax = fig.subplots()
    cf = ax.tricontourf(u_pts, v_pts, powers, levels=LEVELS, cmap='plasma')
    ax.scatter(u_pts, v_pts, c='k', s=8, alpha=0.4)
    ax.plot(u_pts[peak], v_pts[peak], 'ro', markersize=10)
    _label_box(ax, u_pts[peak], v_pts[peak],
               fr'$\phi$: {phi_grid:.1f}°, $\theta$: {theta_grid:.1f}°')
    _finish(fig, ax, cf, 'Beam Scan', path, dpi)


def save_interp_heatmap(u_pts, v_pts, powers, peak, u_pk, v_pk,
                        theta_ref, phi_ref, near_edge, path, dpi=300):
    U, V, S = sinc_surface(u_pts, v_pts, powers)
    fig = Figure(figsize=(8, 6))
    ax = fig.subplots()
    cf = ax.contourf(U, V, np.clip(S, 0, 1), levels=LEVELS, cmap='plasma')
    ax.scatter(u_pts, v_pts, c='k', s=8, alpha=0.4)
    ax.plot(u_pts[peak], v_pts[peak], 'wo', markersize=8, mfc='none')   # grid max
    ax.plot(u_pk, v_pk, 'ro', markersize=10)                            # refined peak
    _label_box(ax, u_pk, v_pk,
               fr'$\phi$: {phi_ref:.1f}°, $\theta$: {theta_ref:.1f}°' + ('*' if near_edge else ''))
    _finish(fig, ax, cf, 'Beam Scan (Sinc-interpolated)', path, dpi)
