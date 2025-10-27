import time, adi, threading
import numpy as np
from config import FREQ, BASE_BAND, SAMP_RATE,BUFFER_SIZE 

# --- Connect to PlutoSDR ---
sdr = adi.Pluto("ip:192.168.2.1")

# --- TX setup ---
sdr.tx_lo = int(FREQ)                    # RF carrier in Hz
sdr.tx_sample_rate = int(SAMP_RATE)
sdr.tx_rf_bandwidth = int(SAMP_RATE)     # match baseband BW
sdr.tx_hardwaregain_chan0 = -4          # adjust amplitude to avoid clipping
sdr.tx_cyclic_buffer = True
# --- RX setup ---
sdr.rx_lo = int(FREQ)                     # RF carrier in Hz
sdr.rx_sample_rate = int(SAMP_RATE)
sdr.rx_rf_bandwidth = int(SAMP_RATE)
sdr.gain_control_mode_chan0 = "manual"
sdr.rx_hardwaregain_chan0 = 0             # adjust as needed
sdr.rx_buffer_size = BUFFER_SIZE 

# --- Tone generator ---
#we use a cylic buffer so the duration doesn't really matter.
BURST_DURATION = 0.001 #seconds
num_samples = int(BURST_DURATION * SAMP_RATE)
TONE = 0.5 * np.exp(1j*2*np.pi*BASE_BAND*np.arange(num_samples)/SAMP_RATE)
TONE = TONE.astype(np.complex64)

def continuous_tx():
    sdr.tx(TONE)

def stop_tx():
    sdr.tx_destroy_buffer()
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
    import matplotlib.pyplot as plt
    DURATION = 15 #seconds
    INTERVAL = 1 #seconds
    n_samples = DURATION/INTERVAL
    energies =[]

    tx_thread = threading.Thread(target=continuous_tx, daemon=True)
    tx_thread.start()
    #let transmit settle
    time.sleep(0.01)
    start_time = time.time()
    for i in range(int(n_samples)):
        energy = get_energy()
        energies.append(energy)
        #wait until next seconds
        elapsed = time.time() - start_time
        next_tick = (i+1)*INTERVAL
        sleep_time = next_tick -elapsed
        if sleep_time >0:
            time.sleep(sleep_time)
    times = np.arange(0,DURATION, INTERVAL)
    plt.figure(figsize=(8,5))
    plt.plot(times,energies, marker='o')
    plt.xlabel('Time [s]')
    plt.ylabel('Received energy')
    plt.title("energy vs time")
    plt.grid(True)
    plt.show()
    sdr.tx_destroy_buffer()
    sdr= None
