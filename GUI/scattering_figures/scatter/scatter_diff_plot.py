import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import RegularGridInterpolator

# ── Grid axes ──────────────────────────────────────────────────────────────────
# theta: incidence angle (rows), psi: tilt/rotation angle (cols)
THETA = np.array([0,  30,  45,  60,  90])
PSI   = np.array([0,  10,  15,  20,  25,  30])

# ── Scattering data tables (rows = theta, cols = psi) ─────────────────────────

# Plate scatterer — LG_0^0  (reference)
PLATE_LG00 = np.array([
    [ 6.41,  7.72,  4.35, -3.77, -3.27,  1.20],
    [ 4.90,  5.65,  2.06, -3.64, -2.27,  0.51],
    [ 3.19,  2.50, -0.40, -1.86, -0.20,  0.69],
    [ 2.32, -0.82, -2.76, -1.55,  0.74,  1.05],
    [ 4.02, -2.73, -5.15, -3.58,  0.60,  1.13],
])

# Plate scatterer — LG_0^1  (candidate)
PLATE_LG01 = np.array([
    [-0.92,  3.75,  0.28, -0.61,  3.79,  6.72],
    [-0.69,  3.50,  1.87,  1.57,  2.95,  4.52],
    [-0.03,  2.77,  2.02,  2.80,  3.88,  3.91],
    [ 1.15,  2.35,  1.79,  3.41,  4.63,  4.54],
    [ 2.43,  1.41,  1.74,  3.30,  4.59,  5.01],
])

# Plate scatterer — LG_0^2  (candidate)
PLATE_LG02 = np.array([
    [ 2.25,  1.05,  1.54,  1.87,  0.76, -0.55],
    [ 2.34,  0.88,  0.99,  1.93,  0.98,  0.29],
    [ 1.61,  0.80,  0.82,  1.55,  1.26,  0.77],
    [ 1.36,  0.94,  0.77,  1.30,  0.99,  0.85],
    [ 0.54,  0.96,  1.19,  1.04,  0.49,  0.61],
])

PLATE_HG10 = np.array([
    [ 0.57,  0.89, -0.18, -1.43, -0.99,  1.68],
    [ 0.42,  0.44, -0.17, -0.64, -0.37,  0.80],
    [ 0.19,  0.14, -0.32, -0.31,  0.22,  0.86],
    [ 0.11, -0.26, -0.42, -0.41,  0.58,  1.08],
    [ 0.37, -0.53, -0.67, -0.76,  0.45,  1.29],
])

PLATE_HG11 = np.array([
    [ 0.00, -0.79, -0.45,  0.84,  0.31, -0.23],
    [ 0.07, -0.96, -0.35,  0.44,  0.22, -0.25],
    [ 0.03, -0.19, -0.22,  0.31,  0.08, -0.27],
    [ 0.02,  0.01, -0.04,  0.22,  0.03, -0.33],
    [-0.30, -0.02,  0.14,  0.24, -0.02, -0.23],
])

# ── Ellipsoid scatterer ────────────────────────────────────────────────────────
ELLIPSOID_LG00 = np.array([
    [ 5.88,  4.79,  0.71, -7.69, -1.71,  0.18],
    [ 4.07,  0.53, -1.93,  0.50, -0.26, -1.06],
    [ 1.46, -1.08,  0.29,  1.28, -0.88, -1.40],
    [-1.10, -0.07,  1.25,  1.20, -1.92, -1.94],
    [-0.81,  1.10,  1.20,  0.53, -1.93, -1.57],
])

ELLIPSOID_LG01 = np.array([
    [-0.23,  1.84,  0.57,  1.54,  3.46,  3.86],
    [ 0.69,  2.21,  2.06,  2.54,  2.75,  1.74],
    [ 0.83,  2.43,  2.76,  2.76,  2.05,  1.57],
    [ 1.56,  2.50,  2.82,  2.60,  1.75,  1.69],
    [ 1.62,  2.62,  2.70,  2.49,  1.91,  1.66],
])

