from scipy.special import genlaguerre
from math import factorial
def LGlpz(l,p,z0,w0,lambda0,xs,ys):
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
