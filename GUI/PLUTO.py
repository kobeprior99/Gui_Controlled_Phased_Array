'''
PLUTO.py

Interface layer for PLUTO SDR: connection and setup, TX tone generation, 
RX gain control, and receive power

Power measurements
------------------
Two kinds of power are available, and they are not interchangeable:

  TONE power  (get_dBFS)
      Power of the transmitted DDS tone only, measured at BASE_BAND with a
      Hann-windowed single-bin DFT:
          A     = sum(s * w * exp(-j*2*pi*BASE_BAND/SAMP_RATE * n)) / sum(w)
          power = |A|^2
      The window and reference are precomputed in config.py (TONE_WREF, TONE_WSUM).
      Noise, LO leakage, spurs, and interference outside the tone's DFT bin are
      rejected, so this is the right measurement for a stationary scatterer or an
      array scan where the received signal sits at the transmitted frequency.
      Note it measures the coherent sum of everything arriving at BASE_BAND
      (direct coupling + clutter + scatterer), not the scattered field alone.

  TOTAL power  (get_total_dBFS, get_energy, the self-test)
      Mean power over the whole capture bandwidth: mean(|s|^2) = mean(I^2 + Q^2).
      Includes noise and anything else the ADC sees. Use it to check ADC
      loading and clipping, and for the AGC self-test (the AGC regulates total
      level, so its -12 dBFS target only makes sense against total power).
      get_energy() still uses total power.

dBFS convention
---------------
    dBFS = 10 * log10(power / FULL_SCALE^2)
FULL_SCALE is the ADC amplitude (2**11 for the Pluto's 12-bit signed samples),
not the power, because it is squared here. A full-scale complex sample (I and Q
both at +/-FULL_SCALE) reads +3 dBFS under this definition, since I^2 + Q^2 = 2 * FS^2.
For a clean tone at BASE_BAND, tone power and total power agree, so this
convention is the same for both. Tone dBFS is always <= total dBFS; a large gap
means noise, interference, or clipping is contributing to the total.

Self-test (python pluto_sdr.py)
-------------------------------
Enables AGC (slow_attack), transmits the DDS tone, waits for the loop to settle,
then logs N_BUFFERS RX buffers. Prints the mean/std dBFS (total power), offset from
the -12 dBFS AGC target, AGC-selected RX gain, and peak sample value (to detect
clipping), then plots dBFS and RX gain versus buffer index. TX is muted and RX gain
restored to manual on exit.

Author: Kobe Prior
Last Modified: November 19 2026
'''
import time
import adi
import numpy as np
from config import (FREQ, BASE_BAND, SAMP_RATE, BUFFER_SIZE, RX_GAIN,
                    TX_GAIN, FULL_SCALE, TONE_WREF, TONE_WSUM)

TX_ACTIVE = False
sdr = None

# --- Connect to PlutoSDR ---
try:
    sdr = adi.Pluto("ip:192.168.2.1")

    # Mute TX hardware gain on startup to prevent calibration RF bursts
    sdr.tx_hardwaregain_chan0 = -80.0

    # Force DDS tone scales to 0 immediately upon startup
    sdr.dds_single_tone(0, 0, 0)

    # --- TX setup ---
    sdr.sample_rate = int(SAMP_RATE)
    sdr.tx_rf_bandwidth = int(SAMP_RATE)
    sdr.tx_lo = int(FREQ)

    # --- RX setup ---
    sdr.rx_lo = int(FREQ)
    sdr.rx_rf_bandwidth = int(SAMP_RATE)
    sdr.gain_control_mode_chan0 = "manual"
    sdr.rx_hardwaregain_chan0 = float(RX_GAIN)
    sdr.rx_buffer_size = BUFFER_SIZE

except Exception as e:
    print(f"Error connecting to PLUTO: {e}")


def set_gain(rx_gain: float = None, tx_gain: float = None):
    """
    Update RX and/or TX hardware gain settings on the SDR.
    """
    global sdr, TX_GAIN
    if sdr is None:
        print("SDR instance is not connected.")
        return

    if rx_gain is not None:
        sdr.gain_control_mode_chan0 = "manual"
        sdr.rx_hardwaregain_chan0 = float(rx_gain)

    if tx_gain is not None:
        TX_GAIN = float(tx_gain)
        # Only apply live to hardware if transmission is active
        if TX_ACTIVE:
            sdr.tx_hardwaregain_chan0 = TX_GAIN


def tx():
    '''Enable hardware DDS tone generation and restore TX gain'''
    global TX_ACTIVE, TX_GAIN
    if sdr is not None:
        sdr.tx_hardwaregain_chan0 = float(TX_GAIN)
        sdr.dds_single_tone(int(BASE_BAND), 0.9, 0)
        TX_ACTIVE = True


