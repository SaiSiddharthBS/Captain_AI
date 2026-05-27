import numpy as np
from scipy.io.wavfile import write
import os

def generate_chime():
    # Parameters
    rate = 44100
    duration = 0.3 # seconds
    freq = 880 # Hz (A5)
    
    t = np.linspace(0, duration, int(rate * duration), endpoint=False)
    
    # Generate Sine Wave with envelope
    # A simple "ping" sound decays over time
    wave = 0.5 * np.sin(2 * np.pi * freq * t)
    
    # Envelope (Attack and Decay)
    # Fast attack, slow decay
    envelope = np.exp(-5 * t)
    wave = wave * envelope
    
    # Convert to 16-bit PCM
    audio = (wave * 32767).astype(np.int16)
    
    # Save
    os.makedirs('media/sounds', exist_ok=True)
    write('media/sounds/chime.wav', rate, audio)
    print("Generated media/sounds/chime.wav")

if __name__ == "__main__":
    generate_chime()
