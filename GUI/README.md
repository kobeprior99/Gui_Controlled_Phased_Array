# Simulation and Experimental Investigation of Structured Wave Scattering Using a Custom Phased Array System

This software repository contains the graphical user interface (GUI) and control software for my Master's Thesis: **SIMULATION AND EXPERIMENTAL INVESTIGATION OF STRUCTURED WAVE SCATTERING USING A CUSTOM PHASED ARRAY SYSTEM**.

## Project Overview
This program is designed to interface directly with a custom-built phase-shifting network, a STM32 microcontroller, and a Analog Devices ADALM PLUTO Software Defined Radio

By utilizing this interface, users can dynamically generate both **structured** (e.g., orbital angular momentum, vortex beams, or customized phase fronts) and **non-structured** steered planewaves. These waveforms are transmitted and received to systematically investigate electromagnetic wave scattering phenomena

### Key Features

* **Microcontroller Interface:** Low-level serial communication (`pyserial`) with the microcontroller.

* **SDR Integration:** High-speed IQ data streaming and hardware configuration using the Analog Devices `pyadi-iio` library.
* **Interactive GUI:** Built with `nicegui` for real-time plotting (via `plotly` and `matplotlib`)

* **Array Simulation:** In-GUI mathematical modeling (`numpy`, `scipy`) of array factor patterns, and brute force direction finding  

---

## Installation & Environment Setup

To run the GUI and the hardware interfaces, you must set up a Python virtual environment and install the required dependencies. Setup scripts are provided for both Unix-like platforms (macOS/Linux) and Windows.

The environment requires Python 3.8+ and installs the following core packages:
* `pyadi-iio` (SDR interfacing)
* `pyserial` (Microcontroller communication)
* `numpy` & `scipy` (Signal processing and array math)
* `matplotlib` & `plotly` (Static and interactive plotting)
* `nicegui` (Web-based local GUI framework)
* `pillow` (Image processing and visualization utilities)

### 1. macOS / Linux Setup
On macOS and Linux, use the shell script `get_requirements.sh` to automatically create a virtual environment, activate it, and install all libraries.

1. Open your terminal in the project directory.
2. Ensure the script is executable:
   ```bash
   chmod +x get_requirements.sh
   ```
3. Run the script:
   ```bash
   ./get_requirements.sh
   ```
4. Once completed, activate the virtual environment in your active terminal session:
   ```bash
   source .venv/bin/activate
   ```

### 2. Windows Setup (PowerShell)
On Windows, you can use the provided PowerShell script `get_requirements.ps1` to automate the setup process.

1. Open PowerShell in the project directory.
2. (Optional) If your execution policy restricts running scripts, you may need to temporarily bypass it for this session:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
   ```
3. Run the script:
   ```powershell
   .\get_requirements.ps1
   ```
4. Once completed, activate the environment in your active PowerShell window:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

---

## Running the Application
Once the virtual environment is active and all requirements are installed, launch the GUI page by running the main Python script:

```bash
python main.py
```
*(Note: Replace `main.py` with the actual filename of your entry script if named differently, e.g., `gui.py`)*

After launching, your default web browser should automatically open to `http://localhost:8080` (or the port specified by NiceGUI) displaying the control interface.
