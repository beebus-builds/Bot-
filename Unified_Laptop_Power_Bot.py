#!/usr/bin/env python3
"""
Unified Laptop Power Bot - Pure Python Desktop & Mobile Controller
==============================================================
This is a single pure Python file that provides:
1. Desktop GUI Application (CustomTkinter)
2. System Power Control (Shutdown, Restart, Sleep, Lock, Cancel Timer)
3. System Tray Integration for background running
4. Local HTTP Server for Remote Mobile/Desktop Control (Pure http.server)
5. QR Code generation for instant mobile pairing

Requirements:
- Python 3.10+
- pip install customtkinter pystray psutil qrcode pillow

Usage:
    python Unified_Laptop_Power_Bot.py
"""

import os
import sys
import json
import threading
import time
import socket
import platform
import subprocess
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import psutil

# GUI & System tray imports
import customtkinter as ctk
from tkinter import messagebox, simpledialog
import pystray
from PIL import Image, ImageDraw

# QR Code for pairing
try:
    import qrcode
    from io import BytesIO
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False

# Configuration
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_config.json")

DEFAULT_CONFIG = {
    "pin_code": "1234",
    "require_pin": True,
    "http_port": 8080,
    "auto_start": False,
    "server_running": True
}

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                cfg = json.load(f)
                return {**DEFAULT_CONFIG, **cfg}
        except:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(cfg, f, indent=2)

class SystemPowerController:
    """Pure Python system power controller - no external dependencies"""
    
    @staticmethod
    def get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return '127.0.0.1'
    
    @staticmethod
    def get_system_stats():
        try:
            bat = psutil.sensors_battery()
            battery_info = {
                "percent": int(bat.percent),
                "plugged": bat.power_plugged
            } if bat else {"percent": 0, "plugged": False}
            
            stats = {
                "hostname": socket.gethostname(),
                "local_ip": SystemPowerController.get_local_ip(),
                "platform": platform.system(),
                "cpu_percent": psutil.cpu_percent(interval=0.2),
                "ram_percent": psutil.virtual_memory().percent,
                "ram_used_gb": round(psutil.virtual_memory().used / (1024**3), 1),
                "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 1),
                "battery": battery_info,
                "timestamp": datetime.now().isoformat()
            }
            return stats
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def shutdown(delay_seconds=0):
        try:
            system = platform.system().lower()
            if system == "windows":
                t = max(0, int(delay_seconds))
                cmd = f'shutdown /s /t {t}'
                subprocess.run(cmd, shell=True, check=True)
            elif system == "darwin":
                cmd = "sudo shutdown -h now" if delay_seconds <= 0 else f"sudo shutdown -h +1"
                subprocess.run(cmd, shell=True, check=True)
            else:
                cmd = f'shutdown -h {delay_seconds}'
                subprocess.run(cmd, shell=True, check=True)
            return {"status": "success", "message": f"Shutdown scheduled in {delay_seconds}s"}
        except Exception as e:
            return {"status": "error", "message": f"Shutdown failed: {e}"}
    
    @staticmethod
    def restart(delay_seconds=0):
        try:
            system = platform.system().lower()
            if system == "windows":
                t = max(0, int(delay_seconds))
                cmd = f'shutdown /r /t {t}'
                subprocess.run(cmd, shell=True, check=True)
            elif system == "darwin":
                subprocess.run("sudo shutdown -r now", shell=True, check=True)
            else:
                cmd = f'shutdown -r {delay_seconds}'
                subprocess.run(cmd, shell=True, check=True)
            return {"status": "success", "message": f"Restart scheduled in {delay_seconds}s"}
        except Exception as e:
            return {"status": "error", "message": f"Restart failed: {e}"}
    
    @staticmethod
    def sleep():
        try:
            system = platform.system().lower()
            if system == "windows":
                # Use rundll32 powrprof for reliable sleep on Windows
                cmd = 'rundll32.exe powrprof.dll,SetSuspendState 0,1,0'
                subprocess.run(cmd, shell=True, check=True)
            elif system == "darwin":
                subprocess.run("pmset sleepnow", shell=True, check=True)
            else:
                subprocess.run("systemctl suspend", shell=True, check=True)
            return {"status": "success", "message": "Sleep mode activated"}
        except Exception as e:
            return {"status": "error", "message": f"Sleep failed: {e}"}
    
    @staticmethod
    def lock():
        try:
            system = platform.system().lower()
            if system == "windows":
                subprocess.run("rundll32.exe user32.dll,LockWorkStation", shell=True, check=True)
            elif system == "darwin":
                subprocess.run("/System/Library/CoreServices/Menu\\ Extras/User.menu/Contents/Resources/CGSession -suspend", shell=True, check=True)
            else:
                subprocess.run("loginctl lock-session", shell=True, check=True)
            return {"status": "success", "message": "Screen locked"}
        except Exception as e:
            return {"status": "error", "message": f"Lock failed: {e}"}
    
    @staticmethod
    def cancel_timer():
        try:
            system = platform.system().lower()
            if system == "windows":
                subprocess.run("shutdown /a", shell=True, check=True)
            elif system == "darwin":
                subprocess.run("sudo shutdown -c", shell=True, check=True)
            else:
                subprocess.run("shutdown -c", shell=True, check=True)
            return {"status": "success", "message": "Scheduled action cancelled"}
        except Exception as e:
            return {"status": "error", "message": f"Cancel failed: {e}"}

