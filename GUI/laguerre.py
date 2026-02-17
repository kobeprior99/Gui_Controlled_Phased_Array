from scipy.special import genlaguerre
from math import factorial
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
from config import *
import PIL
def LGlpz(l, p, z0, w0, lambda0, xs, ys):
    """
    Computes the complex electric field distribution of a Laguerre–Gaussian mode LG_p^l
    evaluated at a transverse plane z = z0.

    Parameters
    ----------
    l : int
        Azimuthal index (topological charge).
        Determines orbital angular momentum (OAM) and helical phase exp(-j l φ).

    p : int
        Radial mode index.
        Determines number of radial intensity rings.

    z0 : float
        Axial distance (meters) from the beam waist (z = 0 plane).
        Controls beam curvature and Gouy phase.

    w0 : float
        Beam waist radius at z = 0 (meters).
        Determines initial spot size and Rayleigh range.

    lambda0 : float
        Freespace Wavelength (meters).

    xs : ndarray or float
        x-coordinate(s) in the transverse plane (meters).

    ys : ndarray or float
        y-coordinate(s) in the transverse plane (meters).

    Derived Quantities
    ------------------
    zr : float
        Rayleigh range:
            zr = π w0² / λ

    wz : float
        Beam radius at z0:
            w(z) = w0 sqrt(1 + (z0/zr)²)

    r : ndarray or float
        Radial distance:
            r = sqrt(x² + y²)

    Rz : float
        Radius of curvature of the phase front:
            R(z) = z0 (1 + (zr/z0)²)
        If z0 = 0, Rz = ∞.

    phi : ndarray or float
        Azimuthal angle:
            φ = atan2(y, x)

    psiz : float
        Gouy phase:
            ψ(z) = (|l| + 2p + 1) arctan(z0/zr)

    Returns
    -------
    E : complex ndarray or complex float
        Complex field value of the Laguerre–Gaussian beam at each (x, y) point.
        Includes:

            - Radial amplitude profile
            - Laguerre polynomial dependence
            - Quadratic curvature phase term
            - Azimuthal OAM phase term
            - Gouy phase term

        The magnitude |E| gives the field amplitude.
        The angle ∠E gives the phase to assign to an array element.
    """
    zr = np.pi*w0**2 / lambda0
    wz = w0*np.sqrt(1+(z0/zr)**2)
    r= np.sqrt(xs**2 + ys**2)
    Rz = np.inf if z0==0 else z0*(1+(zr/z0)**2)
    k=2*np.pi / lambda0
    phi = np.atan2(ys,xs)
    psiz = (np.abs(l) + 2*p + 1)*np.atan2(z0,zr)

    term1 = (np.sqrt(2*factorial(np.abs(p))/(np.pi*factorial(np.abs(p+np.abs(l)))))/wz)
    term2 = ((r*np.sqrt(2)/wz)**np.abs(l))*np.exp(-r**2 / wz**2)*genlaguerre(p,np.abs(l))(2*r**2/wz**2)
    term3 = np.exp((-1j*k*r**2) / (2*Rz))
    term4 = np.exp(-1j*l*phi)
    term5 = np.exp(1j*psiz)
    return term1*term2*term3*term4*term5

