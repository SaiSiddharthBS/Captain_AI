from src.brain import Brain
from src.stt import EarEngine
import threading
import time
import sys

from src.gui import CaptainGUI

class TextRedirector:
    def __init__(self, widget):
        self.widget = widget
        self.buffer = ""

    def write(self, str):
        # We need to filter ANSI codes if we want clean text
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        clean_text = ansi_escape.sub('', str)
        
        if clean_text:
             # Check if text implies state change
             if "Listening" in clean_text:
                 self.widget.update_status("Listening...", "LISTENING")
             elif "Processing" in clean_text:
                 self.widget.update_status("Processing...", "PROCESSING")
             elif "User:" in clean_text:
                 self.widget.update_status("Processing...", "PROCESSING")
             elif "Captain:" in clean_text:
                 self.widget.update_status("Speaking...", "SPEAKING")
             
             # Routing Logic
             # If it ends with \n, it's a log line.
             if clean_text.endswith("\n"):
                 self.widget.log(clean_text.strip())
             else:
                 # It's a stream chunk (e.g. from LLM)
                 self.widget.stream(clean_text)

    def flush(self):
        pass

def main():
    # 1. Init GUI
    app = CaptainGUI()
    
    # 2. Redirect Stdout
    sys.stdout = TextRedirector(app)
    print("--- Captain AI V7 (GUI Mode) ---")
    
    # 3. Init Brain & Ear (Background)
    # Important: Init Pygame Mixer in Main Thread BEFORE threading?
    # Brain/TTS/Music do this on init.
    
    def background_loader():
        brain = Brain()
        ear = EarEngine(brain=brain)
        
        # Link GUI input callback
        # on_input: Text command
        # on_stop: Stop button
        # on_listen: Remote listen trigger (Orb click)
        app.set_callbacks(
            on_input=lambda text: brain.process_input(text),
            on_stop=lambda: brain.stop_all(),
            on_listen=lambda: ear.listen_once(),
            on_llm_toggle=lambda enabled: setattr(brain, 'llm_enabled', enabled)
        )
        
        brain.voice.speak("System online.")
        
        if ear.ww_model:
            ear.listen_loop() # This is blocking, so run in this thread
        else:
            print("Wake Word Error.")
            
    # Launch Logic Thread
    t = threading.Thread(target=background_loader, daemon=True)
    t.start()
    
    # 4. Run GUI (Main Thread Blocking)
    try:
        app.run()
    except Exception as e:
        sys.__stdout__.write(f"GUI Crash: {e}\n")
        input("Press Enter to exit...")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.__stdout__.write(f"Fatal Error: {e}\n")
        import traceback
        traceback.print_exc(file=sys.__stdout__)
        input("Press Enter to exit...")
