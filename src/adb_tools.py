import subprocess
import os
import time
import xml.etree.ElementTree as ET
from colorama import Fore, Style

# We assume adb.exe is in the project root under platform-tools
ADB_PATH = os.path.join(os.path.dirname(__file__), "..", "platform-tools", "adb.exe")

class ADBEngine:
    def __init__(self, voice_engine=None):
        self.voice = voice_engine
        
    def _run_adb(self, cmd_args):
        """Helper to run adb commands silently."""
        full_cmd = [ADB_PATH] + cmd_args
        try:
            result = subprocess.run(full_cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"[ADB] Error running {cmd_args}: {e.stderr}")
            return None

    def _tap_element_by_text(self, text: str, exact_match: bool = False, exclude_text: str = None) -> bool:
        """Dumps UI XML to find a node with specific text or content-desc, then calculates its center and taps."""
        print(f"[ADB] Scanning screen for '{text}'...")
        # Dump to device sdcard
        self._run_adb(["shell", "uiautomator", "dump", "/sdcard/window_dump.xml"])
        
        # Pull to local PC
        dump_path = os.path.join(os.path.dirname(__file__), "window_dump.xml")
        self._run_adb(["pull", "/sdcard/window_dump.xml", dump_path])
        
        if not os.path.exists(dump_path):
            return False
            
        try:
            tree = ET.parse(dump_path)
            root = tree.getroot()
            
            target_node = None
            text_lower = text.lower()
            exclude_lower = exclude_text.lower() if exclude_text else None
            
            for node in root.iter('node'):
                node_text = node.attrib.get('text', '')
                node_desc = node.attrib.get('content-desc', '')
                
                # Exclude if requested
                if exclude_lower:
                    if exclude_lower in node_text.lower() or exclude_lower in node_desc.lower():
                        continue
                        
                match = False
                if exact_match:
                    if node_text.lower() == text_lower or node_desc.lower() == text_lower:
                        match = True
                else:
                    if text_lower in node_text.lower() or text_lower in node_desc.lower():
                        match = True
                        
                if match:
                    bounds_str = node.attrib.get('bounds', '')
                    if bounds_str:
                        target_node = node
                        break # Grab the first valid one
                        
            if target_node is not None:
                # bounds is like "[x1,y1][x2,y2]"
                bounds_str = target_node.attrib.get('bounds')
                bounds = bounds_str.replace('][', ',').replace('[', '').replace(']', '').split(',')
                x1, y1, x2, y2 = map(int, bounds)
                
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                
                print(f"[ADB] Tapping {text} at {center_x}, {center_y}")
                self._run_adb(["shell", "input", "tap", str(center_x), str(center_y)])
                return True
                
        except Exception as e:
            print(f"[ADB] UI Parse error: {e}")
        finally:
            if os.path.exists(dump_path):
                try:
                    os.remove(dump_path)
                except:
                    pass
                
        return False

    def execute_whatsapp_call(self, contact_name: str) -> str:
        """
        Automates WhatsApp to search for a contact and tap the Audio Call button using smart XML layout scanning.
        Requires the phone screen to be unlocked and WhatsApp installed.
        """
        print(f"{Fore.CYAN}[ADB] Initiating WhatsApp Call to {contact_name}...{Style.RESET_ALL}")
        if self.voice:
            self.voice.speak(f"Dialing {contact_name} on WhatsApp via the physical bridge.")
            
        # 1. Wake the screen just in case
        self._run_adb(["shell", "input", "keyevent", "KEYCODE_WAKEUP"])
        
        # 2. Force stop WhatsApp to ensure a clean state
        self._run_adb(["shell", "am", "force-stop", "com.whatsapp"])
        time.sleep(1)
        
        # 3. Launch WhatsApp directly to the Main intent
        self._run_adb([
            "shell", "am", "start", 
            "-n", "com.whatsapp/.Main"
        ])
        time.sleep(3) # Wait for it to load
        
        # 4. Tap the Android Search keyevent
        self._run_adb(["shell", "input", "keyevent", "84"]) # KEYCODE_SEARCH
        time.sleep(1)
        
        # 5. Type the contact name
        self._run_adb(["shell", "input", "text", contact_name.replace(" ", "%s")])
        time.sleep(3) # Wait for search results to populate
        
        # 6. Select the contact
        # ANY tap or ENTER keypress while the search bar is active instantly triggers Meta AI.
        # We must use pure hardware DPAD navigation to move the invisible focus ring DOWN directly
        # from the search bar, past the Meta AI rows, and onto the human contact.
        
        # We do NOT press Enter or Back. We just tab down immediately.
        # Press DPAD_DOWN once to jump focus from the search bar directly to the first human contact result.
        self._run_adb(["shell", "input", "keyevent", "20"]) # DPAD_DOWN
        time.sleep(0.5)
        
        # Now that focus is safely on the contact row, press ENTER to open the chat.
        self._run_adb(["shell", "input", "keyevent", "66"]) # KEYCODE_ENTER
        time.sleep(2) # Wait for the chat to open
        
        # 7. Tap the Voice Call button
        # WhatsApp usually has "Voice call" as the content-desc for the phone icon
        call_success = self._tap_element_by_text("Voice call", exact_match=False)
        if not call_success:
             # Failsafe: Try looking for just "Call"
             call_success = self._tap_element_by_text("Call", exact_match=False)
             if not call_success:
                 # Absolute fallback if UI parsing fails but the chat is open 
                 # We guess the top right corner relative to standard aspect ratios
                 self._run_adb(["shell", "input", "tap", "850", "150"])
                 print(f"Successfully initiated WhatsApp call using blind fallback to {contact_name}.")
        
        # 8. Confirm the call if a dialog appears
        time.sleep(1.5)
        # Tap the "Call" button on the "Start voice call?" dialog
        confirm_success = self._tap_element_by_text("Call", exact_match=True)
        if not confirm_success:
             # Just in case exact_match fails due to capitalization or spacing
             confirm_success = self._tap_element_by_text("Call", exact_match=False)
             if not confirm_success:
                 print(f"{Fore.YELLOW}[ADB] UIAutomator failed to see 'Call' dialog. Forcing hardware confirmation...{Style.RESET_ALL}")
                 # The overlay dialog usually defaults focus to "Cancel" or "Call".
                 # Press DPAD_RIGHT to ensure we tab over to "Call", then hit ENTER.
                 self._run_adb(["shell", "input", "keyevent", "22"]) # KEYCODE_DPAD_RIGHT
                 time.sleep(0.5)
                 self._run_adb(["shell", "input", "keyevent", "66"]) # KEYCODE_ENTER
             
        # 9. Enable Speakerphone for the Audio Bridge (Option A)
        # Wait for the call screen to fully construct
        print(f"{Fore.CYAN}[ADB] Waiting for call to connect to enable Speakerphone...{Style.RESET_ALL}")
        time.sleep(3)
        # WhatsApp usually labels the speakerphone toggle as "Speaker" or "Speakerphone"
        speaker_success = self._tap_element_by_text("Speaker", exact_match=False)
        if not speaker_success:
            print(f"{Fore.YELLOW}[ADB] Could not find Speaker button via UIAutomator. Call might be ringing.{Style.RESET_ALL}")
             
        return f"Successfully initiated WhatsApp call to {contact_name}."

    def end_call(self):
        """Ends the active phone call by attempting to tap 'End call' or sending the hardware end call event."""
        print(f"{Fore.CYAN}[ADB] Attempting to end active call...{Style.RESET_ALL}")
        
        # Method 1: Try UI Automator first for WhatsApp's specific "End call" button
        success = self._tap_element_by_text("End call", exact_match=False)
        
        if not success:
            # Method 2: Fallback to Android Hardware End Call event
            # Note: KEYCODE_ENDCALL (6) sometimes only works for cellular calls depending on the OEM
            self._run_adb(["shell", "input", "keyevent", "6"])
        
        return "Call ended via ADB."
