@echo off
echo ===================================================
echo Setting up Titan Audio Stack Environment
echo ===================================================

REM Check for Conda
where conda >nul 2>nul
if %errorlevel% neq 0 (
    echo Conda is not installed or not in your PATH. 
    echo Please install Anaconda or Miniconda first.
    pause
    exit /b
)

echo Creating 'neural_audio' environment...
call conda create -n neural_audio python=3.9 -y

echo Activating environment...
call conda activate neural_audio

echo Installing PyTorch with CUDA 11.8...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

echo Installing Audio Libraries...
pip install reapy-boost
pip install demucs
pip install fairseq
pip install audiolm-pytorch
pip install transformers
pip install pedalboard
pip install scipy

echo ===================================================
echo Environment 'neural_audio' created successfully.
echo To use the scripts, make sure your Reaper python path
echo points to this environment's python.exe.
echo ===================================================
pause
