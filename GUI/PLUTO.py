import time
import adi
import numpy as np
from config import FREQ, BASE_BAND, SAMP_RATE, BUFFER_SIZE, NUM_AVG, RX_GAIN, TX_GAIN

TX_ACTIVE = False
sdr = None

# --- Connect to PlutoSDR ---
try:
    sdr = adi.Pluto("ip:192.168.2.1")
    sdr.sample_rate = int(SAMP_RATE)

    # --- TX setup ---
    sdr.tx_rf_bandwidth = int(SAMP_RATE)      # Match baseband BW
    sdr.tx_lo = int(FREQ)                     # RF carrier in Hz
    sdr.tx_hardwaregain_chan0 = TX_GAIN       # dB

    # --- RX setup ---
    sdr.rx_lo = int(FREQ)                     # RF carrier in Hz
    sdr.rx_rf_bandwidth = int(SAMP_RATE)
    sdr.gain_control_mode_chan0 = "manual"
    sdr.rx_hardwaregain_chan0 = RX_GAIN       # Adjust as needed
    sdr.rx_buffer_size = BUFFER_SIZE

except Exception as e:
    print(f"Error connecting to PLUTO: {e}")


def tx():
    '''Enable hardware DDS tone generation (0.9 scale prevents clipping)'''
    global TX_ACTIVE
    if sdr is not None:
        sdr.dds_single_tone(int(BASE_BAND), 0.9, 0)
        TX_ACTIVE = True


def stop_tx():
    '''Disable hardware DDS tone generation'''
    global TX_ACTIVE
    if TX_ACTIVE and sdr is not None:
        sdr.dds_single_tone(0, 0, 0)
        TX_ACTIVE = False


def discard_buffer():
    if sdr is not None:
        sdr.rx()


def get_dBFS():
    '''
    Finds the RMS value of the rx buffer and scales relative to full scale
    '''
    s = sdr.rx()
    rms = np.sqrt(np.mean(np.abs(s)**2))
    return 20 * np.log10(rms / 2**14)  # 12-bit signed ADC in a 16-bit container


def get_energy() -> float:
    """
    Get tone strength proportional to amplitude of dominant frequency component
    """
    power = 0.0
    for _ in range(NUM_AVG):
        rx = sdr.rx()
        power += np.mean(np.abs(rx)**2)
    power /= NUM_AVG
    return power


def get_energy_fast() -> float:
    "For receive mode: get energy without averaging"
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


# --- Example usage ---
if __name__ == "__main__":
    import matplotlib.pyplot as plt

    if sdr is not None:
        DURATION = 15  # seconds
        INTERVAL = 1   # seconds
        n_samples = DURATION / INTERVAL
        energies = []

        tx()
        # Let transmit settle
        time.sleep(0.01)

        start_time = time.time()
        for i in range(int(n_samples)):
            energy = get_energy()
            energies.append(energy)

            # Wait until next interval tick
            elapsed = time.time() - start_time
            next_tick = (i + 1) * INTERVAL
            sleep_time = next_tick - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

        stop_tx()
        sdr = None

        times = np.arange(0, DURATION, INTERVAL)
        plt.figure(figsize=(8, 5))
        plt.plot(times, energies / np.max(energies), marker='o')
        plt.xlabel('Time [s]')
        plt.ylabel('Received energy (normalized)')
        plt.title("Energy vs Time")
        plt.grid(True)
        plt.show()
