import sys
import json
import asyncio
import keyboard
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QGraphicsDropShadowEffect, QLineEdit, QMenu, QScrollArea
from PyQt6.QtCore import Qt, QPropertyAnimation, QRect, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QColor, QFont, QAction
import websockets

class WebSocketThread(QThread):
    message_received = pyqtSignal(dict)

    def run(self):
        asyncio.run(self.listen())

    async def listen(self):
        uri = "ws://localhost:8765"
        while True:
            try:
                async with websockets.connect(uri) as websocket:
                    print("[HUD] Connected to Brain.")
                    while True:
                        msg = await websocket.recv()
                        data = json.loads(msg)
                        self.message_received.emit(data)
            except Exception as e:
                print(f"[HUD] Connection lost, retrying... {e}")
                await asyncio.sleep(2)
                
    def send_message(self, message_dict):
        """Send a message to the server via a short-lived connection if needed, 
           or ideally queue it. For simplicity, we fire-and-forget here."""
        async def _send():
            try:
                uri = "ws://localhost:8765"
                async with websockets.connect(uri) as websocket:
                    await websocket.send(json.dumps(message_dict))
            except:
                pass
        asyncio.run(_send())

class HotkeyThread(QThread):
    hotkey_pressed = pyqtSignal()
    
    def run(self):
        # Global hotkey mapping (Ctrl+Shift+Space)
        keyboard.add_hotkey('ctrl+shift+space', lambda: self.hotkey_pressed.emit())
        keyboard.wait()

