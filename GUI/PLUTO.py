import time, adi 
import numpy as np
from config import FREQ , BASE_BAND, SAMP_RATE,BUFFER_SIZE,NUM_AVG 

# --- connect to plutosdr ---
try:
    sdr = adi.Pluto("ip:192.168.2.1")
    sdr.sample_rate = int(SAMP_RATE)

# --- tx setup ---
    sdr.tx_rf_bandwidth = int(SAMP_RATE)     # match baseband bw
    sdr.tx_lo = int(FREQ)                    # rf carrier in hz
    sdr.tx_hardwaregain_chan0 = -40          # adjust amplitude to avoid clipping
    sdr.tx_cyclic_buffer = True

# --- rx setup ---
    sdr.rx_lo = int(FREQ)                     # rf carrier in hz
    sdr.rx_rf_bandwidth = int(SAMP_RATE)
    sdr.gain_control_mode_chan0 = "manual"
    sdr.rx_hardwaregain_chan0 = 0             # adjust as needed
    sdr.rx_buffer_size =  BUFFER_SIZE

# --- tone generator ---
    duration = 0.01
#ensure cyclic
    num_cycles = int(BASE_BAND * duration)
    num_samples = int(num_cycles * SAMP_RATE / BASE_BAND)
    TONE= np.exp(1j*2*np.pi*BASE_BAND*np.arange(num_samples)/SAMP_RATE)
    TONE *= 2**14 
except:
    print('No PLUTO attached')
def tx():
    '''Send the tone'''
    sdr.tx(TONE)

def stop_tx():
    '''stop transmitting by deleting the buffer'''
    sdr.tx_destroy_buffer()

def get_energy() -> float:
    """
    get the tones strength
    gives number proportional to the amplitude of the 
    dominant frequency component
    """
    power = 0
    for _ in range(NUM_AVG):
        rx = sdr.rx()
        power+= np.mean(np.abs(rx)**2)
    power /= NUM_AVG
    return power

# --- Example usage ---
if __name__ == "__main__":
    import matplotlib.pyplot as plt
    DURATION = 15 #seconds
    INTERVAL = 1 #seconds
    n_samples = DURATION/INTERVAL
    energies =[]
    tx()
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
    plt.plot(times,energies/np.max(energies), marker='o')
    plt.xlabel('Time [s]')
    plt.ylabel('Received energy')
    plt.title("energy vs time")
    plt.grid(True)
    plt.show()
    stop_tx()
    sdr = None
