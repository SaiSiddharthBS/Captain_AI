@echo off
echo --- Captain AI V2 Setup and Launch ---

if not exist venv (
    echo Creating Python Environment...
    python -m venv venv
)
call venv\Scripts\activate

echo Installing Requirements (This might take time)...
pip install -r requirements.txt

echo Downloading AI Models (Piper, OpenWakeWord)...
python setup_v2.py

echo Starting Captain (Ghost HUD mode)...
python main_v10.py
pause
