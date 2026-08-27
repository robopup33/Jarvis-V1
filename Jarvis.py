import os
import sys
import json
import threading
import time
import subprocess
import base64
import getpass
import hashlib
import re
import urllib.request
import urllib.error
import traceback
import socket

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".jarvis_core")
os.makedirs(CONFIG_DIR, exist_ok=True)
CRASH_LOG_FILE = os.path.join(CONFIG_DIR, "jarvis_crash.log")
LOCK_FILE = os.path.join(CONFIG_DIR, "jarvis_close.lock")

if __name__ == "__main__":
    try:
        def check_dependencies():
            required = {
                "cv2": "opencv-python", 
                "PIL": "pillow", 
                "keyring": "keyring",
                "sounddevice": "sounddevice",
                "numpy": "numpy",
                "speech_recognition": "SpeechRecognition",
                "pyttsx3": "pyttsx3"
            }
            if sys.platform == 'win32':
                required["pythoncom"] = "pywin32"
            
            for mod, pkg in required.items():
                try:
                    __import__(mod)
                except ImportError:
                    print(f"Installing missing dependency: {pkg}...")
                    subprocess.run([sys.executable, "-m", "pip", "install", pkg], check=False, shell=False)

        print("Checking dependencies...")
        check_dependencies()

        print("Importing core modules...")
        import cv2
        import numpy as np
        from PIL import Image, ImageTk
        import tkinter as tk
        from tkinter import messagebox, simpledialog, ttk
        import keyring
        import sounddevice as sd
        import speech_recognition as sr
        import pyttsx3

        pythoncom = None
        if sys.platform == 'win32':
            try:
                import pythoncom
            except Exception:
                pass

        SETTINGS_FILE = os.path.join(CONFIG_DIR, "jarvis_settings.json")
        USERS_FILE = os.path.join(CONFIG_DIR, "jarvis_users.json")
        USAGE_FILE = os.path.join(CONFIG_DIR, "jarvis_model_usage.json")
        FALLBACK_KEY_FILE = os.path.join(CONFIG_DIR, "jarvis_sec.key")

        USER_HASH = hashlib.sha256(getpass.getuser().encode('utf-8')).hexdigest()[:12]
        KEYRING_SERVICE_NAME = f"JarvisAssistantCore_{USER_HASH}"

        CAMERA_ACCESS_LOCK = threading.Lock()
        JSON_ACCESS_LOCK = threading.Lock()
        TTS_LOCK = threading.Lock()

        MODEL_CANDIDATES = [
            "deepseek-ai/deepseek-v4-flash-0731",
            "nvidia/nemotron-3.5-lightning-30b-a3b"
        ]

        def is_internet_available():
            try:
                socket.create_connection(("8.8.8.8", 53), timeout=2)
                return True
            except OSError:
                return False

        # ==================== CROSS-PLATFORM SYSTEM & OFFLINE TOOLS ====================
        def run_command(command: str) -> str:
            """Executes a system shell script or command on the host machine and returns output."""
            try:
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=15)
                output = result.stdout + "\n" + result.stderr
                return output.strip() or "Command executed successfully with no output."
            except Exception as e:
                return f"Error executing command: {e}"

        def lock_computer() -> str:
            """Locks the workstation screen immediately for security across platforms."""
            try:
                if sys.platform == 'win32':
                    import ctypes
                    ctypes.windll.user32.LockWorkStation()
                elif sys.platform == 'darwin':
                    subprocess.run(["osascript", "-e", 'tell application "System Events" to key code 12 using {control down, command down}'], check=False)
                else:
                    # Try common Linux lock methods
                    for cmd in (["loginctl", "lock-session"], ["xdg-screensaver", "lock"], ["gnome-screensaver-command", "-l"]):
                        try:
                            subprocess.run(cmd, check=False, timeout=5)
                            break
                        except Exception:
                            continue
                return "Workstation locked successfully."
            except Exception as e:
                return f"Error locking screen: {e}"

        def get_system_status() -> str:
            """Returns current system username, platform, and local system time."""
            return f"Current user: {getpass.getuser()}, OS: {sys.platform}, Time: {time.ctime()}"

        def open_application(app_name: str) -> str:
            """Opens a local application cross-platform by name."""
            try:
                app_lower = app_name.lower().strip()
                if sys.platform == 'win32':
                    shortcuts = {"notepad": "notepad.exe", "calculator": "calc.exe", "paint": "mspaint.exe", "cmd": "cmd.exe", "settings": "ms-settings:"}
                    target = shortcuts.get(app_lower, app_name)
                    os.startfile(target)
                elif sys.platform == 'darwin':
                    subprocess.run(["open", "-a", app_name], check=False)
                else:
                    subprocess.run(["xdg-open", app_name], check=False)
                return f"Successfully launched {app_name}."
            except Exception as e:
                return f"Failed to open {app_name}: {e}"

        def terminate_jarvis() -> str:
            """Authorized command for Jarvis to shut down completely when explicitly requested."""
            if os.path.exists(LOCK_FILE):
                try:
                    os.remove(LOCK_FILE)
                except Exception:
                    pass
            def delayed_exit():
                time.sleep(0.3)
                os._exit(0)
            threading.Thread(target=delayed_exit, daemon=True).start()
            return "Jarvis core shutting down safely."

        TOOLS = [
            {
                "type": "function",
                "function": {
                    "name": "run_command",
                    "description": "Executes a shell script or command on the host machine and returns output.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "The command to execute."}
                        },
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "lock_computer",
                    "description": "Locks the workstation screen immediately.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_system_status",
                    "description": "Returns current system username, platform, and local system time.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "open_application",
                    "description": "Opens a local application by name.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "app_name": {"type": "string", "description": "Name of the application to launch."}
                        },
                        "required": ["app_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "terminate_jarvis",
                    "description": "Permanently terminates and closes Jarvis.",
                    "parameters": {"type": "object", "properties": {}}
                }
            }
        ]

        def execute_tool(name, arguments):
            if name == "run_command":
                return run_command(arguments.get("command", ""))
            elif name == "lock_computer":
                return lock_computer()
            elif name == "get_system_status":
                return get_system_status()
            elif name == "open_application":
                return open_application(arguments.get("app_name", ""))
            elif name == "terminate_jarvis":
                return terminate_jarvis()
            return "Unknown tool executed."

        def handle_offline_command(text, user_name, assistant_name):
            t = text.lower()
            if any(k in t for k in ["time", "what time"]):
                return f"Offline mode: The current time is {time.strftime('%I:%M %p')}."
            elif any(k in t for k in ["date", "what day", "today"]):
                return f"Offline mode: Today's date is {time.strftime('%A, %B %d, %Y')}."
            elif "lock" in t:
                return lock_computer()
            elif "system status" in t or "status" in t:
                return get_system_status()
            elif "open" in t:
                parts = t.split("open", 1)
                if len(parts) > 1:
                    return open_application(parts[1].strip())
            elif any(k in t for k in ["exit", "shut down", "terminate"]):
                return terminate_jarvis()
            elif any(k in t for k in ["hello", "hi", "hey"]):
                return f"Hello {user_name}. Offline fallback active."
            return f"Offline mode: Server unavailable, but system status is normal, {user_name}."

        # ==================== AUDIO EFFECTS & TRITON CLICK ====================
        def play_triton_echo_click():
            """Generates and plays a U.S.S. Triton echoing click audio cue programmatically."""
            try:
                sample_rate = 22050
                duration = 0.08
                t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
                # Frequency sweep with echoing decay envelope
                frequency = 1800 - (t * 5000)
                wave_data = np.sin(2 * np.pi * frequency * t) * np.exp(-t * 25)
                # Echo bounce
                echo_delay = int(sample_rate * 0.025)
                if len(wave_data) > echo_delay:
                    wave_data[echo_delay:] += wave_data[:-echo_delay] * 0.4
                audio = (wave_data * 32767).astype(np.int16)
                sd.play(audio, sample_rate)
            except Exception:
                pass

        def play_wake_beep():
            try:
                if sys.platform == 'win32':
                    import winsound
                    winsound.Beep(800, 50)
                    winsound.Beep(1200, 70)
                else:
                    play_triton_echo_click()
            except Exception:
                pass

        # ==================== SECURITY & STORAGE ====================
        def get_secure_fallback_key():
            machine_id = getpass.getuser() + os.environ.get("COMPUTERNAME", os.environ.get("HOSTNAME", "secure_host"))
            return hashlib.sha256(machine_id.encode('utf-8')).digest()[:32]

        def secure_store_password(service, key_name, password):
            try:
                keyring.set_password(service, key_name, password)
                return
            except Exception:
                pass
            try:
                data = {}
                if os.path.exists(FALLBACK_KEY_FILE):
                    with open(FALLBACK_KEY_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                raw_key = get_secure_fallback_key()
                encrypted = "".join(chr(ord(c) ^ raw_key[i % len(raw_key)]) for i, c in enumerate(password))
                data[key_name] = base64.b64encode(encrypted.encode('utf-8')).decode('utf-8')
                with open(FALLBACK_KEY_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f)
            except Exception:
                pass

        def secure_get_password(service, key_name):
            try:
                val = keyring.get_password(service, key_name)
                if val:
                    return val
            except Exception:
                pass
            try:
                if os.path.exists(FALLBACK_KEY_FILE):
                    with open(FALLBACK_KEY_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if key_name in data:
                        enc_bytes = base64.b64decode(data[key_name].encode('utf-8')).decode('utf-8')
                        raw_key = get_secure_fallback_key()
                        return "".join(chr(ord(c) ^ raw_key[i % len(raw_key)]) for i, c in enumerate(enc_bytes))
            except Exception:
                pass
            return ""

        def load_json(filename, default):
            with JSON_ACCESS_LOCK:
                if os.path.exists(filename):
                    for _ in range(3):
                        try:
                            with open(filename, "r", encoding="utf-8") as f:
                                return json.load(f)
                        except Exception:
                            time.sleep(0.02)
                return default

        def save_json(filename, data):
            with JSON_ACCESS_LOCK:
                for attempt in range(5):
                    try:
                        with open(filename, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=4)
                            f.flush()
                            os.fsync(f.fileno())
                        return
                    except Exception:
                        time.sleep(0.1 * (attempt + 1))

        def setup_desktop_shortcut_and_icon():
            """Cross-platform automated desktop shortcut placement and icon setup."""
            try:
                script_path = os.path.abspath(sys.argv[0])
                desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
                if not os.path.exists(desktop_dir):
                    return

                if sys.platform == 'win32':
                    shortcut_path = os.path.join(desktop_dir, "JarvisAssistant.lnk")
                    if not os.path.exists(shortcut_path):
                        from win32com.client import Dispatch
                        shell = Dispatch('WScript.Shell')
                        shortcut = shell.CreateShortcut(shortcut_path)
                        shortcut.TargetPath = sys.executable
                        shortcut.Arguments = f'"{script_path}"'
                        shortcut.WorkingDirectory = os.path.dirname(script_path)
                        shortcut.save()
                elif sys.platform == 'darwin':
                    alias_path = os.path.join(desktop_dir, "JarvisAssistant.command")
                    if not os.path.exists(alias_path):
                        with open(alias_path, "w") as f:
                            f.write(f'#!/bin/bash\ncd "{os.path.dirname(script_path)}"\n"{sys.executable}" "{script_path}"\n')
                        os.chmod(alias_path, 0o755)
                else:
                    desktop_file = os.path.join(desktop_dir, "jarvis_assistant.desktop")
                    if not os.path.exists(desktop_file):
                        with open(desktop_file, "w") as f:
                            f.write(f"[Desktop Entry]\nType=Application\nName=Jarvis Assistant\nExec={sys.executable} {script_path}\nTerminal=false\n")
                        os.chmod(desktop_file, 0o755)
            except Exception:
                pass

        setup_desktop_shortcut_and_icon()

        def get_available_models():
            today = time.strftime("%Y-%m-%d")
            usage_data = load_json(USAGE_FILE, {})
            if usage_data.get("date") != today:
                return MODEL_CANDIDATES
            available = [m for m in MODEL_CANDIDATES if m not in usage_data.get("used_models", [])]
            if not available:
                # Reset daily usage when all models have been tried
                usage_data = {"date": today, "used_models": []}
                save_json(USAGE_FILE, usage_data)
                return MODEL_CANDIDATES
            return available

        def mark_model_used(model_name):
            today = time.strftime("%Y-%m-%d")
            usage_data = load_json(USAGE_FILE, {"date": today, "used_models": []})
            if usage_data.get("date") != today:
                usage_data = {"date": today, "used_models": []}
            if model_name not in usage_data["used_models"]:
                usage_data["used_models"].append(model_name)
                save_json(USAGE_FILE, usage_data)

        def clean_response_text(raw_text):
            if not raw_text:
                return ""
            text = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'\[thought\].*?\[/thought\]', '', text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
            return text.strip()

        def call_nvidia_api(messages_list, system_instruction=""):
            nvidia_key = secure_get_password(KEYRING_SERVICE_NAME, "nvidia_api_key")
            if not nvidia_key:
                return "NVIDIA API key is missing."

            url = "https://integrate.api.nvidia.com/v1/chat/completions"
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {nvidia_key}"}

            for model_name in get_available_models():
                payload_messages = []
                if system_instruction:
                    payload_messages.append({"role": "system", "content": system_instruction})
                payload_messages.extend(messages_list)
                
                payload = {
                    "model": model_name,
                    "messages": payload_messages,
                    "tools": TOOLS,
                    "tool_choice": "auto",
                    "temperature": 0.3,
                    "max_tokens": 300
                }
                try:
                    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method="POST")
                    with urllib.request.urlopen(req, timeout=30) as response:
                        res_data = json.loads(response.read().decode('utf-8'))
                        message = res_data['choices'][0]['message']
                        
                        if "tool_calls" in message and message["tool_calls"]:
                            working_messages = list(payload_messages)
                            working_messages.append(message)
                            for tool_call in message["tool_calls"]:
                                func_name = tool_call["function"]["name"]
                                func_args = json.loads(tool_call["function"]["arguments"])
                                tool_output = execute_tool(func_name, func_args)
                                working_messages.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call["id"],
                                    "content": str(tool_output)
                                })
                            payload["messages"] = working_messages
                            req2 = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method="POST")
                            with urllib.request.urlopen(req2, timeout=30) as resp2:
                                res_data2 = json.loads(resp2.read().decode('utf-8'))
                                content = res_data2['choices'][0]['message']['content']
                                mark_model_used(model_name)
                                return clean_response_text(content)
                        else:
                            content = message.get('content', 'Command processed.')
                            mark_model_used(model_name)
                            return clean_response_text(content)
                except Exception:
                    continue
            return "I encountered a communication timeout with the API."

        class SetupWizard(tk.Tk):
            def __init__(self, existing_settings=None):
                super().__init__()
                self.title("Assistant Configuration Setup")
                self.geometry("450x490")
                self.config(bg="#0b0f19")
                self.result = None
                
                self.update_idletasks()
                x = (self.winfo_screenwidth() // 2) - (450 // 2)
                y = (self.winfo_screenheight() // 2) - (490 // 2)
                self.geometry(f"450x490+{x}+{y}")

                saved_nvidia = secure_get_password(KEYRING_SERVICE_NAME, "nvidia_api_key")
                self.existing = existing_settings or {}
                existing = self.existing
                
                tk.Label(self, text="CONFIGURATION SETUP", fg="#00ffcc", bg="#0b0f19", font=("Segoe UI", 14, "bold")).pack(pady=(15, 10))
                
                form_frame = tk.Frame(self, bg="#111827", bd=1, relief="solid")
                form_frame.pack(padx=20, pady=5, fill="both", expand=True)

                self.entries = {}
                
                tk.Label(form_frame, text="Assistant Name:", fg="#e5e7eb", bg="#111827", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=15, pady=(4, 1))
                ent_asst = tk.Entry(form_frame, width=38, font=("Segoe UI", 9), bg="#1f2937", fg="#ffffff", insertbackground="white")
                ent_asst.insert(0, existing.get("assistant_name", "Jarvis"))
                ent_asst.pack(anchor="w", padx=15, pady=(0, 3))
                self.entries["Assistant Name:"] = ent_asst

                tk.Label(form_frame, text="Your Preferred Name:", fg="#e5e7eb", bg="#111827", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=15, pady=(4, 1))
                ent_user = tk.Entry(form_frame, width=38, font=("Segoe UI", 9), bg="#1f2937", fg="#ffffff", insertbackground="white")
                ent_user.insert(0, existing.get("user_name", "Braden"))
                ent_user.pack(anchor="w", padx=15, pady=(0, 3))
                self.entries["Your Preferred Name:"] = ent_user

                tk.Label(form_frame, text="Voice Accent:", fg="#e5e7eb", bg="#111827", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=15, pady=(4, 1))
                accent_combo = ttk.Combobox(form_frame, values=["UK", "US"], width=35, state="readonly", font=("Segoe UI", 9))
                accent_combo.set(existing.get("voice_accent", "UK"))
                accent_combo.pack(anchor="w", padx=15, pady=(0, 3))
                self.entries["Voice Accent:"] = accent_combo

                tk.Label(form_frame, text="Pronouns:", fg="#e5e7eb", bg="#111827", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=15, pady=(4, 1))
                pronouns_combo = ttk.Combobox(form_frame, values=["He/Him", "She/Her", "They/Them", "Other"], width=35, state="readonly", font=("Segoe UI", 9))
                pronouns_combo.set(existing.get("pronouns", "He/Him"))
                pronouns_combo.pack(anchor="w", padx=15, pady=(0, 3))
                self.entries["Pronouns:"] = pronouns_combo

                tk.Label(form_frame, text="NVIDIA API Key:", fg="#e5e7eb", bg="#111827", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=15, pady=(4, 1))
                ent_key = tk.Entry(form_frame, width=38, font=("Segoe UI", 9), bg="#1f2937", fg="#ffffff", insertbackground="white", show="*")
                ent_key.insert(0, saved_nvidia)
                ent_key.pack(anchor="w", padx=15, pady=(0, 3))
                self.entries["NVIDIA API Key:"] = ent_key

                tk.Button(self, text="Save & Launch", command=self.on_save, bg="#00ffcc", fg="#0b0f19", font=("Segoe UI", 10, "bold"), width=20, height=2, bd=0, cursor="hand2").pack(pady=10)

            def on_save(self):
                nvidia_key = self.entries["NVIDIA API Key:"].get().strip()
                if not nvidia_key:
                    messagebox.showerror("Error", "An NVIDIA API Key is required.")
                    return
                secure_store_password(KEYRING_SERVICE_NAME, "nvidia_api_key", nvidia_key)
                self.result = {
                    "assistant_name": self.entries["Assistant Name:"].get().strip() or "Jarvis",
                    "user_name": self.entries["Your Preferred Name:"].get().strip() or "Braden",
                    "voice_accent": self.entries["Voice Accent:"].get().strip() or "UK",
                    "pronouns": self.entries["Pronouns:"].get().strip() or "He/Him",
                    "selected_voice": self.existing.get("selected_voice", "")
                }
                self.destroy()

        class FaceEnrollmentWindow(tk.Toplevel):
            def __init__(self, parent, user_name):
                super().__init__(parent)
                self.title(f"Facial Enrollment - {user_name}")
                self.geometry("400x480")
                self.config(bg="#0b0f19")
                self.user_name = user_name
                self.captured_images = {}
                self.photo = None
                self.preview_job = None
                self.current_frame = None
                self.frame_lock = threading.Lock()
                self.cap = None
                self.is_active = True
                
                self.transient(parent)
                try:
                    self.grab_set()
                except Exception:
                    pass
                
                tk.Label(self, text=f"Calibrating Profile for: {user_name}", fg="#00ffcc", bg="#0b0f19", font=("Segoe UI", 12, "bold")).pack(pady=15)
                self.instruction_lbl = tk.Label(self, text="Step 1/3: Look straight ahead at the camera.", fg="#e5e7eb", bg="#0b0f19", font=("Segoe UI", 10))
                self.instruction_lbl.pack(pady=5)

                self.canvas = tk.Canvas(self, width=280, height=210, bg="#111827", highlightthickness=1, highlightbackground="#1f2937")
                self.canvas.pack(pady=10)

                self.snap_btn = tk.Button(self, text="Capture Front View", command=self.take_snapshot, bg="#00ffcc", fg="#0b0f19", font=("Segoe UI", 10, "bold"), width=22, height=2, bd=0)
                self.snap_btn.pack(pady=15)

                self.step = 1
                threading.Thread(target=self.init_camera, daemon=True).start()
                self.protocol("WM_DELETE_WINDOW", self.on_close)
                self.update_preview()

            def init_camera(self):
                with CAMERA_ACCESS_LOCK:
                    time.sleep(0.2)
                    try:
                        cap = cv2.VideoCapture(0)
                        if cap.isOpened():
                            self.cap = cap
                            while self.is_active and self.cap and self.cap.isOpened():
                                ret, frame = self.cap.read()
                                if ret and frame is not None:
                                    with self.frame_lock:
                                        self.current_frame = frame.copy()
                                time.sleep(0.02)
                    except Exception:
                        pass
                    finally:
                        if self.cap:
                            try:
                                self.cap.release()
                            except Exception:
                                pass
                            self.cap = None

            def update_preview(self):
                if not self.is_active:
                    return
                try:
                    frame_to_show = None
                    with self.frame_lock:
                        if self.current_frame is not None:
                            frame_to_show = self.current_frame.copy()
                    if frame_to_show is not None:
                        rgb = cv2.cvtColor(frame_to_show, cv2.COLOR_BGR2RGB)
                        img = Image.fromarray(rgb).resize((280, 210))
                        self.photo = ImageTk.PhotoImage(img)
                        if self.winfo_exists():
                            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
                except Exception:
                    pass
                try:
                    if self.winfo_exists() and self.is_active:
                        self.preview_job = self.after(30, self.update_preview)
                except Exception:
                    pass

            def take_snapshot(self):
                frame_snapshot = None
                with self.frame_lock:
                    if self.current_frame is not None:
                        frame_snapshot = self.current_frame.copy()
                if frame_snapshot is None:
                    return
                is_success, buffer = cv2.imencode(".jpg", frame_snapshot)
                if not is_success:
                    return
                image_bytes = buffer.tobytes()

                if self.step == 1:
                    self.captured_images["front"] = image_bytes
                    self.step = 2
                    self.instruction_lbl.config(text="Step 2/3: Turn your head to the LEFT side.")
                    self.snap_btn.config(text="Capture Left Profile")
                elif self.step == 2:
                    self.captured_images["left"] = image_bytes
                    self.step = 3
                    self.instruction_lbl.config(text="Step 3/3: Turn your head to the RIGHT side.")
                    self.snap_btn.config(text="Capture Right Profile")
                elif self.step == 3:
                    self.captured_images["right"] = image_bytes
                    users = load_json(USERS_FILE, {})
                    users[self.user_name] = {
                        "front": base64.b64encode(self.captured_images["front"]).decode('utf-8'),
                        "left": base64.b64encode(self.captured_images["left"]).decode('utf-8'),
                        "right": base64.b64encode(self.captured_images["right"]).decode('utf-8')
                    }
                    save_json(USERS_FILE, users)
                    messagebox.showinfo("Success", f"Profile for {self.user_name} enrolled!")
                    self.on_close()

            def on_close(self):
                self.is_active = False
                try:
                    if self.preview_job:
                        self.after_cancel(self.preview_job)
                except Exception:
                    pass
                if self.cap:
                    try:
                        self.cap.release()
                    except Exception:
                        pass
                try:
                    self.destroy()
                except Exception:
                    pass

        class JarvisApp(tk.Tk):
            def __init__(self, settings):
                super().__init__()
                self.settings = settings
                self.assistant_name = settings.get("assistant_name", "Jarvis")
                self.user_name = settings.get("user_name", "Braden")
                self.voice_accent = settings.get("voice_accent", "UK")
                self.pronouns = settings.get("pronouns", "He/Him")
                self.selected_voice_id = settings.get("selected_voice", "")
                
                self.conversation_history = []
                self.current_worker_thread = None
                self.interrupt_flag = threading.Event()
                
                self.title(f"{self.assistant_name}")
                self.geometry("500x550")
                self.config(bg="#0b0f19")
                
                # Check for unauthorized close lock file on startup
                self.check_close_lock()

                self.protocol("WM_DELETE_WINDOW", self.prevent_close)

                self.is_processing = False
                self.is_talking = False
                self.angle1 = 0
                self.angle2 = 180
                self.pulse_radius_offset = 0
                self.direction = 1
                self.running = True

                self.sr_recognizer = sr.Recognizer()
                self.create_widgets()
                self.start_animation_loop()

                self.after(400, self.verify_or_enroll_user)

            def prevent_close(self):
                # Write lock flag indicating unauthorized close attempt
                with open(LOCK_FILE, "w") as f:
                    f.write("unauthorized")
                messagebox.showinfo("Jarvis Security", "I cannot be closed unless I close myself.")
                # Intentionally blocked from exiting via window 'X'

            def check_close_lock(self):
                if os.path.exists(LOCK_FILE):
                    try:
                        os.remove(LOCK_FILE)
                    except Exception:
                        pass
                    # Trigger spoken warning on startup after forced close attempt
                    threading.Thread(target=lambda: self.speak_text_locally("I cannot be closed unless I close myself."), daemon=True).start()

            def verify_or_enroll_user(self):
                users = load_json(USERS_FILE, {})
                if self.user_name not in users:
                    self.after(0, lambda: FaceEnrollmentWindow(self, self.user_name))
                threading.Thread(target=self.start_background_loops, daemon=True).start()

            def start_background_loops(self):
                try:
                    sd.query_devices(kind='input')
                except Exception:
                    pass
                threading.Thread(target=self.wake_word_listening_loop, daemon=True).start()
                threading.Thread(target=self.trigger_startup_greeting, daemon=True).start()

            def speak_text_locally(self, text):
                cleaned = clean_response_text(text)
                if not cleaned:
                    return
                with TTS_LOCK:
                    self.is_talking = True
                    try:
                        if sys.platform == 'win32' and pythoncom:
                            try:
                                pythoncom.CoInitialize()
                            except Exception:
                                pass
                        
                        engine = pyttsx3.init()
                        voices = engine.getProperty('voices')
                        chosen_voice_id = self.selected_voice_id
                        
                        if not chosen_voice_id or not any(v.id == chosen_voice_id for v in voices):
                            accent_pref = self.voice_accent.upper()
                            for voice in voices:
                                name_lower = voice.name.lower()
                                if accent_pref == "UK":
                                    if any(k in name_lower for k in ['gb', 'uk', 'hazel', 'george', 'alfie', 'oliver', 'charlotte', 'libby', 'maisie', 'ryan', 'stefan']):
                                        chosen_voice_id = voice.id
                                        break
                                else:
                                    if any(k in name_lower for k in ['us', 'david', 'zira', 'mark', 'aria', 'jenny', 'guy', 'steven', 'eric']):
                                        chosen_voice_id = voice.id
                                        break
                        if not chosen_voice_id and voices:
                            chosen_voice_id = voices[0].id
                        if chosen_voice_id:
                            engine.setProperty('voice', chosen_voice_id)
                        
                        engine.setProperty('rate', 185)
                        engine.setProperty('volume', 1.0)
                        
                        clean_speech = re.sub(r'[*_`~#\[\]]', '', cleaned)
                        engine.say(clean_speech)
                        engine.runAndWait()
                    except Exception:
                        pass
                    finally:
                        if sys.platform == 'win32' and pythoncom:
                            try:
                                pythoncom.CoUninitialize()
                            except Exception:
                                pass
                        self.is_talking = False
                        time.sleep(0.1)

                self.after(0, lambda: self.status_lbl.config(text="Response", fg="#00ffcc"))
                self.after(1500, lambda: self.status_lbl.config(text=f"Listening for \"Hey {self.assistant_name}\"...", fg="#38bdf8"))

            def create_widgets(self):
                top_frame = tk.Frame(self, bg="#0b0f19")
                top_frame.pack(fill=tk.X, padx=15, pady=10)

                gear_btn = tk.Button(top_frame, text="⚙", command=self.open_settings, bg="#0b0f19", fg="#00ffcc", font=("Segoe UI", 16), bd=0, cursor="hand2")
                gear_btn.pack(side=tk.RIGHT)

                self.canvas_size = 300
                self.canvas = tk.Canvas(self, width=self.canvas_size, height=self.canvas_size, bg="#0b0f19", highlightthickness=0)
                self.canvas.pack(expand=True, pady=(10, 5))

                self.status_lbl = tk.Label(self, text=f"Listening for \"Hey {self.assistant_name}\"...", fg="#38bdf8", bg="#0b0f19", font=("Segoe UI", 11, "bold"))
                self.status_lbl.pack(pady=(0, 20))

            def start_animation_loop(self):
                if not self.running:
                    return
                try:
                    self.canvas.delete("all")
                    center = self.canvas_size // 2
                    base_radius = 90

                    self.canvas.create_oval(center - base_radius, center - base_radius, center + base_radius, center + base_radius, fill="#0b0f19", outline="#1f2937", width=3)
                    tri_size = 55
                    points = [center, center - tri_size - 10, center - tri_size, center + tri_size - 10, center + tri_size, center + tri_size - 10]
                    self.canvas.create_polygon(points, outline="#00ffcc", width=2, fill="#111827")
                    
                    if self.is_processing:
                        r1 = base_radius + 15
                        r2 = base_radius + 28
                        self.canvas.create_arc(center - r1, center - r1, center + r1, center + r1, start=self.angle1, extent=240, outline="#00ffcc", width=4, style="arc")
                        self.canvas.create_arc(center - r2, center - r2, center + r2, center + r2, start=self.angle2, extent=200, outline="#38bdf8", width=3, style="arc")
                        self.angle1 = (self.angle1 + 12) % 360
                        self.angle2 = (self.angle2 - 18) % 360
                    elif self.is_talking:
                        self.pulse_radius_offset += self.direction * 2.2
                        if self.pulse_radius_offset > 15 or self.pulse_radius_offset < 0:
                            self.direction *= -1
                        pr1 = base_radius + int(self.pulse_radius_offset)
                        self.canvas.create_oval(center - pr1, center - pr1, center + pr1, center + pr1, outline="#00ffcc", width=2)
                except Exception:
                    pass
                if self.running:
                    self.after(35, self.start_animation_loop)

            def wake_word_listening_loop(self):
                sample_rate = 16000
                chunk_duration = 2.5
                target_phrase = f"hey {self.assistant_name.lower()}"

                while self.running:
                    if self.is_processing or self.is_talking:
                        time.sleep(0.3)
                        continue
                    try:
                        audio_np = sd.rec(int(chunk_duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
                        sd.wait()
                        if self.is_processing or self.is_talking:
                            continue

                        import io, wave
                        wav_io = io.BytesIO()
                        with wave.open(wav_io, 'wb') as wf:
                            wf.setnchannels(1)
                            wf.setsampwidth(2)
                            wf.setframerate(sample_rate)
                            wf.writeframes(audio_np.tobytes())
                        
                        with sr.AudioFile(io.BytesIO(wav_io.getvalue())) as source:
                            audio_data = self.sr_recognizer.record(source)

                        try:
                            transcript = self.sr_recognizer.recognize_google(audio_data).lower()
                            if target_phrase in transcript:
                                play_wake_beep()
                                self.after(0, lambda: self.status_lbl.config(text="Listening...", fg="#00ffcc"))
                                self.listen_and_process_command(is_followup=False)
                        except sr.UnknownValueError:
                            pass
                        except sr.RequestError:
                            time.sleep(0.8)
                    except Exception:
                        time.sleep(0.5)

            def listen_and_process_command(self, is_followup=False):
                # Interruption handling: signal previous thread and launch new worker
                if self.current_worker_thread and self.current_worker_thread.is_alive():
                    self.interrupt_flag.set()
                
                self.interrupt_flag.clear()
                self.current_worker_thread = threading.Thread(target=lambda: self.record_and_process_speech(is_followup), daemon=True)
                self.current_worker_thread.start()

            def record_and_process_speech(self, is_followup=False):
                self.is_processing = True
                
                # State 1: Listening
                self.after(0, lambda: self.status_lbl.config(text="Listening...", fg="#00ffcc"))
                try:
                    duration = 5.0
                    sample_rate = 16000
                    audio_np = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
                    sd.wait()

                    if self.interrupt_flag.is_set():
                        self.is_processing = False
                        return

                    # Trigger U.S.S. Triton echoing click when transitioning to Thinking
                    play_triton_echo_click()

                    # State 2: Thinking
                    self.after(0, lambda: self.status_lbl.config(text="Thinking...", fg="#38bdf8"))

                    import io, wave
                    wav_io = io.BytesIO()
                    with wave.open(wav_io, 'wb') as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(sample_rate)
                        wf.writeframes(audio_np.tobytes())
                    
                    transcript_text = ""
                    try:
                        with sr.AudioFile(io.BytesIO(wav_io.getvalue())) as source:
                            audio_data = self.sr_recognizer.record(source)
                        transcript_text = self.sr_recognizer.recognize_google(audio_data)
                    except Exception:
                        pass

                    if not transcript_text.strip() or self.interrupt_flag.is_set():
                        self.is_processing = False
                        self.after(0, lambda: self.status_lbl.config(text=f"Listening for \"Hey {self.assistant_name}\"...", fg="#38bdf8"))
                        return

                    self.conversation_history.append({"role": "user", "content": transcript_text})
                    if len(self.conversation_history) > 14:
                        self.conversation_history = self.conversation_history[-14:]

                    # State 3: Writing response
                    self.after(0, lambda: self.status_lbl.config(text="Writing response...", fg="#00ffcc"))

                    if not is_internet_available():
                        response_text = handle_offline_command(transcript_text, self.user_name, self.assistant_name)
                    else:
                        system_instruction = (
                            f"You are {self.assistant_name}, an intelligent assistant controlling {self.user_name}'s computer. "
                            f"User's Pronouns: {self.pronouns}. "
                            f"Output ONLY the final conversational response to be spoken aloud."
                        )
                        response_text = call_nvidia_api(self.conversation_history, system_instruction)
                        if "communication timeout" in response_text.lower():
                            response_text = handle_offline_command(transcript_text, self.user_name, self.assistant_name)

                    if self.interrupt_flag.is_set():
                        self.is_processing = False
                        return

                    self.is_processing = False
                    if response_text:
                        self.conversation_history.append({"role": "assistant", "content": response_text})
                        self.speak_text_locally(response_text)

                except Exception:
                    self.is_processing = False
                    self.after(0, lambda: self.status_lbl.config(text=f"Listening for \"Hey {self.assistant_name}\"...", fg="#38bdf8"))

            def trigger_startup_greeting(self):
                self.is_processing = True
                self.after(0, lambda: self.status_lbl.config(text="Writing response...", fg="#00ffcc"))
                if not is_internet_available():
                    response_text = f"Hello {self.user_name}. Systems online in offline mode."
                else:
                    greeting_prompt = f"Greet {self.user_name} concisely as {self.assistant_name}."
                    system_instruction = f"You are {self.assistant_name}. User's Pronouns: {self.pronouns}. Output ONLY spoken greeting."
                    response_text = call_nvidia_api([{"role": "user", "content": greeting_prompt}], system_instruction)
                    if "communication timeout" in response_text.lower():
                        response_text = f"Hello {self.user_name}. Systems online."

                self.is_processing = False
                if response_text:
                    self.conversation_history.append({"role": "assistant", "content": response_text})
                    self.speak_text_locally(response_text)

            def open_settings(self):
                settings_win = tk.Toplevel(self)
                settings_win.title("Jarvis Settings")
                settings_win.geometry("400x440")
                settings_win.config(bg="#0b0f19")
                settings_win.resizable(False, False)

                tk.Label(settings_win, text="SYSTEM SETTINGS", fg="#00ffcc", bg="#0b0f19", font=("Segoe UI", 12, "bold")).pack(pady=15)
                form_frame = tk.Frame(settings_win, bg="#111827", bd=1, relief="solid")
                form_frame.pack(padx=20, pady=5, fill="both", expand=True)

                voice_names = []
                voice_map = {}
                try:
                    engine_temp = pyttsx3.init()
                    for v in engine_temp.getProperty('voices'):
                        voice_names.append(v.name)
                        voice_map[v.name] = v.id
                except Exception:
                    voice_names = ["Default System Voice"]

                tk.Label(form_frame, text="Select Voice:", fg="#e5e7eb", bg="#111827", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=15, pady=(8, 2))
                voice_combo = ttk.Combobox(form_frame, values=voice_names, width=35, state="readonly", font=("Segoe UI", 9))
                
                current_v_name = "Default System Voice"
                for vname, vid in voice_map.items():
                    if vid == self.selected_voice_id:
                        current_v_name = vname
                        break
                voice_combo.set(current_v_name if voice_names else "Default System Voice")
                voice_combo.pack(anchor="w", padx=15, pady=(0, 10))

                def save_settings_changes():
                    selected_name = voice_combo.get()
                    if selected_name in voice_map:
                        self.selected_voice_id = voice_map[selected_name]
                    self.settings["selected_voice"] = self.selected_voice_id
                    save_json(SETTINGS_FILE, self.settings)
                    messagebox.showinfo("Success", "Voice updated successfully!")
                    settings_win.destroy()

                def reconfigure_app():
                    settings_win.destroy()
                    wizard = SetupWizard(self.settings)
                    wizard.mainloop()
                    if wizard.result:
                        self.settings = wizard.result
                        save_json(SETTINGS_FILE, self.settings)
                        self.destroy()
                        os.execv(sys.executable, [sys.executable, os.path.abspath(sys.argv[0])])

                tk.Button(form_frame, text="Save Voice Choice", command=save_settings_changes, bg="#00ffcc", fg="#0b0f19", font=("Segoe UI", 9, "bold"), width=30, height=2, bd=0).pack(pady=5)
                tk.Button(settings_win, text="Reconfigure Assistant Preferences", command=reconfigure_app, bg="#1f2937", fg="#ffffff", font=("Segoe UI", 9), width=35, height=2, bd=0).pack(pady=4)

        settings = load_json(SETTINGS_FILE, None)
        nvidia_exists = bool(secure_get_password(KEYRING_SERVICE_NAME, "nvidia_api_key"))

        if not settings or not nvidia_exists:
            wizard = SetupWizard(settings)
            wizard.mainloop()
            settings = wizard.result
            if not settings:
                sys.exit(0)
            save_json(SETTINGS_FILE, settings)

        app = JarvisApp(settings)
        app.mainloop()

    except Exception as e:
        print("\n" + "="*60)
        print("JARVIS CRASHED WITH THE FOLLOWING ERROR:")
        traceback.print_exc()
        print("="*60)
        input("\nPress Enter to close this window...")
