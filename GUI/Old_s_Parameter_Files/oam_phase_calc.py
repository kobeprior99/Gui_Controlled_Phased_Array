
from config import dx_m, dy_m
import numpy as np

def calculate_array_geometry(Nx, Ny, dx, dy):
    """
    Calculates positions and spherical angles for a centered rectangular array.
    """
    elements = []
    
    # Calculate the offset to center the array at (0,0)
    x_offset = (Nx - 1) / 2.0
    y_offset = (Ny - 1) / 2.0
    
    print(f"{'Index (m,n)':<12} | {'X Pos':<8} | {'Y Pos':<8} | {'Azimuth (phi)':<15}")
    print("-" * 55)

    for m in range(Nx):
        for n in range(Ny):
            # Calculate Cartesian coordinates
            x = (m - x_offset) * dx
            y = (n - y_offset) * dy
            
            # Calculate Azimuthal angle (phi) in degrees
            # Note: np.arctan2(y, x) returns angle from positive X axis
            phi = np.degrees(np.arctan2(y, x))
            
            elements.append(((m, n), x, y, phi))
            print(f"({m}, {n})        | {x:8.2f} | {y:8.2f} | {phi:8.2f}°")
            
    return elements

# Configuration: 4x4 array (16 elements)
Nx, Ny = 4, 4
dx, dy = 0.5, 0.5  # Example spacing (e.g., half-wavelength)

calculate_array_geometry(4, 4, dx_m, dy_m)
