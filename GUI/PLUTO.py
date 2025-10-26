import adi
import numpy as np
from config import FREQ, BASE_BAND, SAMP_RATE, BUFFER_SIZE
import threading

# --- Connect to PlutoSDR ---
sdr = adi.Pluto("ip:192.168.2.1")

# --- TX setup ---
sdr.tx_lo = int(FREQ)                    # RF carrier in Hz
sdr.tx_sample_rate = int(SAMP_RATE)
sdr.tx_rf_bandwidth = int(SAMP_RATE)     # match baseband BW
sdr.tx_hardwaregain_chan0 = -10          # adjust amplitude to avoid clipping
sdr.tx_cyclic_buffer = True
# --- RX setup ---
sdr.rx_lo = int(FREQ)                     # RF carrier in Hz
sdr.rx_sample_rate = int(SAMP_RATE)
sdr.rx_rf_bandwidth = int(SAMP_RATE)
sdr.rx_buffer_size = BUFFER_SIZE
sdr.gain_control_mode_chan0 = "manual"
sdr.rx_hardwaregain_chan0 = 0             # adjust as needed

# --- Tone generator ---
BURST_DURATION = 0.001 #seconds
num_samples = int(BURST_DURATION * SAMP_RATE)
TONE = 0.5 * np.exp(1j*2*np.pi*BASE_BAND*np.arange(num_samples)/SAMP_RATE)
TONE = TONE.astype(np.complex64)

def continuous_tx():
    sdr.tx(TONE)

# --- Send burst and measure energy ---
def get_energy() -> float:
    """
    Transmit BASE_BAND tone burst and return received energy.
    """
    # Receive
    rx_data = sdr.rx()
    
    # Compute energy
    energy = np.sum(np.abs(rx_data)**2)
    
    return energy

# --- Example usage ---
if __name__ == "__main__":
    tx_thread = threading.Thread(target=continuous_tx, daemon=True)
    tx_thread.start()
    energy = get_energy()
    print(f'Received energy: {energy:.2f}')
