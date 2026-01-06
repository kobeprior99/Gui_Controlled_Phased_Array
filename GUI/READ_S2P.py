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
from config import FREQ, S2PDIR
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# change directory of s2p files here
s2p_dir = Path(S2PDIR) #directory containing port data
# Cycle through multiple line styles
LINE_STYLE = ['-']

# Font sizes
TITLE_SIZE = 18
LABEL_SIZE = 16
TICK_SIZE = 14
LEGEND_SIZE = 12

def read_s2p(filepath: Path):
    """
    Read S-parameter data from a .s2p file.
    Returns freqs, s11, s41, s44
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
            s44 = complex(float(parts[7]), float(parts[8]))
            data.append((freq, s11, s41, s44))
    data = np.array(data, dtype=object)
    freqs = np.array([d[0] for d in data])
    s11 = np.array([d[1] for d in data])
    s41 = np.array([d[2] for d in data])
    s44 = np.array([d[3] for d in data])
    return freqs, s11, s41, s44


def get_phase_at_freq() -> np.ndarray:
    '''
    Direct helper function for main code.
    Get the phase at FREQ for each port and return the array of these phases (degrees).
    '''
    phases = []
    for i in range(1, 17):
        file = s2p_dir / f"Port{i}.s2p"
        freqs, _, s41, _ = read_s2p(file)
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
        file = s2p_dir / f"Port{i}.s2p"
        freqs, _, s41, _ = read_s2p(file)
        mag_db = 20 * np.log10(np.abs(s41))
        #pick linestyle based on index
        ls = LINE_STYLE[(i-1) % len(LINE_STYLE)]
        plt.plot(freqs / 1e9, mag_db, linestyle=ls, label=f"Port {i}")
    plt.xlabel("Frequency (GHz)", fontsize=LABEL_SIZE)
    plt.ylabel("|S21| (dB)", fontsize=LABEL_SIZE)
    plt.title("S21 Magnitude (dB) for Each Port", fontsize=TITLE_SIZE)
    plt.tick_params(axis='both', which='major', labelsize=TICK_SIZE)
    plt.grid(True)
    plt.legend(ncol=4, fontsize=LEGEND_SIZE)
    plt.tight_layout()
    plt.show()


def plot_S41_phase(unwrap=True, interactive=False):
    '''Plot the S41 phase (degrees) for each port on the same graph'''
    lines = [] #store line handles 
    labels = [] #store label strings
    plt.figure(figsize=(10, 6))

    for i in range(1, 17):
        file = s2p_dir / f"Port{i}.s2p"
        freqs, _, s41, _ = read_s2p(file)
        phase_deg = np.angle(s41, deg=True)
        if unwrap:
            phase_deg = np.unwrap(np.angle(s41)) * 180 / np.pi
        line, = plt.plot(freqs / 1e9, phase_deg, label=f"Port {i}")
        lines.append(line)
        labels.append(f"Port {i}")
    plt.xlabel("Frequency (GHz)", fontsize=LABEL_SIZE)
    plt.ylabel("Phase (degrees)", fontsize=LABEL_SIZE)
    plt.title("S21 Phase for Each Port" + (" (Unwrapped)" if unwrap else ""), fontsize=TITLE_SIZE)
    plt.tick_params(axis='both', which='major', labelsize=TICK_SIZE)
    plt.grid(True)
    leg = plt.legend(ncol=4, fontsize=LEGEND_SIZE, fancybox=True, shadow=False)
    plt.tight_layout()
    if interactive:
        # --- Create legend with picking enabled ---
        leg = plt.legend(ncol=4, fontsize=LEGEND_SIZE, fancybox=True, shadow=False)
        for legend_line in leg.get_lines():
            legend_line.set_picker(True)        # make clickable
            legend_line.set_pickradius(5)

        # --- Click event handler ---
        def on_pick(event):
            legend_line = event.artist
            label = legend_line.get_label()

            # Find which port index
            index = labels.index(label)

            # Highlight selected, dim others
            for idx, line in enumerate(lines):
                if idx == index:
                    line.set_linewidth(3.0)
                    line.set_alpha(1.0)
                    line.set_zorder(3)
                else:
                    line.set_linewidth(1.0)
                    line.set_alpha(0.25)
                    line.set_zorder(1)

            plt.draw()

        # Connect event
        plt.gcf().canvas.mpl_connect('pick_event', on_pick)
    plt.show()


def plot_S11_mag():
    '''Plot |S11| (in dB) for each port on the same graph'''
    plt.figure(figsize=(10, 6))
    for i in range(1, 17):
        file = s2p_dir / f"Port{i}.s2p"
        freqs, s11, _, _ = read_s2p(file)
        mag_db = 20 * np.log10(np.abs(s11))
        plt.plot(freqs / 1e9, mag_db, label=f"Port {i}")
    plt.xlabel("Frequency (GHz)", fontsize=LABEL_SIZE)
    plt.ylabel("|S11| (dB)", fontsize=LABEL_SIZE)
    plt.title("S11 Magnitude (dB) for Each Port", fontsize=TITLE_SIZE)
    plt.tick_params(axis='both', which='major', labelsize=TICK_SIZE)
    plt.grid(True)
    plt.legend(ncol=4, fontsize=LEGEND_SIZE)
    plt.tight_layout()
    plt.show()


def plot_S44_mag():
    '''Plot |S44| (in dB) for each port on the same graph'''
    plt.figure(figsize=(10, 6))
    for i in range(1, 17):
        file = s2p_dir / f"Port{i}.s2p"
        freqs, _, _, s44 = read_s2p(file)
        mag_db = 20 * np.log10(np.abs(s44))
        plt.plot(freqs / 1e9, mag_db, label=f"Port {i}")
    plt.xlabel("Frequency (GHz)", fontsize=LABEL_SIZE)
    plt.ylabel("|S22| (dB)", fontsize=LABEL_SIZE)
    plt.title("S22 Magnitude (dB) for Each Port", fontsize=TITLE_SIZE)
    plt.tick_params(axis='both', which='major', labelsize=TICK_SIZE)
    plt.grid(True)
    plt.legend(ncol=4, fontsize=LEGEND_SIZE)
    plt.tight_layout()
    plt.show()


def plot_relative_phase(unwrap=True, interactive=False):
    """Plot S41 phase relative to the channel with most negative phase at FREQ."""
    phases = []
    freqs_ref = None
    # --- Load all phases first ---
    for i in range(1, 17):
        file = s2p_dir / f"Port{i}.s2p"
        freqs, _, s41, _ = read_s2p(file)
        if freqs_ref is None:
            freqs_ref = freqs  # ensure consistent frequency axis
        phase = np.angle(s41, deg=False)  # radians
        if unwrap:
            phase = np.unwrap(phase)
        phase_deg = np.rad2deg(phase)
        phases.append(phase_deg)
    phases = np.array(phases)  # shape (16, Nfreq)
    
    # --- Find index closest to FREQ ---
    freq_idx = np.argmin(np.abs(freqs_ref - FREQ))
    actual_freq = freqs_ref[freq_idx]
    print(f"Reference frequency: {actual_freq/1e9:.6f} GHz (target: {FREQ/1e9:.6f} GHz)")
    
    # --- Identify reference port: most negative phase at FREQ ---
    phases_at_freq = phases[:, freq_idx]
    ref_index = np.argmin(phases_at_freq)   # port with minimal phase at FREQ
    ref_phase = phases[ref_index]
    print(f"Reference port = Port {ref_index+1} (phase at FREQ: {phases_at_freq[ref_index]:.2f}°)")
    
    # --- Compute relative phases ---
    rel_phases = phases - ref_phase  # broadcast subtract
    
    # --- Plot ---
    plt.figure(figsize=(10, 6))
    lines = []
    labels = []
    for i in range(16):
        line, = plt.plot(freqs_ref / 1e9,
                         rel_phases[i],
                         label=f"Port {i+1}")
        lines.append(line)
        labels.append(f"Port {i+1}")
    
    # Add vertical line at reference frequency
    plt.axvline(actual_freq / 1e9, color='k', linestyle='--', alpha=0.3, label=f'Ref Freq ({actual_freq/1e9:.3f} GHz)')
    
    plt.xlabel("Frequency (GHz)", fontsize=LABEL_SIZE)
    plt.ylabel("Relative Phase (degrees)", fontsize=LABEL_SIZE)
    plt.title("Relative S21 Phase (Referenced to Longest Path at FREQ)", fontsize=TITLE_SIZE)
    plt.tick_params(axis='both', which='major', labelsize=TICK_SIZE)
    plt.grid(True)
    leg = plt.legend(ncol=4, fontsize=LEGEND_SIZE, fancybox=True)
    plt.tight_layout()
    if interactive:
        # enable clickable legend
        leg = plt.legend(ncol=4, fontsize=LEGEND_SIZE, fancybox=True)
        for lg in leg.get_lines():
            lg.set_picker(True)
            lg.set_pickradius(5)
        def on_pick(event):
            lg_line = event.artist
            label = lg_line.get_label()
            if label.startswith('Ref Freq'):
                return  # ignore clicking on reference freq line
            idx = labels.index(label)
            # Highlight selected
            for j, line in enumerate(lines):
                if j == idx:
                    line.set_linewidth(3)
                    line.set_alpha(1.0)
                    line.set_zorder(3)
                else:
                    line.set_linewidth(1)
                    line.set_alpha(0.25)
                    line.set_zorder(1)
            plt.draw()
        plt.gcf().canvas.mpl_connect("pick_event", on_pick)
    plt.show()

def main():
    # For testing purposes
    plot_S11_mag()
    plot_S41_mag()
    plot_S44_mag()
    plot_S41_phase(unwrap=True, interactive=True)
    plot_relative_phase()

if __name__ == '__main__':
    main()
