import os
import random
import pygame
from src.config import MEDIA_DIR

class MusicEngine:
    def __init__(self):
        # Mixer init handled in TTS/Brain usually, but safe to call multiple times
        if not pygame.get_init():
             pygame.init()
        if not pygame.mixer.get_init():
             pygame.mixer.init()
             
        self.current_folder = None
        self.is_playing = False
        self.is_paused = False
        self.playlist = []
        self.current_index = 0
        
        # Start continuous watcher thread
        import threading
        self.watcher_thread = threading.Thread(target=self._music_watcher, daemon=True)
        self.watcher_thread.start()

    def _music_watcher(self):
        import time
        while True:
            time.sleep(1)
            # get_busy() is false if playback stops naturally (or if paused manually)
            # We track is_paused to prevent skipping when explicitly paused
            if self.is_playing and not self.is_paused and not pygame.mixer.music.get_busy():
                # Song finished naturally
                self.next_song()

    def load_folder(self, folder_name):
        target_path = os.path.join(MEDIA_DIR, folder_name)
        if not os.path.exists(target_path):
            # Fallback check
            return False
            
        formats = ('.mp3', '.wav', '.ogg')
        self.playlist = [
            os.path.join(target_path, f) 
            for f in os.listdir(target_path) 
            if f.lower().endswith(formats)
        ]
        
        if not self.playlist:
            return False
            
        random.shuffle(self.playlist)
        self.current_index = 0
        self.current_folder = folder_name
        return True

    def play(self):
        if not self.playlist:
            return "Queue empty."
        try:
            pygame.mixer.music.load(self.playlist[self.current_index])
            pygame.mixer.music.play()
            self.is_playing = True
            self.is_paused = False
            return "Playing."
        except Exception as e:
            print(f"Music Error: {e}")
            return "Error playing."

    def next_song(self):
        """Advances to the next song in the queue and plays it."""
        if not self.playlist:
            return
        self.current_index = (self.current_index + 1) % len(self.playlist)
        self.play()

    def stop(self):
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        
    def pause(self):
        pygame.mixer.music.pause()
        self.is_paused = True

    def list_folders(self):
        if not os.path.exists(MEDIA_DIR):
            return []
        return [d for d in os.listdir(MEDIA_DIR) if os.path.isdir(os.path.join(MEDIA_DIR, d))]

    def set_volume(self, val):
        """Sets volume (0.0 to 1.0)"""
        if 0.0 <= val <= 1.0:
            pygame.mixer.music.set_volume(val)
            return True
        return False
        
    def get_volume(self):
        return pygame.mixer.music.get_volume()
        
    def step_volume(self, delta):
        """Changes volume by delta (e.g. +0.1 or -0.1)"""
        current = self.get_volume()
        new_val = max(0.0, min(1.0, current + delta))
        self.set_volume(new_val)
        return new_val

    def fade_out(self, duration=0.5, target=0.2):
        """Linearly fades volume down to target over duration seconds."""
        if not self.is_playing:
            return
            
        start_vol = self.get_volume()
        steps = 10
        step_delay = (duration * 1000) / steps
        vol_step = (start_vol - target) / steps
        
        for i in range(steps):
             new_vol = start_vol - (vol_step * (i + 1))
             if new_vol < target: new_vol = target
             self.set_volume(new_vol)
             pygame.time.wait(int(step_delay))
        
        self.set_volume(target)

    def fade_in(self, duration=0.5, target=1.0):
        """Linearly fades volume up to target over duration seconds."""
        if not self.is_playing:
             self.set_volume(target) # Just restore level
             return
             
        start_vol = self.get_volume()
        steps = 10
        step_delay = (duration * 1000) / steps
        vol_step = (target - start_vol) / steps
        
        for i in range(steps):
             new_vol = start_vol + (vol_step * (i + 1))
             if new_vol > target: new_vol = target
             self.set_volume(new_vol)
             pygame.time.wait(int(step_delay))
             
        self.set_volume(target)