def stop_tx():
    '''Disable hardware DDS tone generation and mute carrier feedthrough'''
    global TX_ACTIVE
    if sdr is not None:
        sdr.dds_single_tone(0, 0, 0)
        sdr.tx_hardwaregain_chan0 = -80.0  # Drop LO leakage into noise floor
        TX_ACTIVE = False


def discard_buffer():
    if sdr is not None:
        sdr.rx()


def power_to_dBFS(power: float) -> float:
    '''Convert mean power (mean of |s|^2) to dBFS relative to FULL_SCALE'''
    return 10 * np.log10(power / FULL_SCALE**2 + 1e-20)


def tone_power(s: np.ndarray) -> float:
    '''
    Power of the tone at BASE_BAND in one rx buffer (windowed single-bin DFT).
    Same units as mean(|s|^2); equals it for a pure tone at BASE_BAND.
    '''
    A = np.dot(s, TONE_WREF) / TONE_WSUM
    return float(np.abs(A) ** 2)

def get_tone_energy(n_avg: int = 1) -> float:
    return float(np.mean([tone_power(sdr.rx()) for _ in range(n_avg)]))

def get_dBFS():
    '''
    Tone power at BASE_BAND of one rx buffer, relative to full scale.
    Rejects noise and out-of-bin signals; see "Power measurements" in the header.
    '''
    s = sdr.rx()
    return power_to_dBFS(tone_power(s))


def get_total_dBFS():
    '''
    Total power of one rx buffer (mean of I^2 + Q^2) relative to full scale.
    Use for ADC loading / AGC checks, not for tone measurements.
    '''
    s = sdr.rx()
    return power_to_dBFS(np.mean(np.abs(s)**2))


def get_energy() -> float:
    "For receive mode: get energy without averaging (total power)"
    rx = sdr.rx()
    return float(np.mean(np.abs(rx)**2))


def get_mean_dev():
    rx = sdr.rx()
    avg_power = np.mean(np.abs(rx)**2)
    std_power = np.std(np.abs(rx)**2)
    return (avg_power, std_power)


def moving_average(x, window=8):
    x = np.asarray(x)
    return np.convolve(x, np.ones(window) / window, mode='valid')


# --- Test notion of dBFS: with AGC on we should see about -12 dBFS (total power) ---
if __name__ == "__main__":
    import matplotlib.pyplot as plt

    N_BUFFERS = 200          # number of rx buffers to log
    SETTLE_S = 1.0           # wait after enabling TX + AGC
    AGC_TARGET_DBFS = -12.0

    if sdr is None:
        raise SystemExit("SDR not connected.")

    try:
        # AGC on (slow_attack is the usual choice for a continuous tone)
        sdr.gain_control_mode_chan0 = "slow_attack"

        # Transmit and give the AGC time to converge
        tx()
        time.sleep(SETTLE_S)
        for _ in range(10):      # flush stale buffers captured before AGC settled
            discard_buffer()

        levels, gains, peaks = [], [], []
        for _ in range(N_BUFFERS):
            s = sdr.rx()
            levels.append(power_to_dBFS(np.mean(np.abs(s) ** 2)))  # total power: the AGC regulates this
            peaks.append(max(np.max(np.abs(s.real)), np.max(np.abs(s.imag))))
            gains.append(sdr.rx_hardwaregain_chan0)  # gain chosen by the AGC


    finally:
        stop_tx()
        sdr.gain_control_mode_chan0 = "manual"
        sdr.rx_hardwaregain_chan0 = float(RX_GAIN)

    levels, gains, peaks = np.array(levels), np.array(gains), np.array(peaks)

    print(f"Mean dBFS: {levels.mean():.2f}  (std {levels.std():.2f})")
    print(f"Offset from {AGC_TARGET_DBFS:.0f} dBFS target: {levels.mean() - AGC_TARGET_DBFS:+.2f} dB")
    print(f"AGC gain: {gains.mean():.1f} dB (min {gains.min():.1f}, max {gains.max():.1f})")
    print(f"Peak |I| or |Q|: {peaks.max():.0f} of {FULL_SCALE - 1} (near full scale means clipping)")

    # --- Plot ---
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(levels, label="Measured dBFS")
    ax1.axhline(AGC_TARGET_DBFS, color="k", linestyle="--", label="AGC target (-12 dBFS)")
    ax1.set_xlabel("Buffer index")
    ax1.set_ylabel("dBFS")
    ax1.grid(True)

    ax2 = ax1.twinx()
    ax2.plot(gains, color="tab:red", alpha=0.5, label="AGC RX gain (dB)")
    ax2.set_ylabel("RX hardware gain (dB)")

    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="best")
    plt.title("Pluto AGC: measured dBFS and AGC-selected gain")
    plt.tight_layout()
    plt.show()
    del sdr
