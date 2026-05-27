import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from src.config import CONFIG
from colorama import Fore, Style

class TelegramEngine:
    def __init__(self, brain):
        self.brain = brain
        self.token = CONFIG.get("telegram_token", "")
        self.app = None
        self.bot_chat_id = None # Save the ID of the user who talks to it
        
    def start(self):
        if not self.token:
            print(f"{Fore.YELLOW}[Telegram] No token found in config. Remote access disabled.{Style.RESET_ALL}")
            return
            
        print(f"{Fore.CYAN}[Telegram] Initializing remote connection...{Style.RESET_ALL}")
        
        # We must create a new event loop exclusively for the python-telegram-bot async runtime
        # because it conflicts with standard threading if not handled carefully
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Increased timeouts to prevent random httpx.ConnectTimeout crashes
        self.app = Application.builder().token(self.token).connect_timeout(30.0).read_timeout(30.0).build()
        
        # Command handlers
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        
        # Message handler (All text messages)
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        print(f"{Fore.GREEN}[Telegram] Connected. Captain is now listening via mobile.{Style.RESET_ALL}")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=False)

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.bot_chat_id = update.effective_chat.id
        await update.message.reply_text(
            f"Captain AI Remote Link Established.\n"
            f"Your PC is online and ready for commands."
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.bot_chat_id = update.effective_chat.id
        text = update.message.text
        
        if not text:
            return
            
        print(f"\n{Fore.MAGENTA}[Telegram -> Captain]: {text}{Style.RESET_ALL}")
        
        # Route the text directly into Captain's brain EXACTLY as if the user spoke it into the mic or typed it in the HUD.
        # Since Telegram is async, but Brain.process_input is blocking (LLM streams etc.), 
        # we must wrap it in a thread so it doesn't freeze the Telegram polling loop.
        import threading
        # We tell process_input this is 'text mode' so it doesn't wait for audio cues
        threading.Thread(target=self.brain.process_input, args=(text, True), daemon=True).start()
        
    def send_reply_sync(self, text):
        """Called by Brain.voice to send text back to the phone."""
        if not self.bot_chat_id or not text or not self.token:
            return
            
        # Use a raw synchronous HTTP request to permanently bypass the nasty
        # cross-thread asyncio event loop warnings in python-telegram-bot
        import requests
        try:
             url = f"https://api.telegram.org/bot{self.token}/sendMessage"
             requests.post(url, json={"chat_id": self.bot_chat_id, "text": text}, timeout=10)
        except Exception as e:
             print(f"[Telegram] Failed to send sync reply: {e}")
