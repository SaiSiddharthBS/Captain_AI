import os
import requests
import subprocess
import time
import sys
import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def install_ollama():
    url = "https://ollama.com/download/OllamaSetup.exe"
    local_filename = "OllamaSetup.exe"
    
    print(f"Downloading Ollama from {url}...")
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                total_length = r.headers.get('content-length')
                if total_length is None: # no content length header
                    f.write(r.content)
                else:
                    dl = 0
                    total_length = int(total_length)
                    for data in r.iter_content(chunk_size=4096):
                        dl += len(data)
                        f.write(data)
                        done = int(50 * dl / total_length)
                        sys.stdout.write(f"\r[{'=' * done}{' ' * (50-done)}] {dl//(1024*1024)}MB")
                        sys.stdout.flush()
                        
        print("\nDownload complete.")
        
        print("Running Silent Installer... (This may ask for UAC permission)")
        try:
            # /VERYSILENT to suppress wizard window
            # /NORESTART to prevent reboot if not needed
            cmd = f"{local_filename} /VERYSILENT /NORESTART"
            
            # Use ShellExecute to trigger UAC prompt if needed
            if not is_admin():
                 print("Requesting Admin Privileges...")
                 ctypes.windll.shell32.ShellExecuteW(None, "runas", local_filename, "/VERYSILENT /NORESTART", None, 1)
                 print("Installer launched in background. Please approve UAC.")
            else:
                 subprocess.run([local_filename, "/VERYSILENT", "/NORESTART"], check=True)
                 print("Installation completed.")
                 
        except Exception as e:
            print(f"Installer Error: {e}")
        
    except Exception as e:
        print(f"Download Error: {e}")

if __name__ == "__main__":
    install_ollama()
