import os

import json

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
MEDIA_DIR = os.path.join(BASE_DIR, 'media')
MODELS_DIR = os.path.join(BASE_DIR, 'models')
CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MEDIA_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

# Files
MEMORY_FILE = os.path.join(DATA_DIR, 'memory.json')
ALARMS_FILE = os.path.join(DATA_DIR, 'alarms.json')
TODO_FILE = os.path.join(DATA_DIR, 'todo.json')

# Load Config
def load_config():
    defaults = {
        "voice_rate": 150,
        "default_volume": 1.0,
        "wake_word_sensitivity": 0.35,
        "groq_api_key": "",
        "alarm_folders": ["Chill", "Devotional"],
        "user_name": "Boss"
    }
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                user_config = json.load(f)
                defaults.update(user_config)
        except Exception as e:
            print(f"Error loading config: {e}")
            
    return defaults

CONFIG = load_config()

# Expose individual settings for backward compatibility if needed, 
# but preferably use CONFIG['key'] in code.
DEFAULT_VOICE_RATE = CONFIG["voice_rate"]
DEFAULT_VOLUME = CONFIG["default_volume"]
