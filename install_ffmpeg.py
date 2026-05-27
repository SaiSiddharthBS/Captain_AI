import os
import requests
import zipfile
import shutil
from tqdm import tqdm

FFMPEG_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(BASE_DIR, 'tools') # Where we put it
BIN_DIR = os.path.join(BASE_DIR, 'bin') # Where we want exe files

def setup_ffmpeg():
    print("Downloading FFMPEG (Required for MP3 conversion)...")
    zip_path = os.path.join(TOOLS_DIR, "ffmpeg.zip")
    
    # Download
    response = requests.get(FFMPEG_URL, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    with open(zip_path, 'wb') as f, tqdm(total=total_size, unit='B', unit_scale=True) as bar:
        for data in response.iter_content(chunk_size=1024):
            f.write(data)
            bar.update(len(data))
            
    print("Extracting...")
    # Extract
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(TOOLS_DIR)
    
    # Move exe files to root/bin
    os.makedirs(BIN_DIR, exist_ok=True)
    
    # Find the bin folder inside the extracted structure
    # usually tools/ffmpeg-master-latest-win64-gpl/bin
    extracted_root = os.path.join(TOOLS_DIR, "ffmpeg-master-latest-win64-gpl", "bin")
    
    for file in ["ffmpeg.exe", "ffprobe.exe"]:
        src = os.path.join(extracted_root, file)
        dst = os.path.join(BIN_DIR, file)
        if os.path.exists(src):
            shutil.move(src, dst)
            print(f"Moved {file} to {BIN_DIR}")
        else:
            print(f"Warning: Could not find {file}")
            
    # Cleanup
    os.remove(zip_path)
    shutil.rmtree(os.path.join(TOOLS_DIR, "ffmpeg-master-latest-win64-gpl"), ignore_errors=True)
    print("FFMPEG Installed Successfully!")

if __name__ == "__main__":
    setup_ffmpeg()
