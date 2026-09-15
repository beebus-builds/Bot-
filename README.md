# ⚡ Laptop PowerBot - Pure Python Edition

A complete **pure Python** desktop application for remotely controlling your laptop's power functions.

## ✨ Features

### 🔌 Power Management
- **Shut Down** - Instant or delayed shutdown
- **Restart** - Reboot system immediately or with timer
- **Sleep** - Put laptop into suspend mode
- **Lock Screen** - Lock Windows session
- **Cancel Timer** - Cancel scheduled shutdown/restart

### 📱 Remote Access
- **Mobile Web Control** - Access from any phone/browser on same Wi-Fi
- **QR Code Pairing** - Scan QR code to connect instantly
- **Real-time System Stats** - Live battery, CPU, RAM monitoring
- **PIN Protection** - Secure access with configurable PIN code

### 🖥️ Desktop Application
- **Pure Python GUI** - Built with CustomTkinter (no JavaScript)
- **System Tray Integration** - Run in background, minimize to tray
- **Modern Dark UI** - Sleek, responsive interface
- **Live Metrics** - Real-time system information display

## 🚀 Installation

1. **Install Python 3.10+**
   
2. **Install Required Libraries**
   ```bash
   pip install -r requirements.txt
   ```
   
   Or install manually:
   ```bash
   pip install customtkinter pystray Pillow psutil qrcode
   ```

3. **Run the Bot**
   ```bash
   python Unified_Laptop_Power_Bot.py
   ```

## 🎮 Usage

### Desktop GUI
- Launch the app to see the control panel
- Buttons for immediate shutdown, restart, sleep, lock
- Timer input for delayed shutdown
- System stats update automatically
- Minimize to system tray for background operation

### Mobile Remote Control
1. Run the bot on your laptop
2. Note the displayed URL (e.g., `http://192.168.1.100:8080`)
3. Open that URL on your phone (same Wi-Fi network)
4. Scan QR code directly from desktop app for instant access
5. Use PIN `1234` (default, configurable) for security

## ⚙️ Configuration

Edit `bot_config.json` to customize:
```json
{
  "pin_code": "1234",
  "require_pin": true,
  "http_port": 8080,
  "auto_start": false,
  "server_running": true
}
```

## 📁 Files

- `Unified_Laptop_Power_Bot.py` - Main application (single file)
- `requirements.txt` - Python dependencies
- `bot_config.json` - Configuration file (auto-generated)
- `system_controller.py` - Power management module (optional)

## 🔒 Security

- PIN code protection for all power actions
- Local network only (no internet exposure)
- No external dependencies or cloud services
- Pure Python - fully auditable code

## 🛠️ Pure Python Libraries Used

- **customtkinter** - Modern GUI framework
- **pystray** - System tray integration
- **Pillow** - Image generation for tray icon
- **psutil** - System metrics monitoring
- **qrcode** - QR code generation for pairing
- **http.server** - Built-in Python HTTP server (no FastAPI)

## 📝 License

MIT - Free to use and modify

## 🤝 Support

Pure Python implementation - no Node.js, no Telegram, no external services required!
