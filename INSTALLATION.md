# GLOW Installation Guide

## For End Users (Non-Technical)

### One-Click Installer (Recommended)

1. **Download** the installer from GitHub Releases:
   - Go to [Releases](https://github.com/shivampal7405/GLOW/releases)
   - Download `GLOW-Setup-v1.0.5.exe`

2. **Run** the installer:
   - Double-click the downloaded file
   - If Windows Defender shows a warning, click "More info" → "Run anyway"
   - This is normal for new software without an expensive code signing certificate

3. **Choose** your AI model:
   - **Groq** (Recommended) - Fastest, free
   - **Gemini** - Vision-capable, free
   - **Claude** - Most intelligent, free tier

4. **Enter** your API key:
   - Get free key from your chosen provider (see below)
   - Paste it in the installer

5. **Finish** installation:
   - Click "Install"
   - Wait 1-2 minutes
   - Click "Finish"

6. **Launch** GLOW:
   - Double-click the desktop icon
   - Or find it in Start Menu → GLOW

**That's it! You're ready to go!** 🎉

---

## Getting Your Free API Key

### Option 1: Groq (Fastest - Recommended)

1. Go to [console.groq.com](https://console.groq.com)
2. Click "Sign in" → "Continue with Google" (or GitHub)
3. Once signed in, click "API Keys" in the left menu
4. Click "Create API Key"
5. Give it a name like "GLOW"
6. Copy the key (starts with `gsk_...`)
7. Paste it in GLOW installer

**Free Tier**: 14,400 requests/day

### Option 2: Google Gemini (Vision-Capable)

1. Go to [ai.google.dev](https://ai.google.dev)
2. Click "Get API key in Google AI Studio"
3. Sign in with your Google account
4. Click "Get API key" → "Create API key"
5. Copy the key (starts with `AIza...`)
6. Paste it in GLOW installer

**Free Tier**: 60 requests/minute

### Option 3: Anthropic Claude (Most Intelligent)

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign up for an account
3. Go to "API Keys"
4. Click "Create Key"
5. Copy the key (starts with `sk-ant-...`)
6. Paste it in GLOW installer

**Free Tier**: $5 credit for new users

---

## For Developers (Manual Installation)

### Prerequisites

- Windows 10/11 (64-bit)
- Python 3.10 or higher
- Git (optional)

### Step 1: Clone the Repository

```bash
git clone https://github.com/shivampal7405/GLOW.git
cd GLOW
```

Or download ZIP from GitHub and extract it.

### Step 2: Create Virtual Environment (Recommended)

```bash
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- PyQt6 (GUI framework)
- AI API clients (Groq, Gemini, Claude)
- Automation libraries (PyAutoGUI, pywin32)
- And 20+ other dependencies

**Note**: Installation may take 5-10 minutes.

### Step 4: Configure API Keys

Create `config.json` in the GLOW directory:

```json
{
  "conversational_model": "Groq (Fast API)",
  "groq_api_key": "your-groq-key-here",
  "gemini_api_key": "",
  "anthropic_api_key": "",
  "groq_model": "meta-llama/llama-4-maverick-17b-128e-instruct",
  "gemini_model": "gemini-3-flash-preview",
  "anthropic_model": "claude-sonnet-4-5-20250929",
  "enable_vision": false,
  "auto_listen": false,
  "tts_engine": "windows",
  "wake_word_enabled": false
}
```

Or copy `config.example.json` to `config.json` and edit it.

### Step 5: Run GLOW

**GUI Mode** (Recommended):
```bash
python glow_app.py
```

**CLI Mode** (Advanced):
```bash
python main.py
```

---

## Building the Installer (For Contributors)

### Prerequisites

- Python 3.10+
- PyInstaller: `pip install pyinstaller`
- Inno Setup: Download from [jrsoftware.org](https://jrsoftware.org/isdl.php)

### Step 1: Build Executable

```bash
python build_installer.py
```

Or use the spec file:
```bash
pyinstaller GLOW.spec
```

This creates `dist/GLOW.exe`

### Step 2: Test the Executable

```bash
cd dist
GLOW.exe
```

Make sure it runs without errors.

### Step 3: Build Installer

1. Open Inno Setup Compiler
2. File → Open → Select `installer.iss`
3. Build → Compile
4. Find the installer in `installer_output/GLOW-Setup-v1.0.5.exe`

### Step 4: Test the Installer

Run the installer on a clean Windows VM or test machine.

---

## Troubleshooting

### Installer Issues

**"Windows protected your PC"**
- Click "More info" → "Run anyway"
- This is because the app isn't code-signed (costs $300+/year)

**"Installation failed"**
- Run as Administrator
- Disable antivirus temporarily
- Check disk space (needs ~500 MB)

### Runtime Issues

**"API Key Invalid"**
- Verify you copied the entire key
- Check for extra spaces
- Make sure key is from correct provider

**"Module not found"**
- Reinstall dependencies: `pip install -r requirements.txt`
- Try in a fresh virtual environment

**"GLOW won't start"**
- Check `config.json` is valid JSON
- Look for errors in console (CLI mode)
- Try deleting `config.json` and reconfigure

**"Vision mode not working"**
- Make sure you selected Gemini model
- Set `"enable_vision": true` in config.json
- Check your Gemini API key is valid

### Performance Issues

**"GLOW is slow"**
- Switch to Groq model (fastest)
- Close other applications
- Check your internet connection

**"High CPU usage"**
- This is normal during AI processing
- Reduce concurrent tasks

---

## System Requirements

### Minimum
- **OS**: Windows 10 (64-bit)
- **RAM**: 4 GB
- **Disk**: 500 MB free space
- **Internet**: For AI API calls

### Recommended
- **OS**: Windows 11 (64-bit)
- **RAM**: 8 GB or more
- **Disk**: 1 GB free space
- **Internet**: Broadband connection

---

## Optional Dependencies

### Tesseract OCR (For OCR features)

1. Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
2. Install to `C:\Program Files\Tesseract-OCR`
3. Add to PATH or GLOW will auto-detect

### VS Code (For code editing features)

1. Download from [code.visualstudio.com](https://code.visualstudio.com)
2. Install normally
3. GLOW will auto-detect it

---

## Uninstalling

### If Installed with Installer

1. Control Panel → Programs and Features
2. Find "GLOW"
3. Click Uninstall
4. Follow prompts

### If Installed Manually

1. Delete the GLOW folder
2. Delete virtual environment (if created)
3. That's it!

---

## Updating

### Installer Version

1. Download new installer
2. Run it (will update existing installation)

### Manual Installation

```bash
cd GLOW
git pull origin main
pip install -r requirements.txt --upgrade
```

---

## Privacy & Security

- **Local Processing**: GLOW runs entirely on your PC
- **No Telemetry**: We don't collect any data
- **API Calls**: Only sent to your chosen AI provider
- **Your Data**: Never leaves your computer (except AI API calls)
- **Open Source**: All code is public and auditable

---

## Support

- 📖 Read the [README](README.md)
- 🎓 Check [Quick Start Guide](QUICK_START.md)
- 🐛 Report bugs on [GitHub Issues](https://github.com/shivampal7405/GLOW/issues)
- 💬 Ask questions in [Discussions](https://github.com/shivampal7405/GLOW/discussions)

---

**Happy automating with GLOW! 🌟**