ELLIPSOID_LG02 = np.array([
    [-0.82,  0.76,  0.49, -0.38, -0.74, -0.10],
    [-0.74,  0.19, -0.14,  0.05,  0.10,  0.06],
    [-0.54, -0.31, -0.10,  0.21,  0.28, -0.02],
    [-0.23, -0.39, -0.11,  0.28, -0.06, -0.44],
    [-0.33, -0.41,  0.04,  0.34, -0.05, -0.35],
])

ELLIPSOID_HG10 = np.array([
    [ 0.31,  0.09, -0.75, -1.14, -0.09,  1.28],
    [ 0.13, -0.14, -0.33, -0.18,  0.23,  0.27],
    [-0.13, -0.19, -0.05,  0.09,  0.07,  0.02],
    [-0.28,  0.02, -0.02,  0.06, -0.15,  1.17],
    [-0.14,  0.19, -0.13,  0.13, -0.41,  1.29],
])

ELLIPSOID_HG11 = np.array([
    [-0.43, -0.76, -0.44,  0.34, -0.52, -0.62],
    [-0.39, -0.46, -0.48,  0.02, -0.45, -0.44],
    [-0.35, -0.36, -0.42, -0.38, -0.46, -0.52],
    [-0.40, -0.34, -0.39, -0.39, -0.50, -0.48],
    [-0.48, -0.35, -0.41, -0.43, -0.51, -0.49],
])

# ── Corner reflector scatterer ─────────────────────────────────────────────────
CORNER_LG00 = np.array([
    [ 0.03, -4.33,  0.62,  0.73, -1.55, -4.75],
    [ 3.59,  7.58,  6.87,  2.26, -4.95, -2.99],
    [-1.95,  4.79,  4.26, -0.79, -4.63, -1.71],
    [-2.60,  3.05,  2.52, -1.57, -4.28, -1.39],
    [-1.65,  1.58,  0.10, -3.26, -2.72, -0.16],
])

CORNER_LG01 = np.array([
    [-1.76,  2.09,  1.43,  1.92,  1.81,  3.04],
    [ 0.08,  0.59,  2.53, -0.92, -4.85,  2.43],
    [-1.21,  1.44,  1.46,  0.96, -0.48,  1.41],
    [ 0.66,  0.96,  0.04,  0.22, -0.14,  1.14],
    [ 1.38,  2.73,  2.37,  1.65,  1.09,  2.54],
])

CORNER_LG02 = np.array([
    [ 0.34,  0.55,  0.35,  0.97,  0.79, -0.81],
    [-0.17, -1.38, -0.03,  1.99,  2.26, -0.06],
    [ 0.69, -0.72, -0.06,  0.94,  1.45,  0.00],
    [ 0.52, -0.22,  0.19,  0.58,  1.00, -0.20],
    [ 0.19,  0.81,  0.68,  0.72,  0.33, -0.65],
])

CORNER_HG10 = np.array([
    [ 0.12,  0.03, -0.75, -0.25, -0.27,  0.19],
    [ 0.52,  1.10,  0.71, -0.48, -2.72, -0.73],
    [ 0.33,  0.86, -0.07, -0.06, -0.99,  0.09],
    [ 0.39,  0.66, -0.46, -0.35, -0.88,  0.08],
    [ 0.26,  0.12, -0.28, -0.07, -0.10,  0.94],
])

CORNER_HG11 = np.array([
    [ 0.02,  0.16,  0.02, -0.50,  0.03,  0.01],
    [ 0.01, -0.78, -0.29,  0.11,  0.53, -0.03],
    [ 0.59, -0.17, -0.34,  0.25,  0.33,  0.05],
    [ 0.22, -0.40, -0.25,  0.12,  0.13,  0.01],
    [-0.07, -0.21,  0.03,  0.20, -0.08, -0.30],
])

# ── Styling constants ──────────────────────────────────────────────────────────
BG     = '#0d1117'
TICK_C = '#aabbcc'


