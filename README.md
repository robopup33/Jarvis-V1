# Jarvis V1

**Jarvis V1** is a voice-activated AI desktop assistant with cross-platform improvements, facial recognition, and owner/guest access control.

> **Note**: Best experience is on **Windows**. macOS and Linux are supported for core features.

## Features

- Wake-word listening (“Hey [Assistant Name]”)
- Conversational AI via NVIDIA API
- Tool calling with **role-based restrictions**
- Offline fallback mode
- Facial enrollment + live recognition (OpenCV)
- **Owner / Guest roles** (guests have limited tools)
- **Non-blocking startup** auto-identification
- **Face-gated shutdown**; unknown faces get a warning + screen lock
- New profiles require **owner face** verification
- Desktop shortcut auto-creation
- Triton audio cue and status states

## Owner vs Guest

| Capability | Owner | Guest |
|------------|-------|-------|
| Run shell commands | Yes | No |
| Shut down Jarvis | Yes (face required) | No |
| Open apps | Any | Basic only (notepad, calculator, paint) |
| Lock screen / status | Yes | Yes |
| Add new profiles | Yes (face required) | No |

## Shutdown / security behavior

When someone asks Jarvis to shut down:
1. Jarvis says it is **authenticating** and checks the camera.
2. **Owner face match** → clean exit.
3. **Guest / limited** → “You do not have permission to do this.”
4. **Unknown face** → warning to step away + **workstation screen lock** (not full-disk encryption).

> Jarvis does **not** enable BitLocker or encrypt your files with a hidden password. That would risk permanent data loss if face recognition failed. Screen lock + role limits are used instead.

## Installation

```bash
git clone https://github.com/robopup33/Jarvis-V1.git
cd Jarvis-V1
python Jarvis.py
```

Python downloads: [Windows](https://www.python.org/downloads/windows/) · [macOS](https://www.python.org/downloads/macos/) · [Linux](https://www.python.org/downloads/source/)

NVIDIA API key: [https://build.nvidia.com/](https://build.nvidia.com/)

## License

Educational / personal use. Use at your own risk.

**Repo**: https://github.com/robopup33/Jarvis-V1
