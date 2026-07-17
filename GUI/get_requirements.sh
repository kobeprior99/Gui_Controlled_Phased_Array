#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Creating python virtual environment '.venv'..."
python3 -m venv .venv

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing required packages..."
pip install pyadi-iio pyserial numpy matplotlib nicegui pillow scipy plotly 

echo "Installation complete! To activate the environment in your current shell, run:"
echo "source .venv/bin/activate"