# ══════════════════════════════════════════════════════════════════════════════
def plot_scatter_diff(
    reference: np.ndarray,
    candidate: np.ndarray,
    scatterer_name: str,
    reference_label: str  = r'LG$_0^0$',
    candidate_label: str  = r'LG$_0^1$',
    theta: np.ndarray     = THETA,
    psi:   np.ndarray     = PSI,
    save:  bool           = True,
    fname: str | None     = None,
    dpi:   int            = 180,
) -> tuple[plt.Figure, plt.Axes]:
    """
    Plot the back-scattered power difference  (candidate − reference)  as a
    2-D interpolated heat-map over (theta, psi).

    Parameters
    ----------
    reference       : 2-D array  shape (len(theta), len(psi))  — reference mode
    candidate       : 2-D array  same shape                    — candidate mode
    scatterer_name  : human-readable scatterer label, e.g. 'Plate'
    reference_label : TeX label for the reference mode (default LG₀⁰)
    candidate_label : TeX label for the candidate mode (default LG₀¹)
    theta           : incidence-angle grid points (deg)
    psi             : tilt/rotation-angle grid points (deg)
    save            : write PNG to disk when True
    fname           : output filename; auto-generated when None
    dpi             : raster resolution

    Returns
    -------
    fig, ax  — matplotlib objects for further customisation if needed

    Color convention
    ----------------
    Green  →  candidate stronger  (positive difference)
    Red    →  reference stronger  (negative difference)
    """
    diff = candidate - reference

    # ── Fine interpolation grid ────────────────────────────────────────────────
    theta_fine = np.linspace(theta.min(), theta.max(), 400)
    psi_fine   = np.linspace(psi.min(),   psi.max(),   400)
    T_fine, P_fine = np.meshgrid(theta_fine, psi_fine, indexing='ij')

    interp = RegularGridInterpolator((theta, psi), diff, method='linear')
    pts    = np.column_stack([T_fine.ravel(), P_fine.ravel()])
    Z      = interp(pts).reshape(T_fine.shape)

    clim = max(np.abs(Z).max(), 0.5)

    # ── Figure / axes ──────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(11, 6.5), facecolor=BG)
    ax.set_facecolor(BG)

    im = ax.pcolormesh(
        theta_fine, psi_fine, Z.T,
        cmap='RdYlGn', vmin=-clim, vmax=clim, shading='auto',
    )

    # Zero-crossing contour
    cs = ax.contour(
        theta_fine, psi_fine, Z.T,
        levels=[0], colors='black', linewidths=2.2, linestyles='--',
    )
    ax.clabel(cs, fmt='zero', fontsize=9, colors='black',
              inline=True, inline_spacing=6)

    # Data-point labels
    for i, th in enumerate(theta):
        for j, ps in enumerate(psi):
            val = diff[i, j]
            # nudge labels inward at the right boundary
            if th == theta.max():
                x_off, ha = -2.0, 'right'
            else:
                x_off, ha = 1.8,  'left'
            ax.plot(th, ps, 'x', color='black', markersize=5, zorder=5)
            ax.text(
                th + x_off, ps, f'{val:+.2f} dB',
                ha=ha, va='center',
                fontsize=8, color='black', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.15',
                          facecolor='white', alpha=0.55, edgecolor='none'),
            )

    # ── Labels / ticks ─────────────────────────────────────────────────────────
    ax.set_title(
        f'{scatterer_name}  —  {candidate_label} − {reference_label}  '
        f'Back-Scattered Power Difference (dB)\n'
        f'Green → {candidate_label} stronger   |   Red → {reference_label} stronger',
        color='white', fontsize=13, fontweight='bold', pad=12,
    )
    ax.set_xlabel('θ  (deg)', color=TICK_C, fontsize=13)
    ax.set_ylabel('ψ  (deg)', color=TICK_C, fontsize=13)
    ax.tick_params(colors=TICK_C, labelsize=11)
    for spine in ax.spines.values():
        spine.set_edgecolor('#223344')

    ax.set_xlim(theta.min(), theta.max())
    ax.set_ylim(psi.min(),   psi.max())
    ax.set_xticks(theta)
    ax.set_yticks(psi)

    cbar = fig.colorbar(im, ax=ax, pad=0.02)
    cbar.ax.yaxis.set_tick_params(color=TICK_C, labelsize=10)
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color=TICK_C)
    cbar.set_label(
        f'Δ dB  ({candidate_label} − {reference_label})',
        color=TICK_C, fontsize=11,
    )

    plt.tight_layout(pad=2.0)

    # ── Save ───────────────────────────────────────────────────────────────────
    if save:
        if fname is None:
            safe_name  = scatterer_name.lower().replace(' ', '_')
            cand_short = candidate_label.replace('$', '').replace('^', '').replace('{', '').replace('}', '').replace('\\', '')
            ref_short  = reference_label.replace('$', '').replace('^', '').replace('{', '').replace('}', '').replace('\\', '')
            fname = f'scatter-dif-plots/scatter_diff_{safe_name}_{cand_short}_vs_{ref_short}.png'
        plt.savefig(fname, dpi=dpi, bbox_inches='tight',
                    facecolor=fig.get_facecolor())
        print(f"Saved → {fname}")

    return fig, ax


