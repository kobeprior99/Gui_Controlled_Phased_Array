import adi
import numpy as np
import matplotlib.pyplot as plt
import time

# ----------------------
# PARAMETERS
# ----------------------
sample_rate = 10e6  # Hz
center_freq = 2.1e9   # Hz
tx_amplitude = 0.5
tone_freq = 100e3   # baseband tone offset
fft_size = 1024
nSweep = 100

# ----------------------
# INITIALIZE SDR
# ----------------------
sdr = adi.Pluto('ip:192.168.2.1')

# ----------------------
# TX CONFIGURATION
# ----------------------
sdr.tx_lo = int(center_freq)
sdr.tx_rf_bandwidth = int(sample_rate*2)
sdr.tx_hardwaregain_chan0 = 0
sdr.tx_cyclic_buffer = True

# Generate TX tone buffer
t = np.arange(fft_size)/sample_rate
tx_buffer = (tx_amplitude * np.exp(1j*2*np.pi*tone_freq*t)).astype(np.complex64)
sdr.tx(tx_buffer)   # Start transmitting
print("Transmitting tone...")

# ----------------------
# RX CONFIGURATION (unchanged)
# ----------------------
sdr.rx_sample_rate = int(sample_rate)
sdr.rx_rf_bandwidth = int(sample_rate)
sdr.rx_lo = int(center_freq)
sdr.rx_buffer_size = fft_size
sdr.gain_control_mode_chan0 = 'manual'
sdr.rx_hardwaregain_chan0 = -40.0

# ----------------------
# FFT / SPECTRUM
# ----------------------
spectrogram = np.zeros((nSweep, fft_size))
start_time = time.time()

for i in range(nSweep):
    sample = sdr.rx()  # receive samples off Pluto

    # Your original receiver code (unchanged)
    window = np.hamming(fft_size)
    filter_sample = sample*window
    fft_sample = np.fft.fftshift(np.fft.fft(filter_sample))
    s_mag = np.abs(fft_sample) / (np.sum(window)/2)
    spectrogram[i,:] = 20*np.log10(s_mag/(2**12)) + 6.6943

end_time = time.time()
print('seconds elapsed:', end_time - start_time)

# ----------------------
# PLOT
# ----------------------
peak = np.max(np.max(spectrogram, axis=0))
plt.figure(figsize=(5, 6.5))
plt.plot(np.linspace(sample_rate/-2/1e6, sample_rate/2/1e6, spectrogram.shape[1]),
         np.max(spectrogram, axis=0))
plt.text(0, peak, str(round(peak,2))+' dBm', fontsize = 12)
plt.xlabel("Frequency [MHz]")
plt.title('Centre: 3000MHz'.ljust(40)+ "Span: 10Mhz\nRBW: 10MHz".ljust(55)+"VBW: 10MHz\nAtt:20dB".ljust(78))
plt.grid(color = "grey", linestyle = "--", linewidth = "1.4", alpha=0.4)
plt.xticks([-5,-4,-3,-2,-1,0,1,2,3,4,5])
plt.show()

# ----------------------
# STOP TX
# ----------------------
sdr.tx_destroy_buffer()
print("Done transmitting and receiving.")
