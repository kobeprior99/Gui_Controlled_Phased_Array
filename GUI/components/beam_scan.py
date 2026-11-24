async def run_scan(on_progress):
rx_grid, ok = await asyncio.to_thread(ensure_default_rx_lut)
if not ok:
    raise RuntimeError('MCU did not confirm LUT upload')
n = len(rx_grid)
powers = np.zeros(n)
tx()
try:
    await asyncio.sleep(1.0)
    for i in range(n):
        powers[i] = await asyncio.to_thread(_measure, i)
        on_progress(i + 1, n)
finally:
    stop_tx()
return powers
