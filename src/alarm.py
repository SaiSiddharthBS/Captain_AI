import json
import time
import threading
import datetime
import os
from src.config import ALARMS_FILE

class AlarmEngine:
    def __init__(self, voice_engine=None):
        self.voice_engine = voice_engine
        self.alarms = self._load_alarms()
        self.active_alarm = None
        self.running = True
        self.snoozed_count = 0
        
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()

    def _load_alarms(self):
        if not os.path.exists(ALARMS_FILE):
            return []
        try:
            with open(ALARMS_FILE, 'r') as f:
                return json.load(f)
        except:
            return []

    def save_alarms(self):
        with open(ALARMS_FILE, 'w') as f:
            json.dump(self.alarms, f, indent=4)

    def set_alarm(self, time_str, label="Wake up", urgent=False):
        self.alarms.append({
            "time": time_str, 
            "label": label, 
            "enabled": True,
            "urgent": urgent
        })
        self.save_alarms()
        status = "Critical Alarm" if urgent else "Alarm"
        return f"{status} set for {time_str}"

    def snooze(self):
        if not self.active_alarm: return "No alarm to snooze."
        
        # STRICT MODE LOGIC
        # If urgent: 0 snoozes.
        # If normal: 1 snooze max.
        is_urgent = self.active_alarm.get("urgent", False)
        limit = 0 if is_urgent else 1
        
        if self.snoozed_count >= limit:
            if is_urgent:
                return "No. This is important. Get up."
            else:
                return "You already snoozed once. Get up."
        
        # Allowed to snooze
        self.active_alarm = None # Temporarily clear active state
        self.snoozed_count += 1
        
        # We need to re-trigger this alarm in 5 mins
        # For V1 simplicity, we just add a 5-min temp alarm? 
        # Or better: don't clear self.active_alarm? 
        # The monitor loop checks 'active_alarm'. If we clear it, it stops ringing.
        # We need a way to make it ring again.
        # Let's create a NEW one-off alarm for +5 mins.
        
        now = datetime.datetime.now()
        snooze_time = (now + datetime.timedelta(minutes=5)).strftime("%H:%M")
        
        # Add temp alarm
        self.alarms.append({
            "time": snooze_time,
            "label": f"Snooze: {self.active_alarm['label']}",
            "enabled": True,
            "urgent": True # Snooze is ALWAYS urgent. You don't get to snooze a snooze.
        })
        self.save_alarms()
        
        return "Snoozing for 5 minutes."

    def stop_alarm(self):
        self.active_alarm = None
        self.snoozed_count = 0
        return "Alarm stopped."

    def cancel_all_alarms(self):
        count = len(self.alarms)
        self.alarms = []
        self.save_alarms()
        return f"Cancelled {count} alarms."

    def _monitor_loop(self):
        while self.running:
            now = datetime.datetime.now().strftime("%H:%M")
            for alarm in self.alarms:
                if alarm["enabled"] and alarm["time"] == now:
                    # Very simple trigger logic
                    if not self.active_alarm: 
                         self.trigger_alarm(alarm)
                         time.sleep(60) # Avoid double trigger
            time.sleep(1)

    def trigger_alarm(self, alarm):
        self.active_alarm = alarm
        print(f"ALARM: {alarm['label']}")
        
        # Start a loop in a separate thread so it doesn't block the monitor
        threading.Thread(target=self._alarm_loop, args=(alarm,), daemon=True).start()

    def _alarm_loop(self, alarm):
        # Strict Volume: We can't easily control OS volume, but we ensure OUR output is max.
        # We rely on VoiceEngine to handle the actual 'speak' volume (which is hardcoded 1.0).
        
        while self.active_alarm == alarm:
             # Speak loudly
             if self.voice_engine:
                 self.voice_engine.speak(f"Wake up! {alarm['label']}!")
                 
             # Wait a bit between shouts
             time.sleep(2)
             
             # Safety check if alarm was stopped while sleeping
             if self.active_alarm != alarm:
                 break
