# Jarvis V1

Cross-platform voice AI desktop assistant for **Windows**, **macOS**, and **Linux**.

Features: wake-word listening, NVIDIA chat + **vision UI control**, local face recognition (YuNet + SFace), mouse/keyboard automation, owner/guest roles, and offline command fallbacks.

**Repository:** https://github.com/robopup33/Jarvis-V1

---

## 1. Get Python

| Platform | Download |
|----------|----------|
| Windows | https://www.python.org/downloads/windows/ |
| macOS | https://www.python.org/downloads/macos/ |
| Linux | Use your package manager (see distro sections below) or https://www.python.org/downloads/source/ |

Install **Python 3.10+**. On Windows, check **“Add python.exe to PATH”**.

---

## 2. NVIDIA API key

1. Create an account at [https://build.nvidia.com/](https://build.nvidia.com/)
2. Generate an API key
3. Paste it into Jarvis when the setup wizard asks (stored securely via keyring)

---

## 3. Get the app

```bash
git clone https://github.com/robopup33/Jarvis-V1.git
cd Jarvis-V1
```

Place the full **`Jarvis.py`** in this folder (download from the project release / provided artifact if the repo only has the assembler).

Then:

```bash
python Jarvis.py
# or:  python3 Jarvis.py
```

On first run Jarvis installs missing packages (`opencv-python`, `pyttsx3`, `pyautogui`, `SpeechRecognition`, `sounddevice`, `cryptography`, etc.).

---

# Windows setup (step-by-step)

### Requirements
- Windows 10 or 11
- Python 3.10+ with PATH enabled
- Webcam (for face enrollment / verification)
- Microphone and speakers
- Internet (first run + NVIDIA API / vision)

### Steps
1. Install Python from https://www.python.org/downloads/windows/  
   - Enable **Add python.exe to PATH**  
   - Optionally install **py launcher**
2. Open **Command Prompt** or **PowerShell**:
   ```bat
   cd path\to\Jarvis-V1
   python -m pip install --upgrade pip
   python Jarvis.py
   ```
3. Allow Windows Firewall / Defender if prompted for Python network access.
4. When Windows asks for **microphone** or **camera** access for Python, click **Allow**.
5. Complete the setup wizard (assistant name, your name, **Owner vs Guest**, NVIDIA key).
6. Enroll your face (front / left / right). Prefer even lighting.
7. Say: **“Hey Jarvis”** (or your chosen assistant name), then give a command.

### Optional Windows tips
- Run as a normal user (admin only if you need certain shell commands).
- For media keys / volume, no extra install is required.
- Task Manager, Settings, Chrome, Edge, Notepad, Calculator are supported via `open_application`.
- If speech recognition is weak, check **Settings → Privacy → Microphone** and set the default input device.

### Troubleshooting (Windows)
| Problem | Fix |
|---------|-----|
| `python` not found | Reinstall Python with PATH, or use `py Jarvis.py` |
| No mic input | Privacy → Microphone → allow desktop apps |
| Camera black | Close other apps using the webcam; try Device Manager |
| pyautogui / clicks fail | Don’t leave the mouse in a screen corner (failsafe) |
| Vision / API errors | Check API key at build.nvidia.com; confirm internet |

---

# macOS setup (step-by-step)

Jarvis needs **explicit privacy permissions** on macOS. Without them, mouse, screenshots, and mic/camera will fail.

### Requirements
- macOS 12 Monterey or newer (Ventura / Sonoma / Sequoia recommended)
- Python 3.10+ (python.org installer **or** Homebrew)
- Webcam + microphone

### Install Python
**Option A — python.org (simple)**  
1. Download macOS installer: https://www.python.org/downloads/macos/  
2. Run the `.pkg`, then in Terminal:
   ```bash
   python3 --version
   ```

**Option B — Homebrew**
```bash
brew install python
python3 --version
```

### Grant permissions (required)

Open **System Settings → Privacy & Security** and allow the app you use to launch Jarvis (**Terminal**, **iTerm**, or **Python**):

1. **Microphone** — ON for Terminal/Python (speech / wake word)  
2. **Camera** — ON (face enrollment + verification)  
3. **Accessibility** — ON (mouse move/click, typing, hotkeys via pyautogui)  
4. **Screen Recording** — ON (screenshots + **vision_ui_act**)  

If a toggle is missing until first use: run `python3 Jarvis.py` once, click **OK** on system dialogs, then toggle the permission **On** and **restart Terminal**.

### Run
```bash
cd /path/to/Jarvis-V1
python3 -m pip install --upgrade pip
python3 Jarvis.py
```

### macOS tips
- Prefer **Terminal** or **iTerm** with permissions granted to that exact app.
- On Apple Silicon, use the universal/python.org build or `brew install python`.
- Chrome opens as **Google Chrome** (`open -a`); Safari is the default “browser” alias.
- Volume uses `osascript` (no extra package).
- Lock screen uses Control–Command–Q equivalent via system tools.

### Troubleshooting (macOS)
| Problem | Fix |
|---------|-----|
| Clicks do nothing | Enable **Accessibility** for Terminal/Python; quit and reopen Terminal |
| Screenshot / vision fails | Enable **Screen Recording**; restart Terminal |
| Mic not heard | **Microphone** permission; check input device in Sound settings |
| `python3` not found | Install from python.org or `brew install python` |
| Tk windows look odd | Normal on some macOS versions; functionality still works |

---

# Linux setup (all major distros)

Use **X11** for best mouse/keyboard automation. Wayland often blocks synthetic input.

### Common packages

You need: Python 3.10+, `pip`, Tk, PortAudio (mic), a webcam stack, and optionally `xdotool` / `scrot`.

---

### Ubuntu / Debian / Linux Mint / Pop!_OS

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-tk python3-venv \
  portaudio19-dev libasound2-dev \
  libopencv-dev \
  xdotool scrot gnome-screenshot \
  libnotify-bin pulseaudio-utils
```

Optional virtual environment:

```bash
cd /path/to/Jarvis-V1
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
python Jarvis.py
```

Session: on Ubuntu 22.04+, at login choose **Ubuntu on Xorg** if automation fails under Wayland.

---

### Fedora / RHEL / CentOS Stream

```bash
sudo dnf install -y python3 python3-pip python3-tkinter \
  portaudio-devel \
  xdotool scrot \
  libnotify pulseaudio-utils
```

```bash
cd /path/to/Jarvis-V1
python3 Jarvis.py
```

---

### Arch Linux / Manjaro / EndeavourOS

```bash
sudo pacman -S python python-pip tk portaudio \
  xdotool scrot libnotify
```

```bash
cd /path/to/Jarvis-V1
python Jarvis.py
```

---

### openSUSE

```bash
sudo zypper install python3 python3-pip python3-tk \
  portaudio-devel xdotool scrot libnotify-tools
```

---

### Linux Mint notes
Same as Ubuntu/Debian. Prefer the **X11** session from the login screen (gear icon) if clicks or screenshots fail.

---

### Linux tips (all distros)
- **Audio:** `pulseaudio` or `pipewire` with `pactl` for volume.
- **Notifications:** `notify-send` (`libnotify`).
- **Chrome:** package `google-chrome` or `chromium`; Jarvis maps `chrome` → `google-chrome` when available.
- **Permissions:** your user must be in groups that can access video/audio devices if the distro requires it, e.g.:
  ```bash
  sudo usermod -aG audio,video $USER
  ```
  Then log out and back in.
- First run downloads face ONNX models (~15MB) to `~/.jarvis_core/onnx_models/` (needs network once).

### Troubleshooting (Linux)
| Problem | Fix |
|---------|-----|
| ALSA / PortAudio errors | Install `portaudio19-dev` (Debian) or `portaudio-devel` (Fedora) |
| No mouse control | Use X11; install `xdotool`; don’t use pure Wayland without portals |
| Screenshot fails | Install `scrot` or `gnome-screenshot` |
| `tkinter` missing | Install `python3-tk` / `python3-tkinter` |
| Camera permission | Check `ls /dev/video0`; groups `video` |

---

## First-run checklist (every OS)

1. Enter **NVIDIA API key** in the wizard  
2. Choose **Owner** (full control) or **Guest** (limited)  
3. Enroll face (3 poses) — re-enroll after updates for neural embeddings  
4. Allow mic + camera when the OS asks  
5. Test: “Hey Jarvis, what time is it?”  
6. Online multi-step example: “Say hello, then open YouTube”  
7. UI click example (owner, online): “Click the search box” → uses **vision_ui_act**

---

## Security notes

- **Terminate Jarvis**, **folder protect**, **system power**, **mouse**, and **vision_ui_act** are **owner** tools (face checks where configured).  
- Folder protection encrypts Desktop / Documents / Downloads only — not the OS. Save the recovery password offline.  
- Unknown faces on shutdown attempts get a warning + screen lock (not full-disk encryption).

---

## License

Educational / personal use. Use at your own risk.
