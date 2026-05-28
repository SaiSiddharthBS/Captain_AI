<div align="center">
  
<img src="assets/Logo.png" width="400" alt="Captain AI Logo">

### The Sentinel Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-0078D6.svg)](https://microsoft.com/)
[![Status: Active](https://img.shields.io/badge/status-Active-brightgreen.svg)]()
[![Ollama](https://img.shields.io/badge/Ollama-Local_Vision-orange.svg)]()
[![Llama 3.3](https://img.shields.io/badge/Llama_3.3-70B-purple.svg)]()
[![Web Search RAG](https://img.shields.io/badge/RAG-Web_Search-red.svg)]()


> **Unimagined. Unbound.**<br>
> A fully offline, voice-activated AI assistant for Windows. Powered by Groq, Ollama, Faster-Whisper STT, Piper TTS, and OpenWakeWord — operating completely within your local ecosystem.

</div>

<br>

## 🌐 The Sentinel Matrix (Core Capabilities)

Captain AI is not just another voice assistant; it is a headless apparition living in your machine, offering unparalleled local control and real-time cognition.

- 📞 **Telephonic Symbiosis (ADB Automations)**: Seamlessly bridges to your Android device via USB/ADB. Captain can force-stop WhatsApp, search contacts, initiate VoIP calls, switch to speakerphone, and hold continuous AI-driven conversations over the phone line using the `Groq Llama-3.3-70b` model.
- 👁️ **Active Optics (Vision Intelligence)**: Full screen awareness using `Ollama` and the `moondream` model. Captain can look at your screen, read code, analyze images, and synthesize a summary completely offline.
- ⚡ **Zero-Latency Audio Ecosystem**: A custom pipeline featuring `OpenWakeWord` for local trigger detection ("Hey Jarvis") and `Faster-Whisper` (Int8 CPU) for hyper-fast STT. Responses are spoken through `Piper TTS` using the `en_US-ryan-medium` model, backed by an MD5 hash-based WAV caching system for instant recall.
- 🔍 **Hybrid RAG Retrieval**: Ask questions and watch Captain dynamically scrape DuckDuckGo news and Wikipedia summaries in real-time, injecting verifiable context directly into the LLM prompt to eliminate hallucinations.
- 🔐 **Secure Encrypted Uplink**: Away from your PC? The built-in Telegram Bot daemon allows you to command Captain remotely.
- 👻 **Aesthetic Ghost HUD**: A frameless, glassmorphism PyQt6 overlay that slides into view. It communicates asynchronously with the Python WebSocket daemon, glowing contextually based on the system state (Cyan = Listening, Deep Blue = Processing, Green = Speaking).

---

## 🛠️ Technology Stack

**Cognition & Vision**
- **Groq API**: `llama-3.3-70b-versatile` for hyper-speed conversational reasoning and email drafting.
- **Ollama Local**: `moondream` for screen analysis. 

**Vocal & Aural Processing**
- **STT**: `faster-whisper` (Base model, int8 quantization).
- **TTS**: `piper-tts` (ONNX format) for deep, rich offline voice synthesis.
- **Wake Word**: `openwakeword` for constant 16kHz audio stream monitoring.

**Orchestration & Media**
- **Media Engine**: `pygame` for music playback with dynamic audio ducking and fading.
- **Tools**: `yt-dlp` & `ffmpeg` for on-demand music downloading.
- **OS Automation**: `pyautogui`, `pygetwindow`, and `ctypes` for desktop commands.

**Frontend Interface**
- **V7 GUI**: `customtkinter` with animated iOS-style status orbs.
- **V10 Ghost HUD**: `PyQt6`, `HTML5`, `CSS3` (Liquid Aurora meshes & glassmorphism), `websockets`.

---

## 🏗️ Architecture Diagrams

### 1. System Block Diagram
This showcases the separation of concerns between the core backend orchestrator, the hardware layer, and the Ghost HUD frontend.

```mermaid
graph TD
    subgraph Frontend
        HUD[Ghost HUD - PyQt6 / WebSockets]
        V7GUI[CustomTkinter GUI]
    end

    subgraph Backend Orchestrator
        Server[WebSocket Server]
        Brain[Central Brain Engine]
    end

    subgraph Hardware & Interfaces
        Mic[Microphone Stream]
        Spk[Pygame Mixer Audio Out]
        Phone[Android Phone via ADB]
    end

    subgraph Intelligence Engines
        Ear[EarEngine: OpenWakeWord + Whisper]
        LLM[LLMEngine: Groq + Live RAG]
        Vision[VisionEngine: Ollama / Moondream]
        TTS[VoiceEngine: Piper TTS]
    end

    Mic --> Ear
    Ear --> Server
    Server --> Brain
    Brain --> LLM
    Brain --> Vision
    Brain --> TTS
    TTS --> Spk

    Brain <--> Phone
    Server <--> HUD
```

### 2. The Audio & Cognition Pipeline
How Captain processes your voice from start to finish.

```mermaid
sequenceDiagram
    participant User
    participant EarEngine
    participant Brain
    participant LLM
    participant VoiceEngine

    User->>EarEngine: Says "Hey Jarvis"
    EarEngine-->>Brain: Trigger Detected!
    Brain-->>VoiceEngine: Fade Music / Play Chime
    EarEngine->>EarEngine: Record 5 seconds (sd.rec)
    EarEngine->>EarEngine: Whisper STT Transcription
    EarEngine->>EarEngine: Hallucination Filter
    EarEngine->>Brain: Route Intent (Text)
    Brain->>LLM: Formulate Response
    LLM-->>Brain: Stream LLM Output
    Brain->>VoiceEngine: Piper TTS Generation
    VoiceEngine->>User: Play Audio (Pygame)
```

### 3. Active Phone Bridge Automation (WhatsApp)
The sequence when you ask Captain to "Call X on WhatsApp".

```mermaid
flowchart TD
    A[User requests call] --> B[Brain triggers ADBEngine]
    B --> C{Is Screen On?}
    C -->|No| D[KEYCODE_WAKEUP]
    C -->|Yes| E[Force Stop WhatsApp]
    D --> E
    E --> F[Launch WhatsApp Main Activity]
    F --> G[Search Contact]
    G --> H[Type Name & Navigate]
    H --> I[Tap Voice Call Button via XML Dump]
    I --> J[Enable Speakerphone]
    J --> K[Enter Call Mode Bypass]
    K --> L[Record remote voice directly to LLM]
    L --> M[AI converses on phone line]
    M --> N[AI detects 'goodbye' & hangs up]
```

---

## 📸 Media & Demonstrations

### System Interface Screenshots

*Phase 1 Prototype that included a lightweight, functional GUI featuring real-time terminal logs, modular toggle controls and a core voice-activated AI listening loop.* <br>

<img src="assets/screenshot1.png" width="400" alt="Ghost HUD Interface">

---

*Ghost HUD: An Apple 'Dynamic Island'-inspired, frameless cyberpunk overlay summoned via global hotkey, featuring real-time screen awareness and voice-activated AI capabilities right at the top of your screen.* <br>

<img src="assets/screenshot2.png" width="400" alt="Terminal Output">

---

*Telegram Integration: A fully remote, Llama-powered mobile interface that puts the entire intelligence and automation power of Captain AI right in your pocket—ready to answer any question or execute system commands on the go.* <br>

<img src="assets/screenshot3.png" width="800" alt="Full System View">

### Video Demonstrations

*Gmail Automation Demo - Please click on the link given below* <br>

https://github.com/SaiSiddharthBS/Captain_AI/raw/main/assets/demo_gmail.mp4


---

## 📁 Project Structure

```text
Captain_AI/
├── bin/                        # System binaries (ffmpeg.exe, ffprobe.exe)
├── data/                       # Local JSON Storage (The Sovereign Data Doctrine)
│   ├── alarms.json             # Persistent alarms and timers
│   └── memory.json             # Persistent facts, preferences, and todos
├── media/                      # Music and Sound Assets
│   ├── cache/                  # MD5-hashed TTS WAV files
│   └── sounds/                 # System chimes and alerts
├── models/                     # AI Models Directory
│   ├── piper/                  # Piper TTS binaries and voice.onnx
│   └── models--Systran--faster-whisper-base/
├── src/                        # Core Application Source Code
│   ├── adb_tools.py            # Android automation
│   ├── alarm.py                # Alarm and timer logic
│   ├── brain.py                # Central intent routing engine
│   ├── config.py               # Path definitions
│   ├── gui.py                  # V7 Tkinter interface
│   ├── hud.py                  # V10 Ghost HUD overlay
│   ├── llm.py                  # Groq API + RAG context
│   ├── memory.py               # Local JSON read/write logic
│   ├── music.py                # Pygame audio controller
│   ├── server.py               # WebSocket daemon
│   ├── stt.py                  # Faster-Whisper + OpenWakeWord
│   ├── telegram_engine.py      # Secure remote control uplink
│   ├── tools.py                # OS Commands, DuckDuckGo, Wikipedia
│   ├── tts.py                  # Piper TTS wrapper
│   └── vision.py               # Screen capture & Ollama integration
├── tools/                      # Developer Utilities
│   ├── auto_info_ollama.py     # Silent Ollama installer
│   ├── downloader.py           # yt-dlp music scraper
│   └── make_chime.py           # Sine wave generator for alert chimes
├── website/                    # Static promotional frontend
├── config.json                 # User API keys and preferences
├── main.py                     # Entry point for V7 (GUI)
├── main_v10.py                 # Entry point for V10 (Ghost HUD + Server)
├── run_v2.bat                  # One-click startup script
└── setup_v2.py                 # Pre-requisite model downloader
```

---

## 🚀 Setup & Deployment

### Prerequisites
1. **Python 3.10+** installed and added to PATH.
2. **Android Platform Tools** (if using the ADB automation features).
3. **Groq API Key** (Free tier available).

### Installation Steps
1. Clone the repository to a local directory (e.g., `D:\Captain_AI`).
2. Open `config.json` and insert your API keys:
   ```json
   {
       "groq_api_key": "YOUR_API_KEY_HERE",
       "telegram_token": "YOUR_TELEGRAM_BOT_TOKEN_HERE"
   }
   ```
3. Run the installer:
   ```bash
   run_v2.bat
   ```
   *This batch script automatically creates a virtual environment, installs dependencies from `requirements.txt`, runs `setup_v2.py` to download the Piper TTS engine and models, and launches the app.*

4. To start the **V10 Ghost HUD** mode manually (decoupled server/UI):
   ```bash
   venv\Scripts\python main_v10.py
   ```
   *Use `Ctrl+Shift+Space` to summon the HUD.*

### Additional Setup
- Run `install_ffmpeg.py` if you wish to use the `download_music.bat` tool for converting YouTube videos into MP3s.
- Run `tools/install_ollama.py` to get Ollama for local vision processing (`moondream` model required).

---

## 🛡️ The Sovereign Data Doctrine (Privacy)

Captain AI operates under strict cryptographic isolation. 
- **Air-Gapped by Design**: There is absolutely **no telemetry**, analytics, or hidden data harvesting. 
- **Local Storage**: All interactions, to-do lists, alarms, and learned behavioral facts are stored as raw text in local JSON files (`data/memory.json`). You hold the keys. 
- **Modular AI**: By default, STT, TTS, and Wake Word detection run locally. The LLM utilizes the Groq Cloud API for speed, but you can swap it instantly to local Ollama models in the `src/llm.py` file.

<br>
<div align="center">
  <i>Captain AI Engineering Wing, 2026</i>
</div>
