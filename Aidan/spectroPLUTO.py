# pluto_waterfall_norm_autoscale.py
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import adi

FC_HZ   = int(2.10e9)
FS_HZ   = int(1.0e6)
NFFT    = 1024
NROWS   = 400
RXGAIN  = 0.1
RFBW_HZ = FS_HZ

sdr = adi.Pluto()
sdr.rx_lo = FC_HZ
sdr.sample_rate = FS_HZ
sdr.rx_rf_bandwidth = RFBW_HZ
sdr.rx_buffer_size = NFFT
sdr.rx_enabled_channels = [0]
sdr.gain_control_mode_chan0 = "manual"
sdr.rx_hardwaregain_chan0 = RXGAIN

window = np.hanning(NFFT).astype(np.float32)
win_pow = np.sum(window**2, dtype=np.float64)
spec = np.full((NROWS, NFFT), -120.0, dtype=np.float32)
f_khz = np.linspace(-FS_HZ/2, FS_HZ/2, NFFT, endpoint=False)/1e3

fig, ax = plt.subplots(figsize=(8,5))
im = ax.imshow(spec, origin="lower", aspect="auto",
               extent=[f_khz[0], f_khz[-1], 0, NROWS],
               cmap="viridis")
ax.set_xlabel("Frequency (kHz, relative to LO)")
ax.set_ylabel("Time (frames)")
ax.set_title("PlutoSDR Live Spectrogram (dBFS)")

def grab_frame():
    x = sdr.rx()
    if x is None or len(x) < NFFT:
        return None
    xw = x[:NFFT] * window
    Y = np.fft.fftshift(np.fft.fft(xw, NFFT))
    pxx = (np.abs(Y)**2) / (win_pow * NFFT)
    pxx_db = 10.0*np.log10(pxx + 1e-20)
    return pxx_db.astype(np.float32)

def init():
    im.set_data(spec)
    return (im,)

def update(_):
    frame = grab_frame()
    if frame is None:
        return (im,)
    global spec
    spec = np.roll(spec, -1, axis=0)
    spec[-1, :] = frame
    lo = np.percentile(spec, 10)
    hi = np.percentile(spec, 90)
    im.set_data(spec)
    im.set_clim(lo, hi)
    return (im,)

ani = animation.FuncAnimation(fig, update, init_func=init, interval=1, blit=True)
plt.tight_layout()
plt.show()
