# Exit if any command fails
$ErrorActionPreference = "Stop"

Write-Host "Creating python virtual environment '.venv'..."
python -m venv .venv

Write-Host "Upgrading pip..."
python -m pip install --upgrade pip

Write-Host "Installing required packages..."
pip install pyadi-iio pyserial numpy matplotlib nicegui pillow scipy plotly

Write-Host "Installation complete! To activate the environment in your current PowerShell session, run:"
Write-Host ".\.venv\Scripts\Activate.ps1"