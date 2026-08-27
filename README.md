# Jarvis V1

**Jarvis V1** is a voice-activated AI desktop assistant with cross-platform improvements. It features wake-word detection, speech recognition, local TTS, NVIDIA-hosted LLM tool calling, offline fallbacks, face enrollment, and system control tools.

> **Note**: Best experience is on **Windows**. macOS and Linux are supported for core features (voice, API, basic tools), but some system actions and voice engines vary by platform.

## Features

- Wake-word listening (“Hey [Assistant Name]”)
- Conversational AI via NVIDIA API (with automatic model rotation)
- Tool calling: run commands, lock screen, open apps, get system status, terminate Jarvis
- Offline fallback mode (time, date, lock, open, basic greetings) when internet or API is unavailable
- Facial enrollment + live face verification (OpenCV Haar detection + multi-view template matching)
- Re-enroll face from Settings; identity check on startup
- Configurable assistant name, user name, voice accent (UK/US), pronouns, and system voice
- Desktop shortcut auto-creation (Windows / macOS / Linux)
- “Triton” audio click cue and status states (Listening → Thinking → Writing response)
- Interruption support for overlapping voice commands
- Secure-ish API key storage (system keyring + encrypted fallback)
- Cannot be closed via the window X (only via explicit “terminate / shut down” command)

## Requirements

- Python 3.9+ (3.10+ recommended)
- Webcam (for face enrollment and verification)
- Microphone + speakers
- NVIDIA API key (free credits available on first signup)
- Internet connection (for full AI responses; offline mode still works for basic commands)

### Download Python

| Platform   | Official Download |
|------------|-------------------|
| **Windows** | [https://www.python.org/downloads/windows/](https://www.python.org/downloads/windows/) |
| **macOS**   | [https://www.python.org/downloads/macos/](https://www.python.org/downloads/macos/) |
| **Linux**   | [https://www.python.org/downloads/source/](https://www.python.org/downloads/source/) or your package manager (`sudo apt install python3 python3-pip python3-tk` on Debian/Ubuntu, etc.) |

**Windows tip**: Check **“Add python.exe to PATH”** during install.

### Get an NVIDIA API Key

1. Visit **[https://build.nvidia.com/](https://build.nvidia.com/)** and sign in / create a free NVIDIA Developer account.
2. Go to API Keys / Manage API Keys (or open any model and generate a key).
3. Create a key (it starts with `nvapi-`).
4. Copy it immediately — you will paste it into the Jarvis setup wizard.

## Installation & First Run

```bash
git clone https://github.com/robopup33/Jarvis-V1.git
cd Jarvis-V1
```

Optional virtual environment:

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

Run:

```bash
python Jarvis.py
```

On first launch the configuration wizard appears. Enter assistant name, your name, accent, pronouns, and NVIDIA API key. Then complete face enrollment (3 poses). On every subsequent start, a live face verification window confirms your identity.

Speak: **“Hey Jarvis”** (or your chosen name).

## Face recognition

- Uses OpenCV Haar cascades (no extra packages beyond opencv-python)
- Enrollment captures front / left / right and stores normalized face templates
- Startup verification matches the live camera feed against your templates
- Threshold ~55% combined histogram + template similarity
- “Skip (limited)” is available if verification fails; use **Settings → Re-enroll Face Profile** to update templates
- Templates are stored under `~/.jarvis_core/face_models/`

## How to Use

- Wake with **“Hey [Assistant Name]”**
- Give spoken commands or questions
- Explicitly request actions for tools (e.g. “lock the computer”, “open notepad”, “what time is it”)
- Use the ⚙ gear to change voice, re-enroll face, or reconfigure
- To quit: say something like “shut down” / “terminate Jarvis”

### Tools available via natural language

- `run_command` – execute a shell command
- `lock_computer` – lock the screen (Windows / macOS / Linux)
- `open_application` – launch an app by name
- `get_system_status` – username, platform, time
- `terminate_jarvis` – cleanly exit the assistant

## Configuration files

Stored under `~/.jarvis_core/`:

- `jarvis_settings.json`
- `jarvis_users.json` (enrollment photos)
- `face_models/` (normalized face templates for recognition)
- `jarvis_model_usage.json`
- `jarvis_sec.key`
- `jarvis_close.lock`

## Security notes

- `run_command` can execute arbitrary commands — use carefully.
- Face matching is a convenience biometric, not bank-grade security.
- API key is stored via the OS keyring when possible.
- Never commit or share the contents of `~/.jarvis_core/`.

## Troubleshooting

```bash
pip install opencv-python pillow keyring sounddevice numpy SpeechRecognition pyttsx3
```
On Windows also: `pip install pywin32`

- Grant camera + microphone permissions.
- For best face recognition: good lighting, face the camera, avoid heavy glasses glare.
- If verification always fails, use **Re-enroll Face Profile** in Settings.

## License

Released as-is for educational and personal use. Use at your own risk.

---

**Repository**: [https://github.com/robopup33/Jarvis-V1](https://github.com/robopup33/Jarvis-V1)
