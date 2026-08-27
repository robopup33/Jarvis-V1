# Jarvis V1

Voice-activated AI desktop assistant with **local neural face recognition** (YuNet + SFace ONNX on CPU), owner/guest roles, NVIDIA LLM tools, and optional folder protection.

## Quick start

```bash
git clone https://github.com/robopup33/Jarvis-V1.git
cd Jarvis-V1
python Jarvis.py
```

**Python:** [Windows](https://www.python.org/downloads/windows/) · [macOS](https://www.python.org/downloads/macos/) · [Linux](https://www.python.org/downloads/source/)

**NVIDIA API key:** [https://build.nvidia.com/](https://build.nvidia.com/)

## Features

- Wake-word + NVIDIA chat models
- **Local face recognition** — downloads YuNet + SFace (~15MB) once to `~/.jarvis_core/onnx_models/` (CPU-friendly; Haar fallback)
- Owner / Guest roles
- Non-blocking startup auto-identify
- Face-gated shutdown; unknown face → warning + screen lock
- Optional owner-only encrypt of Desktop/Documents/Downloads (not Windows)
- Offline command fallbacks

## Hardware notes

Tested design target: **CPU-only, 16GB RAM** (e.g. Dell Latitude 7440). No GPU required for face models.

## License

Educational / personal use. Use at your own risk.

https://github.com/robopup33/Jarvis-V1