class RemoteHTTPServer:
    """Pure Python HTTP server for remote control - no FastAPI needed"""
    
    def __init__(self, controller, config):
        self.controller = controller
        self.config = config
        self.server = None
        self.server_thread = None
        
    def start(self):
        port = self.config.get("http_port", 8080)
        try:
            handler = self.create_handler()
            self.server = HTTPServer(('0.0.0.0', port), handler)
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            print(f"🌐 Remote Server started on http://{self.controller.get_local_ip()}:{port}")
            return True
        except Exception as e:
            print(f"⚠️  Server failed: {e}")
            return False
    
    def stop(self):
        if self.server:
            self.server.shutdown()
    
    def verify_pin(self, pin):
        if not self.config.get("require_pin", True):
            return True
        return pin == self.config.get("pin_code", "1234")
    
    def create_handler(self):
        controller = self.controller
        config = self.config
        verify_pin = self.verify_pin
        
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass  # Suppress default logging
            
            def send_json(self, data, status=200):
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(data).encode())
            
            def do_OPTIONS(self):
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-PIN')
                self.end_headers()
            
            def do_GET(self):
                parsed = urlparse(self.path)
                path = parsed.path
                
                if path == '/':
                    self.serve_mobile_ui()
                elif path == '/api/status':
                    stats = controller.get_system_stats()
                    self.send_json(stats)
                elif path == '/api/qr':
                    self.serve_qr_code(controller, config)
                elif path == '/api/ping':
                    self.send_json({"status": "ok", "message": "PowerBot is alive"})
                else:
                    self.send_response(404)
                    self.end_headers()
            
            def do_POST(self):
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length).decode()
                
                parsed = urlparse(self.path)
                path = parsed.path
                
                try:
                    data = json.loads(post_data) if post_data else {}
                except:
                    data = {}
                
                pin_header = self.headers.get('X-PIN', '')
                pin_body = data.get('pin', '')
                pin = pin_header or pin_body
                
                # Verify PIN for protected actions
                protected_paths = ['/api/action/shutdown', '/api/action/restart', '/api/action/sleep', '/api/action/lock', '/api/action/cancel']
                if path in protected_paths and not verify_pin(pin):
                    self.send_json({"status": "error", "message": "Invalid PIN code"}, status=401)
                    return
                
                delay = int(data.get('delay_seconds', 0))
                
                if path == '/api/action/shutdown':
                    result = controller.shutdown(delay)
                elif path == '/api/action/restart':
                    result = controller.restart(delay)
                elif path == '/api/action/sleep':
                    result = controller.sleep()
                elif path == '/api/action/lock':
                    result = controller.lock()
                elif path == '/api/action/cancel':
                    result = controller.cancel_timer()
                else:
                    self.send_response(404)
                    self.end_headers()
                    return
                
                self.send_json(result)
            
            def serve_mobile_ui(self):
                html = self.generate_mobile_ui(controller)
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(html.encode())
            
            def serve_qr_code(self, controller, config):
                if not QR_AVAILABLE:
                    self.send_json({"error": "QR library not available"}, status=500)
                    return
                
                local_ip = controller.get_local_ip()
                port = config.get('http_port', 8080)
                url = f"http://{local_ip}:{port}"
                
                qr = qrcode.QRCode(version=1, box_size=10, border=4)
                qr.add_data(url)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                qr_bytes = buffer.getvalue()
                
                self.send_response(200)
                self.send_header('Content-Type', 'image/png')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(qr_bytes)
            
            def generate_mobile_ui(self, controller):
                local_ip = controller.get_local_ip()
                return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🤖 PowerBot Robot Remote</title>
