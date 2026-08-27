# Jarvis V1

**Jarvis V1** is a voice-activated AI desktop assistant for Windows (with limited support notes for other platforms). It features:

- Wake-word detection ("Hey Jarvis" or custom name)
- Speech recognition and local text-to-speech
- NVIDIA-hosted LLM integration with tool calling
- Facial enrollment (stores profile photos)
- Laptop control tools (run commands, lock screen, system status)
- Simple animated UI and setup wizard

> **Important**: This project is primarily designed for **Windows**. Many features (screen lock, some voice engines, process flags, pywin32) are Windows-specific. On macOS/Linux, core voice and API features may work with modifications, but full functionality is not guaranteed.

## Features

- Voice wake-word listening
- Conversational AI via NVIDIA API (DeepSeek / Nemotron models)
- Tool use: run shell commands, lock workstation, get system status, shut down the assistant
- Secure-ish storage of NVIDIA API key (Windows Credential Manager / keyring + fallback)
- Face profile enrollment (front / left / right photos)
- Configurable assistant name, user name, and voice accent (UK / US)
- Auto-installs missing Python dependencies on first run

## Requirements

- Python 3.9 or newer (3.10+ recommended)
- Webcam (for face enrollment)
- Microphone
- Speakers / headphones
- NVIDIA API key (free credits available)
- Internet connection

### Download Python

If you don’t already have Python installed:

| Platform | Official Download |
|----------|-------------------|
| **Windows** | [https://www.python.org/downloads/windows/](https://www.python.org/downloads/windows/) |
| **macOS**   | [https://www.python.org/downloads/macos/](https://www.python.org/downloads/macos/) |
| **Linux**   | [https://www.python.org/downloads/source/](https://www.python.org/downloads/source/) or use your distro’s package manager (`sudo apt install python3 python3-pip python3-tk` on Debian/Ubuntu, etc.) |

**Windows tip**: During installation, check the box **“Add python.exe to PATH”**.

### Get an NVIDIA API Key

1. Go to **[https://build.nvidia.com/](https://build.nvidia.com/)** and sign in (or create a free NVIDIA Developer account).
2. Open any model or go to API Keys / Manage API Keys.
3. Generate a new key (it starts with `nvapi-`).
4. Copy it immediately — you will paste it into the Jarvis setup wizard.

More details: [NVIDIA API Catalog / build.nvidia.com](https://build.nvidia.com/)

## Installation & First Run

1. Clone or download this repository:
   ```bash
   git clone https://github.com/robopup33/Jarvis-V1.git
   cd Jarvis-V1
   ```

2. (Optional but recommended) Create a virtual environment:
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS / Linux
   source venv/bin/activate
   ```

3. Run the assistant:
   ```bash
   python jarvis.py
   ```

4. On first launch:
   - The setup wizard appears.
   - Enter:
     - Assistant Name (default: Jarvis)
     - Your Preferred Name
     - Voice Accent (UK or US)
     - Your NVIDIA API Key
   - Click **Save & Launch**.

5. If your face profile is not enrolled, a camera window will open. Follow the on-screen instructions to capture front, left, and right views.

6. Speak the wake phrase: **“Hey Jarvis”** (or whatever name you chose).

## How to Use

- Say **“Hey [Assistant Name]”** to wake it.
- Give a spoken command or question.
- The assistant responds with voice and can optionally execute tools if you explicitly request actions (e.g. “lock the computer”, “run dir”, etc.).
- Press **F11** for fullscreen, **Escape** to exit fullscreen.
- Use the ⚙ gear icon to open settings (add users, reconfigure).

### Available Tools (via natural language)

- Run a Windows command / PowerShell command
- Lock the computer
- Get system status (username, time)
- Terminate / shut down Jarvis (only when you clearly request it)

## Configuration Files

All settings and data are stored in:

```
~/.jarvis_core/
├── jarvis_settings.json
├── jarvis_users.json          # face profile photos (base64)
├── jarvis_model_usage.json    # daily model rotation tracking
└── jarvis_sec.key             # fallback encrypted key storage
```

## Security Notes

- The `run_command` tool can execute arbitrary shell commands. Use responsibly.
- Your NVIDIA API key is stored via the system keyring when possible.
- Face data is stored as JPEG images encoded in base64 — this is **not** a full face-recognition system; it simply saves enrollment photos.
- Never share your API key or the contents of `~/.jarvis_core/`.

## Troubleshooting

- **Missing packages**: The script tries to auto-install common dependencies. If it fails, run:
  ```bash
  pip install opencv-python pillow keyring sounddevice numpy SpeechRecognition pyttsx3
  ```
  On Windows also: `pip install pywin32`

- **No microphone / camera**: Grant permissions in your OS privacy settings.

- **TTS voice not matching accent**: Install additional system voices or change the accent preference in settings.

- **API errors**: Verify your NVIDIA API key and that you still have free credits / rate-limit headroom.

## License

This project is released as-is for educational and personal use. Use at your own risk.

---

**Repository**: [https://github.com/robopup33/Jarvis-V1](https://github.com/robopup33/Jarvis-V1)