def animate_sweep_z0(l=1, p=0, z0_values=None, w0=0.2, interval=800):

    if z0_values is None:
        z0_values = np.linspace(0.05, 1.5, 20)

    Nx, Ny = 4, 4

    # Physical element locations (meters)
    x_coords = (np.arange(Nx) - (Nx-1)/2) * dx_m
    y_coords = (np.arange(Ny) - (Ny-1)/2) * dy_m

    xs, ys = np.meshgrid(x_coords, y_coords)

    fig, ax = plt.subplots()
    img = ax.imshow(np.zeros((Ny, Nx)), vmin=-180, vmax=180)

    cbar = plt.colorbar(img, ax=ax)
    cbar.set_label("Phase (degrees)")

    # Axis ticks labeled in meters
    ax.set_xticks(range(Nx))
    ax.set_yticks(range(Ny))
    ax.set_xticklabels([f"{x:.3f}" for x in x_coords])
    ax.set_yticklabels([f"{y:.3f}" for y in y_coords])

    ax.set_xlabel("Element Position X (m)")
    ax.set_ylabel("Element Position Y (m)")

    # Create text objects (one per element)
    text_grid = []
    for i in range(Ny):
        row = []
        for j in range(Nx):
            txt = ax.text(j, i, "",
                          ha='center', va='center',
                          color='white', fontsize=10)
            row.append(txt)
        text_grid.append(row)

    def update(frame):
        z0 = z0_values[frame]

        E = LGlpz(l, p, z0, w0, LAMBDA, xs, ys)
        phase_deg = np.angle(E, deg=True)
        phase_deg = (phase_deg + 180) % 360 - 180

        img.set_data(phase_deg)
        ax.set_title(f"LG Phase (l={l}, p={p}) | z0 = {z0:.3f} m")

        # Update numbers inside each box
        for i in range(Ny):
            for j in range(Nx):
                text_grid[i][j].set_text(f"{phase_deg[i,j]:.1f}")

        return [img]

    anim = FuncAnimation(fig, update,
                         frames=len(z0_values),
                         interval=interval,
                         blit=False)

    anim.save('media/lg_sweepz0.gif', writer='pillow', fps=5)
    plt.show()
    return anim

def animate_sweep_w0(l=1, p=0, w0_values=None, z0=0.5, interval=800):

    if w0_values is None:
        w0_values = np.linspace(0.05, 0.5, 20)

    Nx, Ny = 4, 4

    x_coords = (np.arange(Nx) - (Nx-1)/2) * dx_m
    y_coords = (np.arange(Ny) - (Ny-1)/2) * dy_m

    xs, ys = np.meshgrid(x_coords, y_coords)

    fig, ax = plt.subplots()
    img = ax.imshow(np.zeros((Ny, Nx)), vmin=-180, vmax=180)

    cbar = plt.colorbar(img, ax=ax)
    cbar.set_label("Phase (degrees)")

    ax.set_xticks(range(Nx))
    ax.set_yticks(range(Ny))
    ax.set_xticklabels([f"{x:.3f}" for x in x_coords])
    ax.set_yticklabels([f"{y:.3f}" for y in y_coords])

    ax.set_xlabel("Element Position X (m)")
    ax.set_ylabel("Element Position Y (m)")

    text_grid = []
    for i in range(Ny):
        row = []
        for j in range(Nx):
            txt = ax.text(j, i, "",
                          ha='center', va='center',
                          color='white', fontsize=10)
            row.append(txt)
        text_grid.append(row)

    def update(frame):
        w0 = w0_values[frame]

        E = LGlpz(l, p, z0, w0, LAMBDA, xs, ys)
        phase_deg = np.angle(E, deg=True)
        phase_deg = (phase_deg + 180) % 360 - 180

        img.set_data(phase_deg)
        ax.set_title(f"LG Phase (l={l}, p={p}) | w0 = {w0:.3f} m")

        for i in range(Ny):
            for j in range(Nx):
                text_grid[i][j].set_text(f"{phase_deg[i,j]:.1f}")

        return [img]

    anim = FuncAnimation(fig, update,
                         frames=len(w0_values),
                         interval=interval,
                         blit=False)

    anim.save('media/lg_sweepw0.gif', writer='pillow', fps=5)
    plt.show()
    return anim
if __name__ == "__main__":

    run_z0 = True
    run_w0 = True

    if run_z0:
        animate_sweep_z0(
            l=1,
            p=0,
            z0_values=np.linspace(-1.5, 1.5, 60),
            w0=0.2,
            interval=400
        )

    if run_w0:
        animate_sweep_w0(
            l=1,
            p=0,
            w0_values=np.linspace(0.05, 0.5, 30),
            z0=0,
            interval=400
        )
