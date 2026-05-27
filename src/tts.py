import subprocess
import os
import time
import pygame
from src.config import MODELS_DIR

import hashlib
from src.config import MEDIA_DIR

# Path to piper executable (assuming setup_v2.py ran)
PIPER_EXE = os.path.join(MODELS_DIR, 'piper', 'piper.exe')
VOICE_MODEL = os.path.join(MODELS_DIR, 'piper', 'voice.onnx')
CACHE_DIR = os.path.join(MEDIA_DIR, 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

class VoiceEngine:
    def __init__(self, ws_server=None):
        self.ws_server = ws_server
        self.output_file = os.path.join(MODELS_DIR, 'temp_speech.wav')
        pygame.mixer.init() # Ensure mixer is ready
        self._prewarm_cache()
        
    def _get_cache_path(self, text):
        # Create a safe filename from text content
        hash_obj = hashlib.md5(text.encode())
        hash_id = hash_obj.hexdigest()
        return os.path.join(CACHE_DIR, f"{hash_id}.wav")

    def _prewarm_cache(self):
        # Common phrases to generate at startup (or just ensure they exist)
        phrases = [
            "Yes?",
            "I'm listening.",
            "Say that again?",
            "Alarm! Wake up!",
            "Music stopped.",
            "Playing your library."
        ]
        print("Pre-warming voice cache...")
        for p in phrases:
            # We treat them as if we are speaking them, but just generate file
            path = self._get_cache_path(p)
            if not os.path.exists(path):
                self._generate_audio(p, path)
        print("Voice cache ready.")

    def speak(self, text):
        if not text:
            return
            
        print(f"Captain: {text}")
        
        # Route to mobile if Telegram is active
        if self.ws_server and hasattr(self.ws_server, 'telegram'):
            self.ws_server.telegram.send_reply_sync(text)
        
        # Check cache
        cache_path = self._get_cache_path(text)
        if os.path.exists(cache_path):
            self._play_audio(cache_path)
            return

        # Not cached, generate temp
        if self._generate_audio(text, cache_path): # Save to cache for next time!
             self._play_audio(cache_path)
    
    def _generate_audio(self, text, output_path):
        # Piper Command: echo "text" | piper --model voice.onnx --output_file out.wav
        clean_text = text.replace('"', '').replace('\n', ' ')
        cmd = f'echo {clean_text} | "{PIPER_EXE}" --model "{VOICE_MODEL}" --output_file "{output_path}"'
        
        try:
            subprocess.run(cmd, shell=True, check=True)
            return True
        except Exception as e:
            print(f"TTS Gen Error: {e}")
            return False

    def _play_audio(self, file_path):
        # We use a separate channel for voice if possible to allow ducking music
        # But pygame.mixer.music is used for songs. 
        # We should use a Sound object for voice.
        
        try:
            sound = pygame.mixer.Sound(file_path)
            # Voice should be LOUD
            sound.set_volume(1.0) 
            channel = sound.play()
            
            # Block until finished? Or async? 
            # For conversation, usually we want to block so we don't listen to ourselves.
            while channel.get_busy():
                pygame.time.wait(100)
                
        except Exception as e:
            print(f"Playback Error: {e}")

    def stop(self):
        pygame.mixer.stop()
