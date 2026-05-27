import os
import webbrowser
import subprocess
import ctypes
import platform
import wikipedia
from ddgs import DDGS

class ToolsEngine:
    def __init__(self, voice_engine=None):
        self.os_type = platform.system()
        self.voice = voice_engine

    @staticmethod
    def perform_wiki_search(query: str) -> str:
        """Fetches the definitive Wikipedia summary for a specific entity or concept."""
        try:
            # Extract potential subject (e.g., "who is the president" -> "president of usa")
            # Wikipedia search is very forgiving with exact matches
            search_results = wikipedia.search(query, results=1)
            if not search_results:
                return ""
            
            # Fetch the summary of the top result
            summary = wikipedia.summary(search_results[0], sentences=2)
            return f"[WIKIPEDIA FACT]: {summary}"
        except Exception as e:
            print(f"[ToolsEngine] Wiki Search Error: {e}")
            return ""

    @staticmethod
    def perform_web_search(query: str, max_results=3) -> str:
        """Silently searches live DuckDuckGo News and returns a compiled string of the top text snippets."""
        try:
            results = DDGS(proxy=None, timeout=10).news(query, max_results=max_results)
            if not results:
                return ""
                
            snippets = []
            for i, res in enumerate(results):
                title = res.get('title', '')
                body = res.get('body', '')
                snippets.append(f"[{i+1}] {title}: {body}")
            
            return "\n".join(snippets)
        except Exception as e:
            print(f"[ToolsEngine] Web Search Error: {e}")
            return ""

    def open_app_or_url(self, target: str):
        """Opens a local application if found, otherwise falls back to URL/Search."""
        target = target.lower().strip()
        
        # 1. Local App Routing (Windows common paths & executables)
        app_paths = {
            "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "spotify": os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe"),
            "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            "vscode": os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
            "code": os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe")
        }
        
        # 1.5 Windows UWP Apps and Shell Folders
        shell_paths = {
            "mail": "outlookmail:",
            "gmail": "outlookmail:",
            "google mail": "outlookmail:",
            "calendar": "outlookcal:",
            "this pc": "explorer.exe shell:::{20D04FE0-3AEA-1069-A2D8-08002B30309D}",
            "recycle bin": "explorer.exe shell:RecycleBinFolder",
            "trash": "explorer.exe shell:RecycleBinFolder"
        }
        
        # Try Shell Apps first
        for app_name, app_path in shell_paths.items():
            if app_name in target:
                if self.voice: self.voice.speak(f"Opening {app_name}.")
                try:
                    os.startfile(app_path) if ":" in app_path else subprocess.Popen(app_path)
                    return True
                except Exception as e:
                    print(f"Failed to open shell app {app_name}: {e}")
                    break
        
        # Try Standard Apps second
        for app_name, app_path in app_paths.items():
            if app_name == target or app_name in target:
                if self.voice:
                    self.voice.speak(f"Opening {app_name}.")
                try:
                    subprocess.Popen(app_path)
                    return True
                except Exception as e:
                    print(f"Failed to open {app_name}: {e}")
                    break

        # 2. Web Routing (No local app match)
        url = ""
        if "youtube" in target:
            # Did they ask for a specific video? (e.g., "play rockstar on youtube" -> routed here from brain)
            if "play " in target or "search " in target:
                query = target.replace("play ", "").replace("search ", "").replace("on youtube", "").strip()
                import urllib.parse
                url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
                if self.voice: self.voice.speak(f"Searching YouTube for {query}.")
            else:
                url = "https://www.youtube.com"
                if self.voice: self.voice.speak("Opening YouTube.")
        elif target == "google" or target == "open google":
            url = "https://www.google.com"
            if self.voice: self.voice.speak("Opening Google.")
        elif "github" in target:
            url = "https://github.com"
            if self.voice: self.voice.speak("Opening GitHub.")
        else:
            # Try to infer it's a direct open vs a search
            url = f"https://www.google.com/search?q={target}"
            if self.voice: self.voice.speak(f"Searching the web for {target}.")
            
        webbrowser.open(url)
        return True

    def execute_cmd(self, action: str):
        """Executes safe hardcoded system commands."""
        action = action.lower()
        
        if self.os_type == "Windows":
            if "sleep" in action or "suspend" in action:
                if self.voice: self.voice.speak("Going to sleep. Goodnight, Boss.")
                subprocess.Popen("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
                return True
                
            elif "lock" in action:
                if self.voice: self.voice.speak("Locking the workstation.")
                subprocess.Popen("rundll32.exe user32.dll,LockWorkStation")
                return True
                
            elif "empty bin" in action or "empty recycle" in action:
                # Magic ctypes call to empty Windows Recycle Bin
                SHEmptyRecycleBin = ctypes.windll.shell32.SHEmptyRecycleBinW
                result = SHEmptyRecycleBin(None, None, 7) # 7 = No confirmation, no progress, no sound
                if result == 0:
                    if self.voice: self.voice.speak("Recycle bin emptied.")
                else:
                    if self.voice: self.voice.speak("The recycle bin is already empty.")
                return True
                
        return False

    def compose_email(self, to_email: str, subject: str, body: str):
        """Constructs a Gmail compose URI, opens the browser, and uses PyAutoGUI to send it."""
        import urllib.parse
        import time
        import pyautogui
        try:
            subject_encoded = "" if not subject else urllib.parse.quote(subject)
            # Clean up the body to prevent duplicate sign-offs, then enforce our standard signature
            body_clean = body.strip()
            if body_clean.lower().endswith("regards.") or body_clean.lower().endswith("regards"):
                body_clean = body_clean.rsplit("regards", 1)[0].strip()
            
            final_body = f"{body_clean}\n\nBest Regards,\nCaptain"
            body_encoded = urllib.parse.quote(final_body)
            to_email_clean = "" if not to_email else to_email.strip()
            
            # Use Gmail compose URL format
            url = f"https://mail.google.com/mail/?view=cm&fs=1&to={to_email_clean}&su={subject_encoded}&body={body_encoded}"
            
            # Open default browser
            webbrowser.open(url)
            
            if self.voice:
                self.voice.speak("Opening Gmail. Sending in 5 seconds, please do not touch the mouse or keyboard.")
            
            # Wait for the browser and Gmail to initialize
            time.sleep(3)
            
            # Deep force the window to the absolute foreground
            import pygetwindow as gw
            for window in gw.getAllWindows():
                if not window.title: continue
                title_lower = window.title.lower()
                if "compose mail" in title_lower or "gmail" in title_lower or "edge" in title_lower or "chrome" in title_lower or "firefox" in title_lower or "brave" in title_lower:
                    try:
                        if window.isMinimized:
                            window.restore()
                        window.activate()
                        window.maximize()
                        break # Found and focused a browser
                    except Exception as e:
                        pass # Ignore PyGetWindowException (Windows 0 errorCode bug)
            
            # Wait another 3 seconds to let the Compose box finish rendering after maximizing
            time.sleep(3)
            
            # Click the absolute center of the maximized browser window to guarantee hardware keyboard focus
            screen_width, screen_height = pyautogui.size()
            pyautogui.click(screen_width // 2, screen_height // 2)
            time.sleep(1)
            
            # Simulate hitting Ctrl+Enter to send the email in Gmail
            pyautogui.hotkey('ctrl', 'enter')
            time.sleep(0.5)
            # Failsafe double-tap just in case the first one didn't register
            pyautogui.hotkey('ctrl', 'enter')
            
            if self.voice:
                 self.voice.speak("Email has been sent.")
                 
            return "Email sent successfully via Gmail."
        except Exception as e:
            err_msg = f"Email Composition Error: {e}"
            print(f"[ToolsEngine] {err_msg}")
            if self.voice:
                self.voice.speak("I was unable to open and automate the email client.")
            return f"Failed to send email: {e}"
