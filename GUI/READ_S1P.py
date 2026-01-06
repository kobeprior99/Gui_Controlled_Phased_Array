""" 
Author: Kobe Prior
Date: Dec 1, 2025
The purpose of this file is to read s1p to be used in the main program for phased array calibration
format: ! Freq S11:Re/Im(F2)
Secondary Purpose: Generate useful plots
"""
import os
from config import FREQ
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# for 2x2 array
def plot_s1p_2x2():
    """
    Read S-parameter data from a .s1p file.
    Returns freqs, s11
    Also plots |S11| in dB.
    """
    data = []
    with open('2x2_measured.s1p', "r") as f:
        for line in f:
            # Skip comments and option lines
            if line.startswith("!") or line.startswith("#") or not line.strip():
                continue
            parts = line.split()
            # Expected format (RI): freq Re(S11) Im(S11)
            freq = float(parts[0])
            s11 = complex(float(parts[1]), float(parts[2]))
            data.append((freq, s11))
    
    # Convert to arrays
    data = np.array(data, dtype=object)
    freqs = np.array([d[0] for d in data])
    s11 = np.array([d[1] for d in data])
    
    # Convert S11 to dB
    s11_db = 20 * np.log10(np.abs(s11))
    
    # Plot with larger font sizes
    plt.figure(figsize=(8, 5))
    plt.plot(freqs, s11_db)
    plt.xlabel("Frequency", fontsize=16)
    plt.ylabel("|S11| (dB)", fontsize=16)
    plt.title("S11 vs Frequency", fontsize=18)
    plt.tick_params(axis='both', which='major', labelsize=14)
    plt.grid(True)
    plt.tight_layout()
    plt.show()
    
    return freqs, s11

def read_s1p(filepath: Path):
    """
    Read S-parameter data from a .s1p file.
    Returns freqs (array), s11 (complex array)
    """
    data = []
    with open(filepath, "r") as f:
        for line in f:
            if line.startswith("!") or line.startswith("#") or not line.strip():
                continue
            parts = line.split()
            freq = float(parts[0])
            s11 = complex(float(parts[1]), float(parts[2]))
            data.append((freq, s11))
    
    data = np.array(data, dtype=object)
    freqs = np.array([d[0] for d in data])
    s11 = np.array([d[1] for d in data])
    
    return freqs, s11

def plot_s1p_4x4():
    """
    Reads element1.s1p ... element16.s1p from directory and plots |S11| dB for all on the same plot.
    """
    plt.figure(figsize=(10, 6))
    
    for i in range(1, 17):
        filepath = Path("S1P_4x4") / f"element{i}.s1p"
        freqs, s11 = read_s1p(filepath)
        s11_db = 20 * np.log10(np.abs(s11))
        plt.plot(freqs, s11_db, label=f"Element {i}")
    
    plt.xlabel("Frequency", fontsize=16)
    plt.ylabel("|S11| (dB)", fontsize=16)
    plt.title("S11 for All 16 Elements", fontsize=18)
    plt.tick_params(axis='both', which='major', labelsize=14)
    plt.grid(True)
    plt.legend(ncol=4, fontsize=10)
    plt.tight_layout()
    plt.show()

if __name__ =='__main__':
    plot_s1p_2x2()
    plot_s1p_4x4()
