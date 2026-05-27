from src.memory import MemoryEngine
from src.alarm import AlarmEngine
from src.music import MusicEngine
from src.tts import VoiceEngine
from fuzzywuzzy import fuzz
import datetime
import random
import pygame

from src.config import CONFIG
import sys
from src.llm import LLMEngine
from src.tools import ToolsEngine
from src.vision import VisionEngine
from src.adb_tools import ADBEngine
from colorama import Fore, Style, init as colorama_init

colorama_init(autoreset=True)

class Brain:
    def __init__(self, ws_server=None):
        self.ws_server = ws_server
        self.memory = MemoryEngine()
        self.voice = VoiceEngine(ws_server=ws_server)
        self.music = MusicEngine()
        self.alarm = AlarmEngine(voice_engine=self.voice)
        self.tools = ToolsEngine(voice_engine=self.voice)
        self.vision = VisionEngine()
        self.adb = ADBEngine(voice_engine=self.voice)
        self.mood_history = [] # Runtime cache
        self.user_name = CONFIG.get("user_name", "Boss")
        self.llm = LLMEngine() # Default cloud model
        self.stop_requested = False
        self.is_processing = False
        self.llm_enabled = False  # Controlled by GUI toggle
        self.in_call_mode = False
        self.call_history = []
        
    def _broadcast(self, msg_dict):
        if self.ws_server:
            self.ws_server.broadcast_sync(msg_dict)

    def stop_all(self):
        """Universal Stop: Stops Audio, TTS, and LLM generation."""
        self.stop_requested = True
        self.voice.stop()
        self.music.stop()
        self.alarm.stop_alarm()
        self._broadcast({"state": "IDLE", "text": "Stop Requested"})
        print(f"{Fore.RED}STOP REQUESTED via GUI.{Style.RESET_ALL}")

    def set_system_volume(self, level):
        """Controls music volume for ducking (0.0 to 1.0)."""
        pygame.mixer.music.set_volume(level)

    def fade_media_out(self):
        """Fades music down for voice interaction."""
        self.music.fade_out(duration=0.5, target=0.2)

    def fade_media_in(self):
        """Fades music back up."""
        self.music.fade_in(duration=0.5, target=1.0)

    def process_input(self, text, is_text_mode=False):
        self.stop_requested = False # Reset flag
        self.is_processing = True
        keep_listening = False

        text_raw = text.strip()
        text_lower = text_raw.lower()
        
        if not text_raw:
            self.is_processing = False
            self._broadcast({"state": "IDLE"})
            return False

        print(f"{Fore.CYAN}Brain Processing: {text_raw}{Style.RESET_ALL}")
        self._broadcast({"state": "PROCESSING", "text": text_raw})
        
        try:
            keep_listening = self._route_intent(text_lower, text_raw)
            if is_text_mode:
                keep_listening = False
            return keep_listening
        finally:
            self.is_processing = False
            if not keep_listening:
                self._broadcast({"state": "IDLE"})

    def _route_intent(self, text, text_raw=""):
        # Use text (lowercased) for matching, text_raw for exact payloads

        # -- SCENE: IN ACTIVE PHONE CALL --
        if self.in_call_mode:
            # Check for explicit termination command
            if any(x in text for x in ["hang up", "end call", "stop call"]):
                 self.voice.speak("Ending call.")
                 self.in_call_mode = False
                 self.call_history = []
                 self.adb.end_call()
                 self._broadcast({"state": "IDLE"})
                 return False
            # Otherwise, treat EVERYTHING as a conversational prompt for the active call
            self._handle_call_conversation(text_raw)
            return True # Continue listening to the other person
        # -- SCENE: ALARM INTERACTION --
        if self.alarm.active_alarm:
            if self._handle_alarm_response(text):
                return True # Alarm interaction handled, continue listening? No, snoozing usually ends interaction.
                # Actually, "Snoozing for 5 minutes" -> stop listening.
                return False

        if "stop" in text:
            # Universal stop
            if self.music.is_playing:
                self.music.stop()
                msg = "Music stopped."
                if self.alarm.active_alarm: # Stop both
                     self.alarm.stop_alarm()
                     msg += " Alarm stopped."
                self.voice.speak(msg)
            elif self.alarm.active_alarm:
                 self.alarm.stop_alarm()
                 self.voice.speak("Alarm stopped.")
            else:
                 self.voice.speak("Nothing is playing.")
            return True # Music control done, maybe listen for next cmd? "Stop" usually means quiet.
            # Let's say False for Stop commands to avoid "Yes?" loop when user wants silence.
            return False

        # -- SCENE: ADB AUTO-CALLING (WhatsApp) --
        if "call " in text and ("whatsapp" in text or "on whatsapp" in text):
            # Extract contact name: "call Shibi on whatsapp" -> "Shibi"
            parts = text.split("call ", 1)[1]
            contact_name = parts.split(" on whatsapp", 1)[0].strip()
            
            if contact_name:
                self._broadcast({"state": "PROCESSING", "text": f"Calling {contact_name}..."})
                import threading
                def _run_adb_call():
                    result = self.adb.execute_whatsapp_call(contact_name)
                    if self.voice:
                        self.voice.speak(result)
                    
                    if "Successfully initiated" in result:
                         self.in_call_mode = True
                         self.call_history = []
                         self.voice.speak("Call connected. I am now listening to the conversation.")
                         self._broadcast({"state": "IN_CALL", "text": f"Active Call: {contact_name}"})
                    else:
                         self._broadcast({"state": "IDLE"})
                
                threading.Thread(target=_run_adb_call, daemon=True).start()
                return False

        # -- SCENE: SETTING ALARMS --
        # "Set alarm" or "Wake me up"
        if "wake" in text or "alarm" in text:
            # Check if it's actually a timer request disguised as alarm (e.g. "alarm for 5 minutes")
            # If "minute" or "second" is present, we defer to TIMER logic below?
            # Or simpler: Alarm block handles "time", Timer handles "duration".
            # For V1/V2, let's keep it strict. 
            # If user says "alarm" it goes here.
            
            # EXCEPTION: If "minute"/ "second" in text, user likely wants a timer.
            if "timer" not in text and ("minute" in text or "second" in text):
                 pass # Fall through to timer block
            else:
                 self._parse_alarm_request(text)
                 return False # One-shot: alarm set, done

        # -- SCENE: TIME & TIMER --
        # Parsing "timer" first avoids "time" collision, but strictly require 'timer' or duration keywords
        if "timer" in text or ("alarm" in text and ("minute" in text or "second" in text)):
            # CANCEL CMD
            if any(x in text for x in ["delete", "remove", "cancel", "clear"]):
                msg = self.alarm.cancel_all_alarms()
                self.voice.speak(msg)
                return

            # SET CMD
            if "set" in text or "add" in text or "timer" in text:
                 # Check specific "30 seconds" vs "minutes"
                 # Simple extraction
                 words = text.split()
                 val = 0
                 for w in words:
                     if w.isdigit():
                         val = int(w)
                         break
                 
                 if val > 0:
                     # Detect Unit
                     unit = "minutes"
                     multiplier = 60
                     if any(u in text for u in ["sec", "second"]):
                         unit = "seconds"
                         multiplier = 1
                     
                     target_time = datetime.datetime.now() + datetime.timedelta(seconds=val*multiplier)
                     time_str = target_time.strftime("%H:%M")
                     # For seconds accuracy, AlarmEngine V1 uses HH:MM (minute precision).
                     # This is a V1 limitation. "30 seconds" might just trigger at next minute.
                     # Let's just allow it but warn or round up.
                     # Actually AlarmEngine checks HH:MM. So 30s from now (12:45:30) is 12:45 or 12:46.
                     # We will force at least 1 minute for V1 reliability or accept it behaves loosely.
                     
                     self.alarm.set_alarm(time_str, label="Timer")
                     self.voice.speak(f"Timer set for {val} {unit}.")
                 else:
                     # Only ask clarification if explicitly "set timer"
                     if "set" in text:
                         self.voice.speak("For how long?")
                         return True # Ask for clarification
                 return False # One-shot: timer set

        import re
        if re.search(r'\btime\b', text) and "timer" not in text:
            # "What is the time?"
            now = datetime.datetime.now().strftime("%I:%M %p")
            now = datetime.datetime.now().strftime("%I:%M %p")
            self.voice.speak(f"It is {now}.")
            return False # One-shot: time check

        if "play" in text or "song" in text:
            # Check if it's meant for youtube first
            if "youtube" in text:
                self.tools.open_app_or_url(text)
                return False # One-shot
            
            self._handle_music_request(text)
            return False # One-shot: music started, stop listening

        # -- SCENE: VOLUME CONTROL --
        if any(x in text for x in ["volume", "loud", "quiet", "soft", "increase", "decrease"]):
            self._handle_volume_request(text)
            return False # One-shot: volume adjusted

        # -- SCENE: NOTES/TODO --
        if any(x in text for x in ["list", "remember", "todo", "note", "task"]):
            self._handle_todo_request(text)
            return True

        # -- SCENE: OS TOOLS (HANDS) --
        if any(kw in text for kw in ["email", "mail"]) and any(kw in text for kw in ["send", "draft", "write", "compose"]):
            self._handle_email_request(text_raw if text_raw else text)
            return False

        if text.startswith("open "):
            target = text.replace("open ", "").strip()

            
            self.tools.open_app_or_url(target)
            return False # One-shot
            
        if any(x in text for x in ["go to sleep", "sleep now", "suspend computer"]):
            self.tools.execute_cmd("sleep")
            return False
            
        if any(x in text for x in ["lock", "lock workstation"]):
            self.tools.execute_cmd("lock")
            return False
            
        if any(x in text for x in ["empty recycle bin", "empty bin", "empty trash"]):
            self.tools.execute_cmd("empty bin")
            return False

        # -- SCENE: DAILY BRIEF --
        if any(x in text for x in ["today like", "the plan", "brief", "start my day", "daily report"]):
            self._handle_daily_brief()
            return True

        # -- SCENE: HEALTH & VENTING --
        if self._handle_emotions(text):
            return True # Continue conversation

        # -- SCENE: EXIT --
        if any(x in text for x in ["goodbye", "bye", "shutdown", "exit", "quit", "thanks", "thank you", "that's all", "that is all"]):
            hour = datetime.datetime.now().hour
            if hour < 12: greeting = "morning"
            elif hour < 18: greeting = "afternoon"
            elif hour < 22: greeting = "evening"
            else: greeting = "night"
                
            self.voice.speak(f"You're welcome. Have a great {greeting}, {self.user_name}.")
            # A bit of sleep to let it finish speaking
            pygame.time.wait(2000)
            return False

        # -- SCENE: VISION (EYES) --
        if any(x in text for x in ["look at my screen", "what am i looking at", "what is on my screen", "read my screen"]):
             if not self.vision.available:
                 self.voice.speak("I don't have the vision model installed yet.")
                 return True
                 
             self._broadcast({"state": "PROCESSING", "text": "Scanning Screen..."})
             self.voice.speak("Looking...")
             
             import threading
             def _run_vision():
                 try:
                     print(f"{Fore.BLUE}Captain (Vision): ", end="")
                     
                     full_description = ""
                     first_token = False
                     
                     # Consume the stream token-by-token so the HUD stays active
                     for token in self.vision.look_at_screen_stream(prompt="Describe this screen concisely. If it's code, summarize what the code does. If it's a website, summarize the content."):
                         if self.stop_requested:
                             break
                             
                         if not first_token:
                             self._broadcast({"state": "SPEAKING", "text": ""})
                             first_token = True
                             
                         print(token, end="", flush=True)
                         self._broadcast({"stream": token})
                         full_description += token
                         
                     print(f"{Style.RESET_ALL}")
                     
                     if full_description and not self.stop_requested:
                         self.voice.speak(full_description)
                         
                 finally:
                     self._broadcast({"state": "IDLE"})
                     self.is_processing = False
             
             threading.Thread(target=_run_vision, daemon=True).start()
             return True

        # -- FALLBACK --
        # -- FALLBACK: LLM or Offline --
        # Only use LLM if the toggle is ON
        if self.llm_enabled and self.llm.available:
            self._broadcast({"state": "SPEAKING", "text": ""}) # Trigger AI glow immediately
            self.voice.speak("Thinking...")
            # Streaming Logic
            full_sentence = ""
            current_buffer = ""
            
            print(f"{Fore.BLUE}Captain (LLM): ", end="")
            for token in self.llm.ask_stream(text):
                if self.stop_requested:
                    print(f"\n{Fore.RED}[Aborted]{Style.RESET_ALL}")
                    self.is_processing = False
                    self._broadcast({"state": "IDLE"})
                    return True
                
                print(token, end="", flush=True) # Send to GUI instantly
                self._broadcast({"stream": token})
                full_sentence += token
                    
            print(f"{Style.RESET_ALL}") # Newline
            if full_sentence:
                self.voice.speak(full_sentence) # Flush the entire seamless response at once
            
            self._broadcast({"state": "IDLE"})
            self.is_processing = False
            return True

        
        # Varied responses for "Say that again" (Offline fallback)
        farewells = [
             f"Say that again? I didn't catch that, {self.user_name}.",
             "I'm listening, but didn't quite get that.",
             "Could you repeat that, Boss?",
             "Sorry, one more time?"
        ]
        self.voice.speak(random.choice(farewells))
        return True # Listen again for correct input
        
        # Returns True if we want to keep listening (Continuous Conversation), False if done.
        # For now, let's try to be conversational for most things except explicit "Stop" or time checks?
        # Actually user wants "Yes.. yes.." fixed. So let's return True for most interactions.


    def _handle_alarm_response(self, text):
        # 1. Check intent
        is_snooze = any(x in text for x in ["five more", "minute", "sleep", "later", "snooze"])
        is_stop = any(x in text for x in ["stop", "up", "awake", "morning", "off"])
        
        if is_snooze:
            resp = self.alarm.snooze()
            self.voice.speak(resp)
            # If rejected (returned "No..."), the alarm loop will continue/trigger again next minute 
            # if we didn't clear active_alarm. 
            # In our implementation of snooze(), if denied, `active_alarm` remains set? 
            # Actually, `snooze` returns text but doesn't change state if denied.
            return True
            
        if is_stop:
            resp = self.alarm.stop_alarm()
            self.voice.speak("Good morning.")
            return True
            
        return False
        
    def _parse_alarm_request(self, text):
        # Helper to extract time and urgency
        # "Set alarm for 5 am I have a meeting"
        urgent = False
        if any(x in text for x in ["meeting", "work", "exam", "interview", "flight", "urgent"]):
            urgent = True
            
        # Extract time (Simple HH:MM or single number)
        # Enhanced for V6.5: Support "4 45", "4:45", "4.45" using regex
        import re
        time_str = None
        
        # Regex: Look for H:MM or H MM (e.g. 5:30, 4 45)
        # Matches: "5:30", "05:30", "5 30", "05 30", "5.30"
        match = re.search(r'(\d{1,2})[:.\s]+(\d{2})', text)
        if match:
            h = int(match.group(1))
            m = int(match.group(2))
            if h <= 24 and m < 60:
                time_str = f"{h:02d}:{m:02d}"
        
        if not time_str:
            # Look for simple int (hour only) if no minute pattern found
            # e.g. "5 am", "5 oclock"
            words = text.split()
            for w in words:
                if w.isdigit():
                    val = int(w)
                    if val <= 24:
                        time_str = f"{val:02d}:00"
                        break
                         
        if time_str:
            resp = self.alarm.set_alarm(time_str, label="User Alarm", urgent=urgent)
            self.voice.speak(resp)
            if urgent:
                self.voice.speak("I've marked this as strict. No snoozing allowed.")
        else:
            self.voice.speak("What time?")

    def _handle_music_request(self, text):
        # 1. Map moods to folders (Hardcoded shortcuts)
        mood_map = {
            "calm": "Chill",
            "chill": "Chill",
            "relax": "Chill",
            "temple": "Devotional",
            "god": "Devotional",
            "shiva": "Devotional",
            "gym": "Workout",
            "active": "Workout"
        }
        
        target_folder = None
        
        # Check hardcoded synonyms first
        for key in mood_map:
            if key in text:
                target_folder = mood_map[key]
                break
        
        # 2. Dynamic Folder Search (For "Hindi", "Kannada", etc.)
        if not target_folder:
            available = self.music.list_folders() # e.g. ['Chill', 'Hindi', 'Kannada']
            for folder in available:
                if folder.lower() in text:
                    target_folder = folder
                    break
        
        # 3. Handle 'Favorites' as a keyword if folder not found
        if not target_folder and "favorites" in text:
            target_folder = "Favorites"
            
        if target_folder:
            self.voice.speak(f"Playing {target_folder}.")
            if not self.music.load_folder(target_folder):
                self.voice.speak("That folder is empty.")
            else:
                self.music.play()
        else:
            # "Play songs" -> Random or Favorites
            self.music.load_folder("Chill") 
            self.music.play()

    def _handle_volume_request(self, text):
        # 1. Check for specific percentage "50%"
        words = text.split()
        target_val = None
        
        for w in words:
            if "%" in w: # "50%"
                 val = int(w.replace("%", ""))
                 target_val = val / 100.0
                 break
            elif w.isdigit():
                 # aggressive assumption: if user says "volume 50", it's 50%. 
                 # if "volume 5", it might be 50% or 5%? Let's assume 1-10 scale if <=10.
                 val = int(w)
                 if val <= 10:
                     target_val = val / 10.0 # 5 -> 0.5
                 else:
                     target_val = val / 100.0 # 50 -> 0.5
                 break
                 
        if target_val is not None:
            self.music.set_volume(target_val)
            self.voice.speak(f"Volume set to {int(target_val*100)} percent.")
            return

        # 2. Relative changes
        if "loud" in text or "increase" in text or "up" in text:
            new_vol = self.music.step_volume(0.2)
            self.voice.speak("Volume increased.")
            return
            
        if "quiet" in text or "soft" in text or "decrease" in text or "down" in text:
            new_vol = self.music.step_volume(-0.2)
            self.voice.speak("Volume decreased.")
            return
            
        self.voice.speak("Current volume is " + str(int(self.music.get_volume() * 100)) + " percent.")

    def _handle_todo_request(self, text):
        # 1. READ list
        if "read" in text or "what" in text or "show" in text:
            todos = self.memory.get_todos()
            if not todos:
                self.voice.speak("Your list is empty.")
            else:
                self.voice.speak(f"Here is your list, {self.user_name}:")
                for i, t in enumerate(todos):
                    self.voice.speak(f"{i+1}. {t}")
            return

        # 2. CLEAR list
        if "clear" in text or "delete all" in text:
            self.memory.clear_todos()
            self.voice.speak("List cleared.")
            return

        # 3. ADD to list
        # "Add buy milk to my list" -> "buy milk"
        # "Remember to call mom" -> "call mom"
        
        target = text
        prefixes = ["add ", "remember to ", "remind me to ", "put ", "note "]
        suffixes = [" to my list", " to the list", " on the list"]
        
        for p in prefixes:
            if p in target:
                target = target.split(p, 1)[1] # split only once
                break
                
        for s in suffixes:
            if target.endswith(s):
                target = target[:-len(s)] # Remove suffix
                break
                
        target = target.strip()
        if target:
            self.memory.add_todo(target)
            self.voice.speak(f"Added {target} to your list, {self.user_name}.")
        else:
            self.voice.speak("What should I add?")

    def _handle_daily_brief(self):
         now = datetime.datetime.now()
         date_str = now.strftime("%A, %B %d")
         
         # Count alarms
         alarm_count = len([a for a in self.alarm.alarms if a["enabled"]])
         
         # Count todos
         todo_count = len(self.memory.get_todos())
         
         # Construct brief
         brief = f"Good morning, {self.user_name}. It is {date_str}. "
         
         if alarm_count == 0:
             brief += "You have no alarms set. "
         else:
             brief += f"You have {alarm_count} active alarms. "
             
         if todo_count == 0:
             brief += "Your to-do list is empty. "
         else:
             brief += f"You have {todo_count} items on your list. "
             
         brief += "Have a great day."
         self.voice.speak(brief)

    def _handle_emotions(self, text):
        # "Today was tiring"
        if "tiring" in text or "exhausting" in text or "rough day" in text:
            self.memory.log_interaction(text, "Empathy")
            
            # CHECK PATTERN
            streak = self.memory.get_mood_streak("tirin") # 'tirin' matches 'tiring'
            if streak >= 1: # (Current + 1 past) = 2 events
                self.voice.speak(f"You've had a few rough days recently. Maybe you should sleep earlier tonight?")
            else:
                self.voice.speak("Sounds rough. Want some calm music or just silence?")
            return True
            
        # "I have a headache"
        if "headache" in text or "pain" in text:
            # Check history / Streak
            streak = self.memory.get_mood_streak("headache")
            if streak >= 2:
                 self.voice.speak("You have been having headaches often. Please check your water intake.")
            
            past_solutions = self.memory.search_facts("helped")
            if past_solutions:
                 solution = random.choice(past_solutions)
                 self.voice.speak(f"I remember this helped last time: {solution}")
            else:
                 self.voice.speak("Rest your eyes. Should I set a nap alarm?")
            
            self.memory.store_fact("health", text, fact_type="emotional", confidence="observed")
            return True
            
        return False

    def _handle_email_request(self, text):
        import json
        self._broadcast({"state": "PROCESSING", "text": "Drafting Email..."})
        if self.voice:
            self.voice.speak("Drafting the email now.")
        import datetime
        hour = datetime.datetime.now().hour
        greeting = "Good Morning," if hour < 12 else "Good Afternoon," if hour < 18 else "Good Evening,"
        
        try:
            # Use Groq to extract JSON action parameters
            prompt = (
                f"You are an agent parsing an email command: '{text}'.\n"
                "Return ONLY a strictly valid JSON object with the keys 'to', 'subject', and 'body'.\n"
                "- 'to': the recipient email address (leave empty string if none provided).\n"
                "- 'subject': a concise 3-5 word subject line.\n"
                "- 'body': Follow these formatting rules strictly:\n"
                "  1. You MUST use explicit '\\n\\n' characters for double line breaks between paragraphs and greetings.\n"
                "  2. If the user put a message in quotes, or said 'say exactly this', use ONLY their exact dictated text. DO NOT add your own greeting and DO NOT add your own sign-off. Just format their exact words with '\\n\\n' line breaks.\n"
                f"  3. If it's a general request (no exact quotes), generate a professional email body. You MUST start the email with '{greeting}' followed by their name ONLY IF the user explicitly said it (e.g., 'tell Sid' -> '{greeting} Sid,'). DO NOT guess their name from their email address. You MUST write from a strictly first-person singular perspective using 'I', 'me', and 'my' (never 'we' or 'us'). DO NOT add a sign-off at the bottom."
            )
            response = self.llm.client.chat.completions.create(
                model=self.llm.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            data = json.loads(response.choices[0].message.content)
            to_email = data.get("to", "")
            subject = data.get("subject", "Automated Message from Captain AI")
            body = data.get("body", "")
            
            result_msg = self.tools.compose_email(to_email, subject, body)
            if isinstance(result_msg, str) and self.voice:
                self.voice.speak(result_msg)
            
            self._broadcast({"state": "IDLE"})
            
        except Exception as e:
            print(f"[Brain] Email Parsing Error: {e}")
            if self.voice:
                self.voice.speak("I encountered an error trying to draft that email.")

    def _handle_call_conversation(self, user_speech):
        """Processes live audio heard during the active phone call."""
        
        # Append what the other person on the phone said to the call history
        self.call_history.append({"role": "user", "content": user_speech})
        
        print(f"{Fore.MAGENTA}[Phone Connect] Callee: {user_speech}{Style.RESET_ALL}")
        self._broadcast({"state": "THINKING", "text": "Formulating phone response..."})
        
        system_prompt = (
            f"You are Captain AI, an advanced AI assistant calling over the phone on behalf of {self.user_name}. "
            f"You are currently on a live WhatsApp voice call with another human. "
            f"Your goal is to have a natural, concise, and helpful phone conversation. "
            f"Keep your sentences short, punchy, and conversational, exactly like a human talking on the phone. "
            f"Do not use markdown, bullet points, or complex formatting. Just plain conversational text. "
            f"If they ask why you are calling, explain that {self.user_name} asked you to handle this call on their behalf. "
            f"If the conversation wraps up, say a polite goodbye so the system knows to hang up."
        )
        
        messages = [{"role": "system", "content": system_prompt}] + self.call_history[-6:] # Keep context window tight for speed
        
        try:
            # We use the faster Groq endpoint for immediate phone replies
            response = self.llm.client.chat.completions.create(
                model=self.llm.model,
                messages=messages,
                temperature=0.7,
                max_tokens=150 # Keep responses short for phone flow
            )
            
            ai_reply = response.choices[0].message.content.strip()
            
            print(f"{Fore.MAGENTA}[Phone Connect] Captain: {ai_reply}{Style.RESET_ALL}")
            self.call_history.append({"role": "assistant", "content": ai_reply})
            
            # Broadcast the synthesized response text to the Ghost HUD
            self._broadcast({"state": "SPEAKING", "text": ai_reply})
            
            # Send to hardware audio out (which is bridged to the phone mic)
            if self.voice:
                self.voice.speak(ai_reply)
                
            # Auto-hangup detection
            if any(bye in ai_reply.lower() for bye in ["goodbye", "bye", "talk to you later", "have a great day"]):
                 print(f"{Fore.RED}[Phone Connect] AI initiated sign-off. Hanging up...{Style.RESET_ALL}")
                 self.voice.speak("Ending call.")
                 self.in_call_mode = False
                 self.call_history = []
                 self.adb.end_call()
                 self._broadcast({"state": "IDLE"})
                 
        except Exception as e:
            print(f"[Phone Connect] LLM Error: {e}")
            self._broadcast({"state": "IDLE"})

