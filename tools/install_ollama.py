import os
import requests
import subprocess
import sys

def install_ollama():
    url = "https://ollama.com/download/OllamaSetup.exe"
    local_filename = "OllamaSetup.exe"
    
    print(f"Downloading from {url}...")
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print("Download complete.")
        
        print("Launching Installer... Please follow the prompts.")
        # Launching installer
        subprocess.run([local_filename], check=True)
        
        print("\n--- NEXT STEP ---")
        print("1. After installation finishes, open a NEW terminal.")
        print("2. Run command: ollama pull phi3")
        print("3. Then start Captain AI.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    install_ollama()
