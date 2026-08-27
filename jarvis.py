import os
import sys

# Do NOT hide the console window so you can see any startup errors clearly
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".jarvis_core")
os.makedirs(CONFIG_DIR, exist_ok=True)
CRASH_LOG_FILE = os.path.join(CONFIG_DIR, "jarvis_crash.log")

# Master try-except wrapper covering everything
if __name__ == "__main__":
    try:
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

        def check_dependencies():
            required = {
                "cv2": "opencv-python", 
                "PIL": "pillow", 
                "keyring": "keyring",
                "sounddevice": "sounddevice",
                "numpy": "numpy",
                "speech_recognition": "SpeechRecognition",
                "pyttsx3": "pyttsx3",
                "pythoncom": "pywin32"
            }
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
        from tkinter import messagebox, simpledialog
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

        # ==================== LAPTOP CONTROL TOOLS ====================
        def run_command(command: str) -> str:
            """Executes a Windows command shell script or command on the user's laptop and returns the output."""
            try:
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=15)
                output = result.stdout + "\n" + result.stderr
                return output.strip() or "Command executed successfully with no output."
            except Exception as e:
                return f"Error executing command: {e}"

        def lock_computer() -> str:
            """Locks the Windows computer workstation screen immediately for security."""
            try:
                if sys.platform == 'win32':
                    import ctypes
                    ctypes.windll.user32.LockWorkStation()
                    return "Workstation locked successfully."
                return "Unsupported platform for locking."
            except Exception as e:
                return f"Error locking screen: {e}"

        def get_system_status() -> str:
            """Returns current system username, platform, and local system time."""
            return f"Current user: {getpass.getuser()}, OS: Windows, Time: {time.ctime()}"

        def terminate_jarvis() -> str:
            """Authorized command for Jarvis to shut down completely when explicitly requested."""
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
                    "description": "Executes a Windows command shell script or command on the user's laptop and returns the output.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "The Windows CMD or PowerShell command to execute."
                            }
                        },
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "lock_computer",
                    "description": "Locks the Windows computer workstation screen immediately for security.",
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
                    "name": "terminate_jarvis",
                    "description": "Permanently terminates and closes Jarvis. Only call this when explicitly authorized by the user.",
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
            elif name == "terminate_jarvis":
                return terminate_jarvis()
            return "Unknown tool executed."
        # ==============================================================

        def play_wake_beep():
            try:
                if sys.platform == 'win32':
                    import winsound
                    winsound.Beep(800, 50)
                    winsound.Beep(1200, 70)
            except Exception:
                pass

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

        def get_available_models():
            today = time.strftime("%Y-%m-%d")
            usage_data = load_json(USAGE_FILE, {})
            if usage_data.get("date") != today:
                return MODEL_CANDIDATES
            used_list = usage_data.get("used_models", [])
            return [m for m in MODEL_CANDIDATES if m not in used_list]

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
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {nvidia_key}"
            }

            available_models = get_available_models()
            if not available_models:
                usage_data = load_json(USAGE_FILE, {})
                usage_data["used_models"] = []
                save_json(USAGE_FILE, usage_data)
                available_models = MODEL_CANDIDATES

            for model_name in available_models:
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
                self.title("Assistant Configuration Setup v38")
                self.geometry("450x440")
                self.config(bg="#0b0f19")
                self.result = None
                
                self.update_idletasks()
                x = (self.winfo_screenwidth() // 2) - (450 // 2)
                y = (self.winfo_screenheight() // 2) - (440 // 2)
                self.geometry(f"450x440+{x}+{y}")

                saved_nvidia = secure_get_password(KEYRING_SERVICE_NAME, "nvidia_api_key")
                existing = existing_settings or {}
                
                default_user = existing.get("user_name", "Braden")

                tk.Label(self, text="CONFIGURATION SETUP V38", fg="#00ffcc", bg="#0b0f19", font=("Segoe UI", 14, "bold")).pack(pady=(15, 10))
                
                form_frame = tk.Frame(self, bg="#111827", bd=1, relief="solid")
                form_frame.pack(padx=20, pady=5, fill="both", expand=True)

                self.entries = {}
                fields = [
                    ("Assistant Name:", existing.get("assistant_name", "Jarvis")),
                    ("Your Preferred Name:", default_user),
                    ("Voice Accent (UK / US):", existing.get("voice_accent", "UK")),
                    ("NVIDIA API Key:", saved_nvidia)
                ]

                for label_text, default_val in fields:
                    tk.Label(form_frame, text=label_text, fg="#e5e7eb", bg="#111827", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=15, pady=(4, 1))
                    show_char = "*" if "API Key" in label_text else None
                    ent = tk.Entry(form_frame, width=38, font=("Segoe UI", 9), bg="#1f2937", fg="#ffffff", insertbackground="white", bd=1, relief="solid", show=show_char)
                    ent.insert(0, default_val)
                    ent.pack(anchor="w", padx=15, pady=(0, 3))
                    self.entries[label_text] = ent

                tk.Button(self, text="Save & Launch", command=self.on_save, bg="#00ffcc", fg="#0b0f19", font=("Segoe UI", 10, "bold"), width=20, height=2, bd=0, cursor="hand2").pack(pady=10)

            def on_save(self):
                nvidia_key = self.entries["NVIDIA API Key:"].get().strip()
                if not nvidia_key:
                    messagebox.showerror("Error", "An NVIDIA API Key is required.")
                    return

                secure_store_password(KEYRING_SERVICE_NAME, "nvidia_api_key", nvidia_key)
                settings = {
                    "assistant_name": self.entries["Assistant Name:"].get().strip() or "Jarvis",
                    "user_name": self.entries["Your Preferred Name:"].get().strip() or "Braden",
                    "voice_accent": self.entries["Voice Accent (UK / US):"].get().strip().upper() or "UK"
                }
                self.result = settings
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
                                else:
                                    time.sleep(0.03)
                                time.sleep(0.01)
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
                    messagebox.showerror("Error", "Webcam feed not ready.")
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
                    messagebox.showinfo("Success", f"Profile for {self.user_name} successfully enrolled!")
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
                    self.cap = None
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
                
                self.conversation_history = []
                
                self.title(f"{self.assistant_name} (Debug v38)")
                self.geometry("500x550")
                self.config(bg="#0b0f19")
                
                self.resizable(True, True)
                self.bind("<F11>", self.toggle_fullscreen)
                self.bind("<Escape>", self.exit_fullscreen)
                self._is_fullscreen = False

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
                self.protocol("WM_DELETE_WINDOW", lambda: self.quit_app(authorized=False))

            def toggle_fullscreen(self, event=None):
                self._is_fullscreen = not self._is_fullscreen
                self.attributes("-fullscreen", self._is_fullscreen)

            def exit_fullscreen(self, event=None):
                if self._is_fullscreen:
                    self._is_fullscreen = False
                    self.attributes("-fullscreen", False)

            def verify_or_enroll_user(self):
                users = load_json(USERS_FILE, {})
                if self.user_name not in users:
                    self.after(0, lambda: FaceEnrollmentWindow(self, self.user_name))
                threading.Thread(target=self.request_native_permissions_and_start, daemon=True).start()

            def request_native_permissions_and_start(self):
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
                        selected_voice_id = None
                        accent_pref = self.voice_accent.upper()
                        
                        for voice in voices:
                            name_lower = voice.name.lower()
                            if accent_pref == "UK":
                                if any(k in name_lower for k in ['gb', 'uk', 'hazel', 'george', 'alfie', 'oliver', 'charlotte', 'libby', 'maisie', 'ryan', 'stefan']):
                                    selected_voice_id = voice.id
                                    break
                            else:
                                if any(k in name_lower for k in ['us', 'david', 'zira', 'mark', 'aria', 'jenny', 'guy', 'steven', 'eric']):
                                    selected_voice_id = voice.id
                                    break
                        
                        if not selected_voice_id and voices:
                            selected_voice_id = voices[0].id
                        
                        if selected_voice_id:
                            engine.setProperty('voice', selected_voice_id)
                        
                        engine.setProperty('rate', 185)
                        engine.setProperty('volume', 1.0)
                        
                        clean_speech = re.sub(r'[*_`~#\[\]]', '', cleaned)
                        engine.say(clean_speech)
                        engine.runAndWait()
                    except Exception as e:
                        print(f"TTS Error: {e}")
                    finally:
                        if sys.platform == 'win32' and pythoncom:
                            try:
                                pythoncom.CoUninitialize()
                            except Exception:
                                pass
                        self.is_talking = False
                        time.sleep(0.2)

                ends_with_question = "?" in cleaned or any(cleaned.lower().startswith(w) for w in ["what", "who", "where", "when", "why", "how", "can you", "would you", "do you", "is there", "are you", "did you"])
                
                if ends_with_question:
                    self.after(50, lambda: self.listen_and_process_command(is_followup=True))
                else:
                    self.after(50, lambda: self.status_lbl.config(text=f"Listening for \"Hey {self.assistant_name}\"...", fg="#38bdf8"))

            def create_widgets(self):
                top_frame = tk.Frame(self, bg="#0b0f19")
                top_frame.pack(fill=tk.X, padx=15, pady=10)

                tk.Label(top_frame, text="Press F11 for Fullscreen", fg="#4b5563", bg="#0b0f19", font=("Segoe UI", 9)).pack(side=tk.LEFT)

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

                        import io
                        import wave
                        wav_io = io.BytesIO()
                        with wave.open(wav_io, 'wb') as wf:
                            wf.setnchannels(1)
                            wf.setsampwidth(2)
                            wf.setframerate(sample_rate)
                            wf.writeframes(audio_np.tobytes())
                        wav_bytes = wav_io.getvalue()

                        with sr.AudioFile(io.BytesIO(wav_bytes)) as source:
                            audio_data = self.sr_recognizer.record(source)

                        try:
                            transcript = self.sr_recognizer.recognize_google(audio_data).lower()
                            if target_phrase in transcript:
                                play_wake_beep()
                                self.after(0, lambda: self.status_lbl.config(text="Listening for command...", fg="#00ffcc"))
                                self.listen_and_process_command(is_followup=False)
                        except sr.UnknownValueError:
                            pass
                        except sr.RequestError:
                            time.sleep(0.8)
                    except Exception:
                        time.sleep(0.8)

            def listen_and_process_command(self, is_followup=False):
                if self.is_processing:
                    return
                threading.Thread(target=lambda: self.record_and_process_speech(is_followup), daemon=True).start()

            def record_and_process_speech(self, is_followup=False):
                self.is_processing = True
                self.after(0, lambda: self.status_lbl.config(text="Listening..." if is_followup else "Processing...", fg="#00ffcc"))
                try:
                    duration = 5.0
                    sample_rate = 16000
                    audio_np = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
                    sd.wait()

                    transcript_text = ""
                    try:
                        import io
                        import wave
                        wav_io = io.BytesIO()
                        with wave.open(wav_io, 'wb') as wf:
                            wf.setnchannels(1)
                            wf.setsampwidth(2)
                            wf.setframerate(sample_rate)
                            wf.writeframes(audio_np.tobytes())
                        audio_bytes = wav_io.getvalue()

                        with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
                            audio_data = self.sr_recognizer.record(source)
                        transcript_text = self.sr_recognizer.recognize_google(audio_data)
                    except Exception:
                        pass

                    if not transcript_text.strip():
                        self.is_processing = False
                        self.after(0, lambda: self.status_lbl.config(text=f"Listening for \"Hey {self.assistant_name}\"...", fg="#38bdf8"))
                        return

                    self.conversation_history.append({"role": "user", "content": transcript_text})
                    
                    if len(self.conversation_history) > 14:
                        self.conversation_history = self.conversation_history[-14:]

                    system_instruction = (
                        f"You are {self.assistant_name}, an intelligent assistant controlling {self.user_name}'s Windows laptop. "
                        f"STRICT RULES: "
                        f"1. Never output internal thoughts, reasoning steps, or <think> tags. "
                        f"2. Output ONLY the final conversational response to be spoken aloud. "
                        f"3. Never perform actions or execute tools unless explicitly requested by the user."
                    )

                    response_text = call_nvidia_api(self.conversation_history, system_instruction)

                    self.is_processing = False

                    if response_text:
                        self.conversation_history.append({"role": "assistant", "content": response_text})
                        self.speak_text_locally(response_text)

                except Exception:
                    self.is_processing = False
                    self.after(0, lambda: self.status_lbl.config(text=f"Listening for \"Hey {self.assistant_name}\"...", fg="#38bdf8"))

            def trigger_startup_greeting(self):
                self.is_processing = True
                greeting_prompt = f"Greet {self.user_name} instantly and concisely as {self.assistant_name}, confirming systems online."
                system_instruction = f"You are {self.assistant_name}. Output ONLY the spoken greeting. No internal thoughts or reasoning."
                
                init_messages = [{"role": "user", "content": greeting_prompt}]
                response_text = call_nvidia_api(init_messages, system_instruction)
                self.is_processing = False
                if response_text:
                    self.conversation_history.append({"role": "assistant", "content": response_text})
                    self.speak_text_locally(response_text)

            def open_settings(self):
                settings_win = tk.Toplevel(self)
                settings_win.title("Jarvis Settings")
                settings_win.geometry("380x360")
                settings_win.config(bg="#0b0f19")
                settings_win.resizable(False, False)

                tk.Label(settings_win, text="SYSTEM SETTINGS V38", fg="#00ffcc", bg="#0b0f19", font=("Segoe UI", 12, "bold")).pack(pady=15)

                def add_new_user():
                    settings_win.destroy()
                    new_name = simpledialog.askstring("New User", "Enter name of new authorized user:")
                    if new_name:
                        FaceEnrollmentWindow(self, new_name.strip())

                tk.Button(settings_win, text="Add New Authorized User", command=add_new_user, bg="#1f2937", fg="#ffffff", font=("Segoe UI", 10), width=28, height=2, bd=0).pack(pady=6)

                def reconfigure_app():
                    settings_win.destroy()
                    wizard = SetupWizard(self.settings)
                    wizard.mainloop()
                    if wizard.result:
                        self.settings = wizard.result
                        save_json(SETTINGS_FILE, self.settings)
                        self.destroy()
                        python_exe = sys.executable
                        script_path = os.path.abspath(sys.argv[0])
                        os.execv(python_exe, [python_exe, script_path])

                tk.Button(settings_win, text="Reconfigure Assistant Preferences", command=reconfigure_app, bg="#1f2937", fg="#ffffff", font=("Segoe UI", 10), width=28, height=2, bd=0).pack(pady=6)
                tk.Button(settings_win, text="Close Settings", command=settings_win.destroy, bg="#00ffcc", fg="#0b0f19", font=("Segoe UI", 10, "bold"), width=28, height=2, bd=0).pack(pady=6)

            def quit_app(self, authorized=False):
                if not authorized:
                    try:
                        subprocess.Popen([sys.executable, os.path.abspath(sys.argv[0])], creationflags=subprocess.DETACHED_PROCESS if sys.platform == 'win32' else 0)
                    except Exception:
                        pass
                
                self.running = False
                try:
                    self.destroy()
                except Exception:
                    pass
                
                if not authorized:
                    sys.exit(0)

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
