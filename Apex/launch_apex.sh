#!/bin/bash
#
# APEX PRO - Quick Launch Script
# 
# This script ensures all dependencies are installed and launches the GUI
#

echo "=========================================="
echo "   APEX PRO - Audio Interface Control"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

# Check if PyQt6 is installed
echo ""
echo "Checking dependencies..."
python3 -c "import PyQt6" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "PyQt6 not found. Installing..."
    pip install PyQt6 numpy --break-system-packages
else
    echo "✓ PyQt6 installed"
fi

python3 -c "import numpy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "NumPy not found. Installing..."
    pip install numpy --break-system-packages
else
    echo "✓ NumPy installed"
fi

echo ""
echo "Launching APEX PRO..."
echo ""

# Launch the application
python3 apex_pro_gui.py

echo ""
echo "APEX PRO closed."
