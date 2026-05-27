import os
import re
import queue
import numpy as np
import sounddevice as sd
import openwakeword
from openwakeword.model import Model
from faster_whisper import WhisperModel
from src.config import MODELS_DIR, CONFIG

# Hallucination filter patterns
_JUNK_RE = re.compile(r'^[\W\d\s]+$')           # Only symbols/numbers/whitespace
_REPEAT_RE = re.compile(r'(.)\1{4,}')            # Same char repeated 5+ times
_WHISPER_JUNK = re.compile(r'[\(\)\*]{3,}')      # Repeated brackets/asterisks

# Wake Words to look for
WAKE_MODELS = ["hey jarvis", "alexa"] # Default pre-trained ones. 'hey captain' requires custom training.
# For V2, we will use "hey jarvis" as a proxy for "Hey Captain" or train a custom one later.
# Actually, openwakeword has specific pre-trained models. Let's stick to 'hey_jarvis_v0.1' available in openwakeword.

class EarEngine:
    def __init__(self, brain=None, ws_server=None):
        self.brain = brain # Reference to brain to trigger ducking
        self.ws_server = ws_server
        self.q = queue.Queue()
        
        # 1. Load Wake Word Model
        print("Loading Wake Word Model...")
        try:
            # simple generic model for V1/V2
            openwakeword.utils.download_models(["hey_jarvis_v0.1"]) 
            self.ww_model = Model(wakeword_models=["hey_jarvis_v0.1"], inference_framework="onnx")
        except:
            print("WakeWord Init Failed. Defaulting to manual trigger mode.")
            self.ww_model = None

        # 2. Load Whisper (STT)
        print("Loading Whisper...")
        # Upgrading to 'base' for better accuracy than 'tiny'
        self.stt_model = WhisperModel("base", device="cpu", compute_type="int8", download_root=MODELS_DIR)
        
        self.listening = False
        self.audio_buffer = np.zeros(1280, dtype=np.int16) # rolling buffer for WW

    def audio_callback(self, indata, frames, time, status):
        """Streaming callback."""
        if status:
            print(status)
        self.q.put(indata.copy())

    def listen_loop(self):
        """Blocking loop that waits for wake word, then records command."""
        print("--- LISTENING FOR 'HEY JARVIS' (Proxy for Captain) ---")
        
        # Mic Stream parameters
        CHUNK = 1280
        FORMAT = np.int16
        RATE = 16000
        
        cooldown_until = 0
        with sd.InputStream(samplerate=RATE, channels=1, dtype='int16', 
                           blocksize=CHUNK, callback=self.audio_callback):
            while True:
                # 0. Active Phone Call Bypass
                if getattr(self.brain, 'in_call_mode', False):
                    # We are in an active call. The microphone is bridged to the phone.
                    # Bypass wake word entirely and continuously grab 5-second audio chunks 
                    # from the call to feed into the conversational LLM.
                    with self.q.mutex:
                        self.q.queue.clear()
                    self._handle_wake_event(RATE, is_call_turn=True)
                    continue

                # 1. Wake Word Detection Phase
                chunk = self.q.get()
                
                if self.ww_model:
                    # Check if Brain is busy FIRST
                    if self.brain and hasattr(self.brain, 'is_processing') and self.brain.is_processing:
                        # Brain is busy speaking/thinking. Ignore wake word.
                        with self.q.mutex:
                            self.q.queue.clear()
                        continue

                    # Feed to openwakeword to maintain its internal audio buffer state
                    # Ensure chunk is 1D array
                    flat_chunk = chunk.flatten()
                    prediction = self.ww_model.predict(flat_chunk)
                    
                    import time
                    if time.time() < cooldown_until:
                        continue # Skip checking the threshold, but keep feeding the model
                        
                    # Check scores against config threshold
                    threshold = CONFIG.get('wake_word_sensitivity', 0.35)
                    for mdl in prediction.keys():
                        if prediction[mdl] > threshold:
                            print(f"Wake Word Detected: {mdl}")
                            self._handle_wake_event(RATE)
                            cooldown_until = time.time() + 2.0
                            # Clear queue to avoid processing old chunks
                            with self.q.mutex:
                                self.q.queue.clear()
                            break

    def listen_once(self):
        """Manually triggers the listening loop (bypass wake word)."""
        print("Manual Trigger...")
        # We need to run _handle_wake_event in the SAME thread or ensure safety.
        # Since listen_loop is blocking in a thread, we should probably interact via queue or thread.
        # But _handle_wake_event calls sd.rec which is blocking.
        # If we call this from GUI thread, it blocks GUI. 
        # So we MUST run this in a thread.
        self._handle_wake_event(16000)

    def _is_hallucination(self, text, info):
        """Returns True if the transcription is likely junk."""
        # 1. High no-speech probability
        if hasattr(info, 'no_speech_prob') and info.no_speech_prob > 0.6:
            return True
        # 2. Only symbols/numbers
        if _JUNK_RE.match(text):
            return True
        # 3. Repeated characters (e.g. "))))))))")
        if _REPEAT_RE.search(text):
            return True
        # 4. Whisper junk patterns
        cleaned = _WHISPER_JUNK.sub('', text).strip()
        if not cleaned:
            return True
        # 5. Too short after cleanup (single char noise)
        if len(cleaned) < 2:
            return True
        return False

    def _broadcast(self, msg_dict):
        if self.ws_server:
            self.ws_server.broadcast_sync(msg_dict)

    def _handle_wake_event(self, rate, is_call_turn=False):
        """Called when wake word is heard, or when continuously listening in a phone call."""
        # Loop for continuous conversation
        keep_listening = True
        first_turn = True
        
        while keep_listening:
            self._broadcast({"state": "LISTENING"})
            # 1. Feedback (Duck + Chime)
            if self.brain:
                # Use fade out if music engine supports it (accessed via brain.music)
                # But brain.set_system_volume calls pygame.mixer.music.set_volume directly currently.
                # Let's use brain's helper which we'll update to use fade.
                self.brain.fade_media_out() 
                
                if first_turn and not is_call_turn:
                    # Play Chime only if not in a phone call (where we want silent listening)
                    import pygame
                    chime_path = "media/sounds/chime.wav"
                    if os.path.exists(chime_path):
                         # Play chime on a Sound channel, not Music channel
                         try:
                             s = pygame.mixer.Sound(chime_path)
                             s.set_volume(0.6)
                             s.play()
                             pygame.time.wait(int(s.get_length() * 1000) + 100) # Wait for chime
                         except:
                             self.brain.voice.speak("Yes?") # Fallback
                             pygame.time.wait(800)
                    else:
                         self.brain.voice.speak("Yes?")
                         pygame.time.wait(800)
                    
                    first_turn = False
                else:
                    # Subsequent turns
                    print("Listening for follow-up...")
                    import pygame
                    pygame.time.wait(300)
            
            # 2. Record Command (Active Listening)
            print("Capturing command...")
            duration = 5 # seconds
            
            # Record explicitly for 5 sec
            recording = sd.rec(int(duration * rate), samplerate=rate, channels=1, dtype='float32')
            sd.wait()
            
            # 3. Transcribe
            try:
                segments, info = self.stt_model.transcribe(recording[:, 0], beam_size=5)
                seg_list = list(segments)
                text = " ".join([s.text for s in seg_list]).strip()
                
                # --- HALLUCINATION FILTER ---
                if text and self._is_hallucination(text, info):
                    print(f"[Filtered Junk]: {text[:60]}")
                    text = ""
            except Exception as e:
                print(f"STT Error: {e}")
                text = ""
                
            if text:
                print(f"User: {text}")
                self._broadcast({"state": "RECEIVED", "text": text})
                
                if self.brain:
                    # Feed the transcribed text to the Brain.
                    # It will use in_call_mode to route to _handle_call_conversation if active.
                    keep_listening = self.brain.process_input(text)
            else:
                self._broadcast({"state": "IDLE"})
                
            # If we are in an active call, we break the internal `keep_listening` loop 
            # and let the parent `listen_loop` re-trigger us so we don't block the queue.
            if is_call_turn:
                break
            
            # 4. Restore Volume
            if self.brain:
                self.brain.fade_media_in()
                
            # 5. Process
            if text and self.brain:
                # process_input now returns True if we should keep listening
                keep_listening = self.brain.process_input(text)
            else:
                # Silence or noise -> Stop conversation
                keep_listening = False