<style>
body{{margin:0;font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#0f172a;color:#fff;}}
.header{{background:#1e293b;padding:20px;text-align:center;}}
.header h1{{margin:0;font-size:24px;}}
.status{{padding:15px;background:#1e293b;margin:10px;border-radius:12px;}}
.btn{{width:100%;padding:18px;margin:8px 0;border:none;border-radius:12px;font-size:18px;font-weight:bold;cursor:pointer;transition:0.2s;}}
.btn:active{{transform:scale(0.98);}}
.shutdown{{background:#dc2626;color:white;}}
.restart{{background:#ea580c;color:white;}}
.sleep{{background:#2563eb;color:white;}}
.lock{{background:#7c3aed;color:white;}}
.timer{{background:#d97706;color:white;}}
.cancel{{background:#475569;color:white;}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:10px;}}
.input{{width:100%;padding:15px;font-size:16px;border-radius:12px;border:none;margin:10px 0;}}
</style>
</head>
<body>
<div class="header">
<h1>🤖 PowerBot Robot Remote</h1>
<p style="color:#94a3b8;margin:5px 0;">Clean robot control • {local_ip}:{config.get('http_port', 8080)}</p>
</div>
<div class="status" id="status">
🔋 Battery: --% | 💻 CPU: --% | 🧠 RAM: --%
</div>
<div>
<p style="padding:0 15px;color:#94a3b8;">PIN Required: <span id="pinStatus">Yes (1234)</span></p>
</div>
<div class="grid">
<button class="btn shutdown" onclick="confirmAction('shutdown',0)">🛑 Shutdown</button>
<button class="btn restart" onclick="confirmAction('restart',0)">🔄 Restart</button>
<button class="btn sleep" onclick="confirmAction('sleep',0)">🌙 Sleep</button>
<button class="btn lock" onclick="confirmAction('lock',0)">🔒 Lock</button>
</div>
<div style="padding:10px;">
<input type="number" class="input" id="minutes" placeholder="Minutes for timer..." min="1">
<button class="btn timer" onclick="timerShutdown()">⏱️ Timer Shutdown</button>
<button class="btn cancel" onclick="cancelTimer()">❌ Cancel Timer</button>
</div>
<script>
let pin = '1234';
async function sendAction(path, delay=0){{
    const res = await fetch(path, {{
        method:'POST',
        headers:{{'Content-Type':'application/json','X-PIN':pin}},
        body:JSON.stringify({{delay_seconds:delay}})
    }});
    const data = await res.json();
    alert(data.message || data.status);
    updateStatus();
}}
async function confirmAction(action, delay){{
    if(confirm('Are you sure you want to '+action+'?')) {{
        sendAction('/api/action/'+action, delay);
    }}
}}
async function timerShutdown(){{
    const mins = document.getElementById('minutes').value;
    if(mins && mins>0) {{
        confirmAction('shutdown', mins*60);
    }}
}}
async function cancelTimer(){{
    sendAction('/api/action/cancel');
}}
async function updateStatus(){{
    try{{
        const res = await fetch('/api/status');
        const data = await res.json();
        document.getElementById('status').innerHTML = 
            `🔋 Battery: ${{data.battery?.percent||'--'}}% | 💻 CPU: ${{data.cpu_percent||'--'}}% | 🧠 RAM: ${{data.ram_percent||'--'}}%`;
    }}catch(e){{}}
}}
setInterval(updateStatus, 3000);
updateStatus();
</script>
</body>
</html>"""
        
        return Handler

class PowerBotDesktopApp:
    """Pure Python CustomTkinter GUI Application with System Tray"""
    
    def __init__(self, controller, http_server, config):
        self.controller = controller
        self.http_server = http_server
        self.config = config
        self.running = True
        self.voice_listening = False
        self.voice_thread = None
        self.recognizer = sr.Recognizer() if SPEECH_AVAILABLE else None
        
        # Initialize CustomTkinter
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.root = ctk.CTk()
        self.root.title("🤖 PowerBot Robot Controller")
        self.root.geometry("600x850")
        self.root.resizable(False, False)
        
        self.setup_ui()
        self.start_stats_polling()
        
    def ripple_effect(self, btn, action):
        orig = btn.cget("fg_color")
        btn.configure(fg_color="#ffffff")
        self.root.after(120, lambda: btn.configure(fg_color=orig))
        action()
        
        # System Tray
        self.setup_system_tray()
    
    def setup_ui(self):
        # Header
        header = ctk.CTkFrame(self.root, height=80)
        header.pack(fill="x", padx=20, pady=(20,10))
        header.pack_propagate(False)
        
        title = ctk.CTkLabel(header, text="🤖 PowerBot", font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(pady=(10,0))
        
        subtitle = ctk.CTkLabel(header, text=f"🤖 Clean robot control • {self.controller.get_local_ip()}:{self.config['http_port']}", font=ctk.CTkFont(size=11))
        subtitle.pack()
        
        # System Stats Card
        stats_card = ctk.CTkFrame(self.root, corner_radius=15)
        stats_card.pack(fill="x", padx=20, pady=10)
        
        stats_title = ctk.CTkLabel(stats_card, text="📊 System", font=ctk.CTkFont(size=16, weight="bold"))
        stats_title.pack(pady=10)
        
        stats_grid = ctk.CTkFrame(stats_card, fg_color="transparent")
        stats_grid.pack(fill="x", padx=15, pady=5)
        
        self.lbl_battery = ctk.CTkLabel(stats_grid, text="🔋 Battery: -", font=ctk.CTkFont(size=13))
        self.lbl_battery.grid(row=0, column=0, padx=15, pady=5, sticky="w")
        
        self.lbl_cpu = ctk.CTkLabel(stats_grid, text="💻 CPU: -", font=ctk.CTkFont(size=13))
        self.lbl_cpu.grid(row=0, column=1, padx=15, pady=5, sticky="w")
        
        self.lbl_ram = ctk.CTkLabel(stats_grid, text="🧠 RAM: -", font=ctk.CTkFont(size=13))
        self.lbl_ram.grid(row=1, column=0, padx=15, pady=5, sticky="w")
        
        self.lbl_ip = ctk.CTkLabel(stats_grid, text="🌐 IP: -", font=ctk.CTkFont(size=13))
        self.lbl_ip.grid(row=1, column=1, padx=15, pady=5, sticky="w")
        
        # Power Controls
        controls_card = ctk.CTkFrame(self.root, corner_radius=15)
        controls_card.pack(fill="x", padx=20, pady=10)
        
        controls_title = ctk.CTkLabel(controls_card, text="🚀 Power Actions", font=ctk.CTkFont(size=16, weight="bold"))
        controls_title.pack(pady=10)
        
        btn_grid = ctk.CTkFrame(controls_card, fg_color="transparent")
        btn_grid.pack(fill="x", padx=15, pady=5)
        
        self.btn_shutdown = ctk.CTkButton(btn_grid, text="🛑 SHUT DOWN", fg_color="#dc2626", hover_color="#b91c1c", height=50, font=ctk.CTkFont(size=14, weight="bold"), command=lambda: self.ripple_effect(self.btn_shutdown, self.confirm_shutdown))
        self.btn_shutdown.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.btn_restart = ctk.CTkButton(btn_grid, text="🔄 RESTART", fg_color="#ea580c", hover_color="#c2410c", height=50, font=ctk.CTkFont(size=14, weight="bold"), command=lambda: self.ripple_effect(self.btn_restart, self.confirm_restart))
        self.btn_restart.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.btn_sleep = ctk.CTkButton(btn_grid, text="🌙 SLEEP", fg_color="#2563eb", hover_color="#1d4ed8", height=50, font=ctk.CTkFont(size=14, weight="bold"), command=lambda: self.ripple_effect(self.btn_sleep, self.action_sleep))
        self.btn_sleep.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.btn_lock = ctk.CTkButton(btn_grid, text="🔒 LOCK", fg_color="#7c3aed", hover_color="#6d28d9", height=50, font=ctk.CTkFont(size=14, weight="bold"), command=lambda: self.ripple_effect(self.btn_lock, self.action_lock))
        self.btn_lock.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        btn_grid.grid_columnconfigure(0, weight=1)
        btn_grid.grid_columnconfigure(1, weight=1)
        
        # Timer Section
        timer_card = ctk.CTkFrame(self.root, corner_radius=15)
        timer_card.pack(fill="x", padx=20, pady=10)
        
        timer_title = ctk.CTkLabel(timer_card, text="⏱️ Shutdown Timer", font=ctk.CTkFont(size=16, weight="bold"))
        timer_title.pack(pady=10)
        
        timer_grid = ctk.CTkFrame(timer_card, fg_color="transparent")
        timer_grid.pack(fill="x", padx=15, pady=5)
        
        self.entry_minutes = ctk.CTkEntry(timer_grid, placeholder_text="Enter minutes (e.g. 15)", width=200)
        self.entry_minutes.grid(row=0, column=0, padx=5, pady=5)
        
        self.btn_sched = ctk.CTkButton(timer_grid, text="Schedule Shutdown", fg_color="#d97706", hover_color="#b45309", command=lambda: self.ripple_effect(self.btn_sched, self.action_timer_shutdown))
        self.btn_sched.grid(row=0, column=1, padx=5, pady=5)
        self.btn_cancel_timer = ctk.CTkButton(timer_grid, text="Cancel Timer", fg_color="#475569", hover_color="#334155", command=lambda: self.ripple_effect(self.btn_cancel_timer, self.action_cancel))
        self.btn_cancel_timer.grid(row=0, column=2, padx=5, pady=5)

        # Voice Control Section
        voice_card = ctk.CTkFrame(self.root, corner_radius=15)
        voice_card.pack(fill="x", padx=20, pady=10)

        voice_title = ctk.CTkLabel(voice_card, text="🎤 Voice Commands", font=ctk.CTkFont(size=16, weight="bold"))
        voice_title.pack(pady=10)

        voice_grid = ctk.CTkFrame(voice_card, fg_color="transparent")
        voice_grid.pack(fill="x", padx=15, pady=5)

        self.btn_voice = ctk.CTkButton(voice_grid, text="Start Listening", fg_color="#10b981", hover_color="#059669", command=lambda: self.ripple_effect(self.btn_voice, self.toggle_voice_listening))
        self.btn_voice.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.lbl_voice_status = ctk.CTkLabel(voice_grid, text="Voice: Off", font=ctk.CTkFont(size=13))
        self.lbl_voice_status.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        voice_grid.grid_columnconfigure(0, weight=1)

        self.lbl_voice_text = ctk.CTkLabel(voice_card, text="Say: 'shutdown', 'restart', 'sleep', 'lock', 'cancel timer', or 'shutdown in 10 minutes'", font=ctk.CTkFont(size=11), text_color="#94a3b8")
        self.lbl_voice_text.pack(pady=(0,10))
    
    def start_stats_polling(self):
        def poll():
            while self.running:
                try:
                    stats = self.controller.get_system_stats()
                    self.root.after(0, lambda s=stats: self.update_stats(s))
                except:
                    pass
                time.sleep(3)
        threading.Thread(target=poll, daemon=True).start()
    
    def update_stats(self, stats):
        bat = stats.get("battery", {})
        self.lbl_battery.configure(text=f"🔋 Battery: {bat.get('percent',0)}% {'🔌' if bat.get('plugged') else '🔋'}")
        self.lbl_cpu.configure(text=f"💻 CPU: {stats.get('cpu_percent',0):.0f}%")
        self.lbl_ram.configure(text=f"🧠 RAM: {stats.get('ram_percent',0):.0f}% ({stats.get('ram_used_gb',0)}GB)")
        self.lbl_ip.configure(text=f"🌐 IP: {stats.get('local_ip','-')}")
    
    def confirm_shutdown(self):
        if messagebox.askyesno("Confirm Shutdown", "Are you sure you want to SHUT DOWN your laptop now?"):
            result = self.controller.shutdown(0)
            messagebox.showinfo("Shutdown", result["message"])
    
    def confirm_restart(self):
        if messagebox.askyesno("Confirm Restart", "Are you sure you want to RESTART your laptop now?"):
            result = self.controller.restart(0)
            messagebox.showinfo("Restart", result["message"])
    
    def action_sleep(self):
        result = self.controller.sleep()
        messagebox.showinfo("Sleep", result["message"])
    
    def action_lock(self):
        result = self.controller.lock()
        messagebox.showinfo("Lock", result["message"])
    
    def action_timer_shutdown(self):
        try:
            mins = int(self.entry_minutes.get())
            if mins <= 0:
                raise ValueError
            result = self.controller.shutdown(mins * 60)
            messagebox.showinfo("Timer", result["message"])
        except:
            messagebox.showerror("Error", "Please enter a valid number of minutes")
    
    def action_cancel(self):
        result = self.controller.cancel_timer()
        messagebox.showinfo("Cancel", result["message"])

    def speak(self, text):
        if TTS_AVAILABLE and _tts_engine:
            try:
                _tts_engine.say(text)
                _tts_engine.runAndWait()
            except Exception:
                pass

    def toggle_voice_listening(self):
        if not SPEECH_AVAILABLE:
            messagebox.showerror("Voice Unavailable", "SpeechRecognition library not installed. Install SpeechRecognition and PyAudio.")
            return
        self.voice_listening = not self.voice_listening
        if self.voice_listening:
            self.btn_voice.configure(text="Stop Listening", fg_color="#ef4444", hover_color="#b91c1c")
            self.lbl_voice_status.configure(text="Voice: Listening...")
            self.voice_thread = threading.Thread(target=self.voice_listener_loop, daemon=True)
            self.voice_thread.start()
            self.speak("Voice control activated")
        else:
            self.btn_voice.configure(text="Start Listening", fg_color="#10b981", hover_color="#059669")
            self.lbl_voice_status.configure(text="Voice: Off")
            self.speak("Voice control deactivated")

    def voice_listener_loop(self):
        recognizer = self.recognizer
        mic = sr.Microphone()
        # Adjust for ambient noise once
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
        while self.voice_listening and self.running:
            try:
                with mic as source:
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                text = recognizer.recognize_google(audio).lower()
                self.root.after(0, lambda t=text: self.lbl_voice_text.configure(text=f"Heard: {t}"))
                self.root.after(0, lambda t=text: self.handle_voice_command(t))
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                continue
            except sr.RequestError:
                self.root.after(0, lambda: messagebox.showerror("Voice Error", "Speech recognition service unavailable"))
                break
            except Exception:
                continue

    def handle_voice_command(self, text):
        text = text.lower()
        # Custom URL shortcuts
        if "task" in text:
            url = "https://pegasus.pairlab.ai/xapp/dashboard"
            try:
                webbrowser.open(url)
                messagebox.showinfo("Voice Command", f"Opening {url}")
                self.speak("Opening task dashboard")
            except Exception as e:
                messagebox.showerror("Voice Command", f"Failed to open URL: {e}")
            return
        # Parse commands
        if "shutdown" in text:
            # Check for timer
            m = re.search(r"in (\d+) (minute|minutes|min)", text)
            if m:
                mins = int(m.group(1))
                result = self.controller.shutdown(mins * 60)
                messagebox.showinfo("Voice Command", f"Scheduled shutdown in {mins} minutes: {result['message']}")
                self.speak(f"Shutdown scheduled in {mins} minutes")
            else:
                if messagebox.askyesno("Voice Confirm", "Voice command: Shutdown now?"):
                    result = self.controller.shutdown(0)
                    messagebox.showinfo("Voice Command", result["message"])
                    self.speak("Shutting down")
        elif "restart" in text or "reboot" in text:
            if messagebox.askyesno("Voice Confirm", "Voice command: Restart now?"):
                result = self.controller.restart(0)
                messagebox.showinfo("Voice Command", result["message"])
                self.speak("Restarting")
        elif "sleep" in text or "suspend" in text:
            result = self.controller.sleep()
            messagebox.showinfo("Voice Command", result["message"])
            self.speak("Going to sleep")
        elif "lock" in text:
            result = self.controller.lock()
            messagebox.showinfo("Voice Command", result["message"])
            self.speak("Locking screen")
        elif "cancel" in text and ("timer" in text or "shutdown" in text):
            result = self.controller.cancel_timer()
            messagebox.showinfo("Voice Command", result["message"])
            self.speak("Timer cancelled")
        else:
            # Unrecognized
            pass
    
    def setup_system_tray(self):
        # Create robot tray icon
        def create_icon():
            image = Image.new('RGB', (64, 64), color='#0b0f19')
            draw = ImageDraw.Draw(image)
            # head rounded
            draw.ellipse([16, 12, 48, 48], fill='#1e3a8a', outline='#38bdf8', width=2)
            # eyes
            draw.ellipse([22, 22, 30, 32], fill='#38bdf8')
            draw.ellipse([34, 22, 42, 32], fill='#38bdf8')
            # eye pupils
            draw.ellipse([24, 24, 28, 28], fill='#0b0f19')
            draw.ellipse([36, 24, 40, 28], fill='#0b0f19')
            # antenna
            draw.line([32, 12, 32, 4], fill='#38bdf8', width=2)
            draw.ellipse([28, 0, 36, 8], fill='#38bdf8')
            # mouth
            draw.rectangle([24, 38, 40, 44], fill='#38bdf8', outline='#0b0f19', width=1)
            # cheek highlights
            draw.ellipse([18, 28, 22, 32], fill='#3b82f6')
            draw.ellipse([42, 28, 46, 32], fill='#3b82f6')
            return image
        
        def show_window(icon, item):
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
        
        def hide_window(icon, item):
            self.root.withdraw()
        
        def exit_app(icon, item):
            self.running = False
            self.root.quit()
            icon.stop()
            sys.exit(0)
        
        menu = pystray.Menu(
            pystray.MenuItem('Show Window', show_window),
            pystray.MenuItem('Hide Window', hide_window),
            pystray.MenuItem('Exit', exit_app)
        )
        
        try:
            self.tray = pystray.Icon("PowerBot", create_icon(), "🤖 PowerBot Robot Controller", menu)
            threading.Thread(target=self.tray.run, daemon=True).start()
        except:
            pass
    
    def run(self):
        self.root.mainloop()

def main():
    parser = argparse.ArgumentParser(description="Laptop PowerBot - Power control via CLI, GUI, or Voice")
    parser.add_argument('--shutdown', action='store_true', help='Shutdown system')
    parser.add_argument('--restart', action='store_true', help='Restart system')
    parser.add_argument('--sleep', action='store_true', help='Put system to sleep')
    parser.add_argument('--lock', action='store_true', help='Lock screen')
    parser.add_argument('--cancel', action='store_true', help='Cancel scheduled action')
    parser.add_argument('--delay', type=int, default=0, help='Delay in seconds')
    parser.add_argument('--minutes', type=int, help='Delay in minutes')
    args = parser.parse_args()

    print("="*60)
    print("🤖 PowerBot Robot - Pure Python Edition")
    print("="*60)
    
    # Load configuration
    config = load_config()
    controller = SystemPowerController()

    # CLI mode
    delay = args.delay
    if args.minutes:
        delay = args.minutes * 60

    if any([args.shutdown, args.restart, args.sleep, args.lock, args.cancel]):
        if args.shutdown:
            res = controller.shutdown(delay)
        elif args.restart:
            res = controller.restart(delay)
        elif args.sleep:
            res = controller.sleep()
        elif args.lock:
            res = controller.lock()
        elif args.cancel:
            res = controller.cancel_timer()
        print(json.dumps(res, indent=2))
        sys.exit(0)
    
    # Initialize components
    http_server = RemoteHTTPServer(controller, config)
    
    # Start HTTP server
    if config.get("server_running", True):
        if not http_server.start():
            print("⚠️  HTTP server failed to start")
    
    # Start Desktop GUI
    print("🚀 Launching Desktop GUI...")
    print(f"📱 Mobile Remote URL: http://{controller.get_local_ip()}:{config['http_port']}")
    print(f"🔑 PIN Code: {config.get('pin_code', '1234')}")
    print("="*60)
    
    app = PowerBotDesktopApp(controller, http_server, config)
    try:
        app.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        http_server.stop()
        save_config(config)

if __name__ == "__main__":
    main()
