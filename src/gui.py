import customtkinter as ctk
import tkinter as tk
from threading import Thread
import time
import math
from PIL import Image, ImageTk, ImageDraw
import os
import queue

# Configuration for "Apple-style" Dark Theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

COLOR_BG = "#1c1c1e" # Apple Dark Gray
COLOR_PANEL = "#2c2c2e" # Lighter Gray
COLOR_PRIMARY = "#0a84ff" # iOS Blue
COLOR_CYAN = "#64D2FF" # iOS Cyan (Listening)
COLOR_GREEN = "#30d158" # iOS Green (Speaking/Success)
COLOR_RED = "#ff453a" # iOS Red (Error)
FONT_MAIN = ("Segoe UI", 16)
FONT_BOLD = ("Segoe UI", 16, "bold")

class StatusOrb(ctk.CTkCanvas):
    def __init__(self, master, width=200, height=200, **kwargs):
        super().__init__(master, width=width, height=height, highlightthickness=0, bg=COLOR_BG, **kwargs)
        self.width = width
        self.height = height
        self.center_x = width // 2
        self.center_y = height // 2
        self.current_color = COLOR_PRIMARY
        self.pulse_phase = 0
        self.is_animating = True
        self.mode = "IDLE" # IDLE, LISTENING, PROCESSING, SPEAKING
        self._animate()

    def set_mode(self, mode):
        self.mode = mode
        if mode == "IDLE":
            self.current_color = COLOR_PANEL
        elif mode == "LISTENING":
            self.current_color = COLOR_CYAN
        elif mode == "SPEAKING":
            self.current_color = COLOR_GREEN
        elif mode == "PROCESSING":
            self.current_color = COLOR_PRIMARY
        elif mode == "ERROR":
            self.current_color = COLOR_RED
            
    def _animate(self):
        if not self.is_animating:
            return
            
        self.delete("all")
        
        # Pulse Math
        self.pulse_phase += 0.1
        pulse = (math.sin(self.pulse_phase) + 1) / 2 # 0 to 1
        
        # Base Radius
        base_r = 60
        
        # Dynamic Radius based on mode
        if self.mode == "LISTENING":
            # Fast pulse
            r = base_r + (pulse * 10)
            outline_width = 4
        elif self.mode == "SPEAKING":
            # Sound wave simulation (random jitter)
            import random
            jitter = random.randint(-5, 5)
            r = base_r + 20 + jitter
            outline_width = 0
            self.create_oval(self.center_x - r - 10, self.center_y - r - 10,
                           self.center_x + r + 10, self.center_y + r + 10,
                           fill=self.current_color, stipple='gray50') # Fake glow
        elif self.mode == "PROCESSING":
             # Spin loading effect (Orbbiting circle)
             r = base_r
             orb_x = self.center_x + math.cos(self.pulse_phase) * (r + 20)
             orb_y = self.center_y + math.sin(self.pulse_phase) * (r + 20)
             self.create_oval(orb_x-5, orb_y-5, orb_x+5, orb_y+5, fill="white", width=0)
             outline_width = 2
        else:
            # Idle - gentle breath
            r = base_r + (pulse * 2)
            outline_width = 2
            
        # Draw Main Circle
        self.create_oval(self.center_x - r, self.center_y - r,
                         self.center_x + r, self.center_y + r,
                         fill=self.current_color, outline="", width=outline_width)
        
        self.after(20, self._animate)

class CaptainGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Thread-Safety Queue
        self.queue = queue.Queue()
        
        # Window Setup
        self.title("Captain AI")
        self.geometry("400x600")
        self.configure(fg_color=COLOR_BG)
        self.resizable(False, False)
        
        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # Log expands
        
        # 1. Header (Status Orb)
        self.orb = StatusOrb(self, width=300, height=250)
        self.orb.grid(row=0, column=0, pady=(20, 0))
        
        # 2. Text Status Label
        self.lbl_status = ctk.CTkLabel(self, text="Offline", font=FONT_BOLD, text_color="gray")
        self.lbl_status.grid(row=1, column=0, pady=(0, 20))
        
        # 3. Chat Log (Glass Panel)
        self.frame_log = ctk.CTkFrame(self, fg_color=COLOR_PANEL, corner_radius=20)
        self.frame_log.grid(row=2, column=0, sticky="nsew", padx=20, pady=20)
        self.frame_log.grid_columnconfigure(0, weight=1)
        self.frame_log.grid_rowconfigure(0, weight=1)
        
        self.txt_log = ctk.CTkTextbox(self.frame_log, font=("Consolas", 12), text_color="white", fg_color="transparent")
        self.txt_log.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.txt_log.configure(state="disabled")
        
        # 4. Input Field (for silent commands)
        self.entry_cmd = ctk.CTkEntry(self, placeholder_text="Type a command...", 
                                      fg_color=COLOR_PANEL, border_width=0, text_color="white",
                                      height=40, font=FONT_MAIN, corner_radius=20)
        self.entry_cmd.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 10))
        self.entry_cmd.bind("<Return>", self._on_enter)
        
        # 5. LLM Toggle Row (Switch + Label)
        self.frame_toggle = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_toggle.grid(row=4, column=0, sticky="ew", padx=60, pady=(0, 5))
        self.frame_toggle.grid_columnconfigure(1, weight=1)
        
        self.llm_enabled = False  # OFF by default
        self.lbl_llm = ctk.CTkLabel(self.frame_toggle, text="🧠 AI Brain", font=FONT_MAIN, text_color="gray")
        self.lbl_llm.grid(row=0, column=0, padx=(0, 10))
        self.switch_llm = ctk.CTkSwitch(self.frame_toggle, text="OFF", font=FONT_MAIN,
                                         fg_color=COLOR_PANEL, progress_color=COLOR_GREEN,
                                         command=self._on_llm_toggle)
        self.switch_llm.grid(row=0, column=1, sticky="w")
        
        # 6. Stop Button
        self.btn_stop = ctk.CTkButton(self, text="STOP", fg_color=COLOR_RED, 
                                      hover_color="#ff3b30", font=FONT_BOLD,
                                      height=40, corner_radius=20,
                                      command=self._on_stop)
        self.btn_stop.grid(row=5, column=0, sticky="ew", padx=60, pady=(0, 20))
        
        self.callback_input = None
        self.callback_stop = None
        self.callback_listen = None
        self.callback_llm_toggle = None
        
        # Bind Orb Click
        self.orb.bind("<Button-1>", self._on_orb_click)
        
        self.log("System Initialized.")
        
        # Start Queue Polling (100ms)
        self.after(100, self._check_queue)
        
    def _check_queue(self):
        """Polls queue for UI updates from other threads."""
        try:
            while True:
                # Get all messages
                msg = self.queue.get_nowait()
                type_ = msg.get("type")
                
                if type_ == "status":
                    self._safe_update_status(msg["text"], msg["mode"])
                elif type_ == "log":
                    self._safe_log(msg["text"], msg["color"])
                elif type_ == "stream":
                     self._safe_stream(msg["text"])
                    
        except queue.Empty:
            pass
        finally:
            # Reschedule check
            self.after(50, self._check_queue) # Faster polling for smoother text

    def set_callbacks(self, on_input=None, on_stop=None, on_listen=None, on_llm_toggle=None):
        self.callback_input = on_input
        self.callback_stop = on_stop
        self.callback_listen = on_listen
        self.callback_llm_toggle = on_llm_toggle
        
    def _on_llm_toggle(self):
        self.llm_enabled = self.switch_llm.get() == 1
        if self.llm_enabled:
            self.switch_llm.configure(text="ON")
            self.lbl_llm.configure(text_color=COLOR_GREEN)
            self.log("🧠 AI Brain: ENABLED")
        else:
            self.switch_llm.configure(text="OFF")
            self.lbl_llm.configure(text_color="gray")
            self.log("🧠 AI Brain: DISABLED")
        if self.callback_llm_toggle:
            self.callback_llm_toggle(self.llm_enabled)
        
    def _on_stop(self):
        if self.callback_stop:
            Thread(target=self.callback_stop).start()
            
    def _on_orb_click(self, event):
        if self.callback_listen:
             # Visual feedback
             self.update_status("Listening (Manual)...", "LISTENING")
             Thread(target=self.callback_listen).start()

    def _on_enter(self, event):
        text = self.entry_cmd.get()
        if text:
            self.entry_cmd.delete(0, "end")
            self.log(f"You: {text}", "cyan")
            if self.callback_input:
                Thread(target=self.callback_input, args=(text,)).start()

    def update_status(self, text, mode="IDLE"):
        # Put into queue
        self.queue.put({"type": "status", "text": text, "mode": mode})
        
    def log(self, text, color=None):
        # Put into queue
        self.queue.put({"type": "log", "text": text, "color": color})

    def stream(self, text):
        # Put into queue
        self.queue.put({"type": "stream", "text": text})

    def _safe_update_status(self, text, mode):
        self.lbl_status.configure(text=text)
        self.orb.set_mode(mode)
        
    def _safe_log(self, text, color=None):
        try:
            self.txt_log.configure(state="normal")
            if color == "cyan":
                text = f"\n> {text}"
            elif color == "green":
                 text = f"\nCaptain: {text}"
            else:
                 text = f"\n{text}"
                 
            self.txt_log.insert("end", text)
            self.txt_log.see("end")
            self.txt_log.configure(state="disabled")
        except Exception as e:
            pass # Avoid crash during shutdown

    def _safe_stream(self, text):
        try:
            self.txt_log.configure(state="normal")
            self.txt_log.insert("end", text)
            self.txt_log.see("end")
            self.txt_log.configure(state="disabled")
        except Exception as e:
            pass 

    def run(self):
        self.mainloop()

# Test Block
if __name__ == "__main__":
    app = CaptainGUI()
    app.update_status("Listening...", "LISTENING")
    app.run()
