@echo off
call venv\Scripts\activate
echo Installing Downloader Dependencies...
pip install --upgrade yt-dlp
echo.
if not exist bin\ffmpeg.exe (
    echo FFMPEG missing. Downloading...
    python install_ffmpeg.py
)
python tools/downloader.py
pause
