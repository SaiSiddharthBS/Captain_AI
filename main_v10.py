import os
import sys
import threading
import subprocess
import pystray
from PIL import Image, ImageDraw

def create_image():
    # Create a simple icon (e.g. a blue dot or 'C')
    image = Image.new('RGB', (64, 64), color=(30, 30, 30))
    dc = ImageDraw.Draw(image)
    # Draw a cyan circle
    dc.ellipse((16, 16, 48, 48), fill=(0, 255, 255))
    return image

# Global process references
server_process = None
hud_process = None

def start_services():
    global server_process, hud_process
    
    # Ensure subprocesses know where the project root is
    project_root = os.path.abspath(os.path.dirname(__file__))
    env = os.environ.copy()
    env["PYTHONPATH"] = project_root
    
    # 1. Ensure we use the exact virtual environment Python
    venv_python = os.path.join(project_root, "venv", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        print(f"[Error] Virtual environment Python not found at: {venv_python}")
        print("Please run this from within the venv, or ensure the venv folder exists.")
        sys.exit(1)
        
    print(f"[Launcher] Using Python: {venv_python}")
    
    print("[Launcher] Starting Background Brain (server.py)...")
    server_process = subprocess.Popen(
        [venv_python, "src/server.py"], 
        cwd=project_root, 
        env=env
    )
    
    print("[Launcher] Starting Ghost HUD (hud.py)...")
    hud_process = subprocess.Popen(
        [venv_python, "src/hud.py"], 
        cwd=project_root, 
        env=env
    )

def stop_services(icon=None, item=None):
    print("[Launcher] Shutting down services...")
    if server_process:
        server_process.terminate()
    if hud_process:
        hud_process.terminate()
    if icon:
        icon.stop()

def restart_services(icon, item):
    stop_services()
    start_services()

def build_tray_menu():
    return pystray.Menu(
        pystray.MenuItem("Restart Captain", restart_services),
        pystray.MenuItem("Quit", stop_services)
    )

if __name__ == "__main__":
    print("=== Captain AI V10 (Ghost HUD) ===")
    start_services()
    
    # Initialize Tray Icon
    icon = pystray.Icon("CaptainAI", create_image(), "Captain AI", menu=build_tray_menu())
    
    # Run the tray icon (this blocks until quit is clicked)
    try:
        icon.run()
    except KeyboardInterrupt:
        stop_services()
