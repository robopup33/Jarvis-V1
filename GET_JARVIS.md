# Get the full Jarvis.py

The complete assistant is large (~157KB).

## What's in this build

- **NVIDIA vision UI** (`vision_ui_act`): screenshot to vision model via API key to automatic clicks/typing
- Multi-step tool chains (up to 8 rounds)
- Mouse control via pyautogui (Windows, macOS, Linux)
- Local YuNet+SFace face recognition (CPU)
- Owner/guest roles and expanded PC tools

## macOS

Grant Accessibility and Screen Recording to Terminal/Python.

## Linux

Prefer X11. Optional: `sudo apt install xdotool scrot`

Run the validated `Jarvis.py` from the project release artifact, then:

```bash
python Jarvis.py
```