# ══════════════════════════════════════════════════════════════════════════════
# Example calls
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':

    # Plate: LG01 vs LG00  (your updated tables)
    plot_scatter_diff(
        reference      = PLATE_LG00,
        candidate      = PLATE_LG01,
        scatterer_name = 'Plate',
        reference_label= r'LG$_0^0$',
        candidate_label= r'LG$_0^1$',
    )

    plot_scatter_diff(
        reference      = PLATE_LG00,
        candidate      = PLATE_LG02,
        scatterer_name = 'Plate',
        reference_label= r'LG$_0^0$',
        candidate_label= r'LG$_0^2$',
    )

    plot_scatter_diff(
        reference      = PLATE_LG00,
        candidate      = PLATE_HG10,
        scatterer_name = 'Plate',
        reference_label= r'LG$_0^0$',
        candidate_label= r'HG$_{10}$',
    )

    plot_scatter_diff(
        reference      = PLATE_LG00,
        candidate      = PLATE_HG11,
        scatterer_name = 'Plate',
        reference_label= r'LG$_0^0$',
        candidate_label= r'HG$_{11}$',
    )


    plot_scatter_diff(
        reference      = ELLIPSOID_LG00,
        candidate      = ELLIPSOID_LG01,
        scatterer_name = 'Ellipsoid',
        reference_label= r'LG$_0^0$',
        candidate_label= r'LG$_0^1$',
    )

    plot_scatter_diff(
        reference      = ELLIPSOID_LG00,
        candidate      = ELLIPSOID_LG02,
        scatterer_name = 'Ellipsoid',
        reference_label= r'LG$_0^0$',
        candidate_label= r'LG$_0^2$',
    )

    plot_scatter_diff(
        reference      = ELLIPSOID_LG00,
        candidate      = ELLIPSOID_HG10,
        scatterer_name = 'Ellipsoid',
        reference_label= r'LG$_0^0$',
        candidate_label= r'HG$_{10}$',
    )

    plot_scatter_diff(
        reference      = ELLIPSOID_LG00,
        candidate      = ELLIPSOID_HG11,
        scatterer_name = 'Ellipsoid',
        reference_label= r'LG$_0^0$',
        candidate_label= r'HG$_{11}$',
    )

    plot_scatter_diff(
        reference      = CORNER_LG00,
        candidate      = CORNER_LG01,
        scatterer_name = 'Corner Reflector',
        reference_label= r'LG$_0^0$',
        candidate_label= r'LG$_0^1$',
    )

    plot_scatter_diff(
        reference      = CORNER_LG00,
        candidate      = CORNER_LG02,
        scatterer_name = 'Corner Reflector',
        reference_label= r'LG$_0^0$',
        candidate_label= r'LG$_0^2$',
    )

    plot_scatter_diff(
        reference      = CORNER_LG00,
        candidate      = CORNER_HG10,
        scatterer_name = 'Corner Reflector',
        reference_label= r'LG$_0^0$',
        candidate_label= r'HG$_{10}$',
    )

    plot_scatter_diff(
        reference      = CORNER_LG00,
        candidate      = CORNER_HG11,
        scatterer_name = 'Corner Reflector',
        reference_label= r'LG$_0^0$',
        candidate_label= r'HG$_{11}$',
    )
    plt.show()
