# Jarvis V1

Cross-platform voice AI desktop assistant (Windows, **macOS**, **Linux**) with local face recognition, NVIDIA LLM tools, vision-guided UI clicks, and owner/guest roles.

## Quick start

```bash
git clone https://github.com/robopup33/Jarvis-V1.git
cd Jarvis-V1
python Jarvis.py
```

**Python:** [Windows](https://www.python.org/downloads/windows/) · [macOS](https://www.python.org/downloads/macos/) · [Linux](https://www.python.org/downloads/source/)

**NVIDIA API key:** [https://build.nvidia.com/](https://build.nvidia.com/)

## Features

- Wake-word listening and NVIDIA chat models (tool calling, multi-step actions)
- **Vision UI control** — `vision_ui_act` screenshots the desktop, sends it to NVIDIA vision models (`meta/llama-3.2-90b-vision-instruct`, etc.), and performs clicks/typing
- Mouse move/click/drag/scroll (pyautogui) on Windows, macOS, and Linux
- Local face recognition: YuNet + SFace ONNX (CPU) with Haar fallback
- Owner / Guest roles; face-gated shutdown and folder protection
- Volume, media keys, screenshots, hotkeys, folders, URLs, power actions
- Offline command subset when the network is down

## Platform notes

| Area | Windows | macOS | Linux |
|------|---------|-------|-------|
| Mouse / type / hotkeys | pyautogui | pyautogui (+ Accessibility permission) | pyautogui / xdotool (X11) |
| Screenshots | pyautogui / PowerShell | screencapture | gnome-screenshot / scrot / ImageMagick |
| Volume | Win APIs | osascript | pactl |
| Apps | startfile | `open -a` | PATH / gtk-launch |

On **macOS**, grant Accessibility + Screen Recording to Terminal/Python for mouse and screenshots.  
On **Linux**, use an X11 session for best automation; install `xdotool` and `scrot` if needed.

## Hardware

Works on **CPU-only, 16GB RAM** laptops (e.g. Dell Latitude). Face models ~15MB once downloaded to `~/.jarvis_core/onnx_models/`.

## License

Educational / personal use. Use at your own risk.

https://github.com/robopup33/Jarvis-V1