class GhostHUD(QWidget):
    def __init__(self):
        super().__init__()
        
        # --- Window Properties (The "Ghost" Setup) ---
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Initialize UI Components
        self.init_ui()
        
        # Animations
        self.slide_anim = QPropertyAnimation(self, b"geometry")
        self.slide_anim.setDuration(400) # 400ms smooth slide
        
        # State
        self.is_visible = False
        self.screen_width = QApplication.primaryScreen().size().width()
        self.hud_width = 450      # Expanded width to hold full paragraphs
        self.hud_height = 200     # Taller to prevent text clipping
        self.hidden_y = -self.hud_height - 10
        self.visible_y = 20
        self.llm_enabled = False # Local state cache
        
        # Set Initial Position (Hidden above screen)
        self.setGeometry((self.screen_width - self.hud_width) // 2, self.hidden_y, self.hud_width, self.hud_height)
        
        # Start WebSocket listener
        self.ws_thread = WebSocketThread()
        self.ws_thread.message_received.connect(self.handle_event)
        self.ws_thread.start()
        
        # Start Global Hotkey listener
        self.hotkey_thread = HotkeyThread()
        self.hotkey_thread.hotkey_pressed.connect(self.on_hotkey)
        self.hotkey_thread.start()

    def init_ui(self):
        # Background Pill container with blur-like semi-transparency
        self.container = QWidget(self)
        self.container.setStyleSheet("""
            QWidget {
                background-color: rgba(20, 20, 25, 200);
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 30);
            }
        """)
        self.container.resize(450, 200)
        
        # Layout
        layout = QVBoxLayout(self.container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # --- THE LOGO (CAPT'AI'N) ---
        self.lbl_logo = QLabel("CAPT<span style='color: #ffffff;'>AI</span>N", self)
        # We start with basic grey, and the AI gets its glow via rich text + shadow
        self.lbl_logo.setStyleSheet("""
            QLabel {
                color: #555555;
                font-family: 'Segoe UI', sans-serif;
                font-size: 28px;
                font-weight: 800;
                letter-spacing: 4px;
                background: transparent;
                border: none;
            }
        """)
        self.lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # The Neon Glow Effect
        self.glow = QGraphicsDropShadowEffect(self)
        self.glow.setBlurRadius(20) # Bright glow
        self.glow.setColor(QColor(0, 255, 255, 0)) # Start transparent
        self.glow.setOffset(0, 0)
        self.lbl_logo.setGraphicsEffect(self.glow)
        
        layout.addWidget(self.lbl_logo)
        
        # --- SUBTEXT / STREAM ---
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.lbl_text = QLabel("...", self.scroll_area)
        self.lbl_text.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                background: transparent;
                border: none;
            }
        """)
        self.lbl_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_text.setWordWrap(True)
        
        self.scroll_area.setWidget(self.lbl_text)
        layout.addWidget(self.scroll_area)
        
        # --- TEXT INPUT BAR ---
        self.input_box = QLineEdit(self)
        self.input_box.setStyleSheet("""
            QLineEdit {
                background-color: rgba(0, 0, 0, 100);
                color: white;
                border: 1px solid rgba(255, 255, 255, 50);
                border-radius: 10px;
                padding: 4px 10px;
                font-family: 'Segoe UI', sans-serif;
            }
        """)
        self.input_box.setPlaceholderText("Type a command...")
        self.input_box.returnPressed.connect(self.submit_text)
        self.input_box.hide() # Hidden by default, shown on hotkey
        layout.addWidget(self.input_box)

    def on_hotkey(self):
        """Triggered by Ctrl+Shift+Space"""
        if self.is_visible:
            self.hide_hud()
        else:
            self.show_hud()
            self.lbl_text.setText("")
            self.input_box.setText("")
            self.input_box.show()
            self.input_box.setFocus()
            
    def submit_text(self):
        """Sends the typed text to the backend socket."""
        text = self.input_box.text().strip()
        if text:
            self.ws_thread.send_message({"command": "process_text", "text": text})
            self.input_box.setText("")
            self.input_box.hide()
            self.lbl_text.setText(f"User: {text}")
            self.set_glow((0, 255, 255, 255)) # Act like we are listening/processing
            
    def contextMenuEvent(self, event):
        """Right click menu for HUD controls."""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #555;
            }
            QMenu::item:selected {
                background-color: #0078d7;
            }
        """)
        
        # Toggle LLM Action
        toggle_text = "Turn AI Engine OFF" if self.llm_enabled else "Turn AI Engine ON"
        toggle_action = QAction(toggle_text, self)
        toggle_action.triggered.connect(self.toggle_llm)
        menu.addAction(toggle_action)
        
        # Stop Action
        stop_action = QAction("Stop Current Task", self)
        stop_action.triggered.connect(lambda: self.ws_thread.send_message({"command": "stop"}))
        menu.addAction(stop_action)
        
        # Hide Action
        hide_action = QAction("Hide HUD", self)
        hide_action.triggered.connect(self.hide_hud)
        menu.addAction(hide_action)
        
        menu.exec(event.globalPos())
        
    def toggle_llm(self):
        self.llm_enabled = not self.llm_enabled
        self.ws_thread.send_message({"command": "toggle_llm", "enabled": self.llm_enabled})
        self.show_hud()
        status = "ON" if self.llm_enabled else "OFF"
        self.lbl_text.setText(f"AI Engine is now {status}")
        self.set_glow((0, 255, 0, 150) if self.llm_enabled else (255, 100, 0, 150))

    def show_hud(self):
        if not self.is_visible:
            self.show()
            self.slide_anim.setStartValue(self.geometry())
            self.slide_anim.setEndValue(QRect((self.screen_width - self.hud_width) // 2, self.visible_y, self.hud_width, self.hud_height))
            self.slide_anim.start()
            self.is_visible = True

    def hide_hud(self):
        if self.is_visible:
            self.slide_anim.setStartValue(self.geometry())
            self.slide_anim.setEndValue(QRect((self.screen_width - self.hud_width) // 2, self.hidden_y, self.hud_width, self.hud_height))
            self.slide_anim.start()
            self.is_visible = False
            # Clear text when hiding
            self.lbl_text.setText("")
            self.input_box.hide()

    def set_glow(self, color_tuple, radius=20):
        # Simple static glow switch based on state
        self.glow.setColor(QColor(*color_tuple))
        self.glow.setBlurRadius(radius)

    def handle_event(self, data):
        """Processes state and stream events from Python Brain over WS."""
        if "state" in data:
            state = data["state"]
            text = data.get("text", "")
            
            if state == "LISTENING":
                self.show_hud()
                self.lbl_text.setText("Listening...")
                self.set_glow((0, 255, 255, 255))  # Bright Cyan
                
            elif state == "PROCESSING":
                self.lbl_text.setText(f"'{text}'")
                self.set_glow((0, 150, 255, 200))  # Deep Blue
                
            elif state == "SPEAKING":
                self.lbl_text.setText("")
                self.set_glow((50, 255, 100, 255)) # iOS Green
                
            elif state == "RECEIVED":
                self.lbl_text.setText(f"User: {text}")
                
            elif state == "READY":
                self.show_hud()
                self.lbl_text.setText(text)
                self.set_glow((0, 255, 100, 255)) # Green
                QTimer.singleShot(4000, self.hide_hud)
                
            elif state == "IDLE":
                self.set_glow((0, 0, 0, 0)) # Off
                self.hide_hud()
                
        if "stream" in data:
            current_text = self.lbl_text.text()
            self.lbl_text.setText(current_text + data["stream"])
            # Auto-scroll or wrap is handled by QLabel properties roughly

if __name__ == "__main__":
    app = QApplication(sys.argv)
    hud = GhostHUD()
    # hud.show_hud() # Uncomment to test UI without backend
    sys.exit(app.exec())
