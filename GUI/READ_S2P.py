"""
Author: Kobe Prior
Date: Nov 12, 2025
The purpose of this file is to read s2p to be used in the main program for 
phased array calibration

format:
! Freq	S11:Re/Im(F2)	S41:Re/Im(F2)	S14:Re/Im(F2)	S44:Re/Im(F2)

Secondary Purpose: 
Generate useful plots 

"""
import os
from config import FREQ
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

S2P_DIR = Path("S2P") #directory containing port data

def read_s2p(filepath: Path):
    """
    Read S-parameter data from a .s2p file.
    Retunrs freqs s11 and s41
    """

    data = []
    with open(filepath, "r") as f:
        for line in f:
            if line.startswith("!") or line.startswith("#") or not line.strip():
                continue
            parts = line.split()
            freq = float(parts[0])
            # Columns: Freq, S11 Re/Im, S41 Re/Im, S14 Re/Im, S44 Re/Im
            s11 = complex(float(parts[1]), float(parts[2]))
            s41 = complex(float(parts[3]), float(parts[4]))
            data.append((freq, s11, s41))
    data = np.array(data, dtype=object)
    freqs = np.array([d[0] for d in data])
    s11 = np.array([d[1] for d in data])
    s41 = np.array([d[2] for d in data])
    return freqs, s11, s41


def get_phase_at_freq() -> np.ndarray:
    '''
    Direct helper function for main code.
    Get the phase at FREQ for each port and return the array of these phases (degrees).
    '''
    phases = []
    for i in range(1, 17):
        file = S2P_DIR / f"Port{i}.s2p"
        freqs, _, s41 = read_s2p(file)
        # Find the closest frequency index
        idx = np.argmin(np.abs(freqs - FREQ))
        phase_deg = np.angle(s41[idx], deg=True)
        phases.append(phase_deg)
    return np.array(phases)


# ---- For Plotting Purposes ----

def plot_S41_mag():
    '''Plot |S41| (in dB) for each port on the same graph'''
    plt.figure(figsize=(10, 6))
    for i in range(1, 17):
        file = S2P_DIR / f"Port{i}.s2p"
        freqs, _, s41 = read_s2p(file)
        mag_db = 20 * np.log10(np.abs(s41))
        plt.plot(freqs / 1e9, mag_db, label=f"Port {i}")
    plt.xlabel("Frequency (GHz)")
    plt.ylabel("|S41| (dB)")
    plt.title("S41 Magnitude (dB) for Each Port")
    plt.grid(True)
    plt.legend(ncol=4, fontsize=8)
    plt.tight_layout()
    plt.show()


def plot_S41_phase(unwrap=True):
    '''Plot the S41 phase (degrees) for each port on the same graph'''
    plt.figure(figsize=(10, 6))
    for i in range(1, 17):
        file = S2P_DIR / f"Port{i}.s2p"
        freqs, _, s41 = read_s2p(file)
        phase_deg = np.angle(s41, deg=True)
        if unwrap:
            phase_deg = np.unwrap(np.angle(s41)) * 180 / np.pi
        plt.plot(freqs / 1e9, phase_deg, label=f"Port {i}")
    plt.xlabel("Frequency (GHz)")
    plt.ylabel("Phase (degrees)")
    plt.title("S41 Phase for Each Port" + (" (Unwrapped)" if unwrap else ""))
    plt.grid(True)
    plt.legend(ncol=4, fontsize=8)
    plt.tight_layout()
    plt.show()


def plot_S11_mag():
    '''Plot |S11| (in dB) for each port on the same graph'''
    plt.figure(figsize=(10, 6))
    for i in range(1, 17):
        file = S2P_DIR / f"Port{i}.s2p"
        freqs, s11, _ = read_s2p(file)
        mag_db = 20 * np.log10(np.abs(s11))
        plt.plot(freqs / 1e9, mag_db, label=f"Port {i}")
    plt.xlabel("Frequency (GHz)")
    plt.ylabel("|S11| (dB)")
    plt.title("S11 Magnitude (dB) for Each Port")
    plt.grid(True)
    plt.legend(ncol=4, fontsize=8)
    plt.tight_layout()
    plt.show()

    
def main():
    #For testing purposes
    plot_S11_mag()
    plot_S41_mag()
    plot_S41_phase()


#if running this program directly plot S41 -> for each port
if __name__=='__main__':
    main()
