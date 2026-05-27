import os
import requests
import zipfile
import tarfile
import shutil
from tqdm import tqdm

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, 'models')
PIPER_DIR = os.path.join(MODELS_DIR, 'piper')

# URLs (Windows x64)
PIPER_URL = "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_windows_amd64.zip"
# Voice: en_US-lessac-medium (Good balance of speed/quality, female but clear. 
# For "Bro" vibe, maybe 'en_GB-alan-low' (male) or 'en_US-ryan-medium'.
# Let's go with 'en_US-ryan-medium' for a male 'Bro' voice.
VOICE_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/ryan/medium/en_US-ryan-medium.onnx"
VOICE_JSON_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/ryan/medium/en_US-ryan-medium.onnx.json"

def download_file(url, dest_path):
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    with open(dest_path, 'wb') as f, tqdm(total=total_size, unit='B', unit_scale=True, desc=os.path.basename(dest_path)) as bar:
        for data in response.iter_content(chunk_size=1024):
            f.write(data)
            bar.update(len(data))

def setup_piper():
    os.makedirs(PIPER_DIR, exist_ok=True)
    
    # 1. Download Piper Binary
    piper_zip = os.path.join(MODELS_DIR, "piper.zip")
    if not os.path.exists(os.path.join(PIPER_DIR, "piper.exe")):
        print("Downloading Piper TTS Engine...")
        download_file(PIPER_URL, piper_zip)
        print("Extracting Piper...")
        with zipfile.ZipFile(piper_zip, 'r') as zip_ref:
            zip_ref.extractall(MODELS_DIR) # Extracts to piper/
        os.remove(piper_zip)
    else:
        print("Piper already installed.")

    # 2. Download Voice Model
    voice_path = os.path.join(PIPER_DIR, "voice.onnx")
    if not os.path.exists(voice_path):
        print("Downloading Voice Model (Ryan - Medium)...")
        download_file(VOICE_URL, voice_path)
        download_file(VOICE_JSON_URL, voice_path + ".json")
    else:
        print("Voice model already exists.")

if __name__ == "__main__":
    setup_piper()
