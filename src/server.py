import asyncio
import websockets
import json
import threading
from src.brain import Brain
from src.stt import EarEngine
from src.telegram_engine import TelegramEngine

class WebSocketServer:
    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port
        self.clients = set()
        self.loop = asyncio.new_event_loop()
        
        # Initialize Core Engines
        print("[Server] Initializing Brain...")
        self.brain = Brain(ws_server=self)
        self.brain.llm_enabled = False # V18: Request from user to default to OFF
        
        print("[Server] Initializing EarEngine...")
        self.ear = EarEngine(brain=self.brain, ws_server=self)
        
        # Start Listen Loop in background thread
        self.listen_thread = threading.Thread(target=self.ear.listen_loop, daemon=True)
        self.listen_thread.start()
        
        # Start Telegram Listener in background thread
        print("[Server] Initializing Telegram Engine...")
        self.telegram = TelegramEngine(brain=self.brain)
        self.telegram_thread = threading.Thread(target=self.telegram.start, daemon=True)
        self.telegram_thread.start()
        
        print(f"[Server] WebSocket Server starting on ws://{host}:{port}")

    async def register(self, websocket):
        self.clients.add(websocket)
        print(f"[Server] Client connected: {websocket.remote_address}")
        try:
            # Send welcome state when HUD connects to indicate backend is ready
            await websocket.send(json.dumps({
                "state": "READY",
                "text": "Captain AI is Online.\nMicrophone Active."
            }))
            async for message in websocket:
                data = json.loads(message)
                await self.handle_message(data)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.remove(websocket)
            print(f"[Server] Client disconnected: {websocket.remote_address}")

    async def handle_message(self, data):
        """Handle incoming messages from the Tauri frontend."""
        cmd = data.get("command")
        if cmd == "stop":
            self.brain.stop_all()
        elif cmd == "toggle_llm":
            self.brain.llm_enabled = data.get("enabled", False)
            print(f"[Server] LLM Enabled: {self.brain.llm_enabled}")
        elif cmd == "manual_listen":
            # Fire and forget listen_once in a thread
            threading.Thread(target=self.ear.listen_once, daemon=True).start()
        elif cmd == "process_text":
            input_text = data.get("text", "")
            if input_text:
                # Process in a background thread so we don't block the asyncio loop
                threading.Thread(target=self.brain.process_input, args=(input_text,), daemon=True).start()

    def broadcast_sync(self, message_dict):
        """Thread-safe way to broadcast from Python threads to the asyncio loop."""
        if not self.clients:
            return
            
        async def _broadcast():
            msg = json.dumps(message_dict)
            for client in list(self.clients):
                try:
                    await client.send(msg)
                except:
                    pass
        
        # Schedule the coroutine in the main event loop
        asyncio.run_coroutine_threadsafe(_broadcast(), self.loop)

    async def _start_server(self):
        """Async context manager wrapper for websockets 16.0 compatibility."""
        async with websockets.serve(self.register, self.host, self.port):
            await asyncio.Future()  # run forever

    def start(self):
        """Starts the WebSocket event loop."""
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._start_server())

if __name__ == "__main__":
    server = WebSocketServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("[Server] Shutting down...")
