# OmniBot Architect: Multimodal Vision-to-Bot Developer

**OmniBot Architect** is an autonomous, multimodal Python system that converts UI screenshots, mockups, wireframes, and workflow video recordings into fully functional, production-ready Python automation bots.

---

## 📁 Package Contents

```
omnibot_architect/
├── omnibot_architect.py  # Core CLI and Multimodal Developer Engine
├── example_run.py        # Programmatic Python API usage example
├── requirements.txt      # Python dependencies
├── config.example.json   # Configuration template
└── README.md             # Complete Documentation
```

---

## 🚀 Quick Start Guide

### 1. Setup Virtual Environment & Install Dependencies
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install -r requirements.txt

# Install Playwright browser drivers
playwright install
```

### 2. Set API Key
```bash
export GEMINI_API_KEY="your_api_key_here"
```

### 3. Usage Examples

#### Web Automation (Playwright) with Screenshots
```bash
python omnibot_architect.py \
  --prompt "Automate logging into this portal, navigating to reports, and downloading the CSV." \
  --images screen1.png screen2.png \
  --type playwright \
  --out web_bot.py
```

#### Desktop GUI Automation (PyAutoGUI) from Video Demonstration
```bash
python omnibot_architect.py \
  --prompt "Replicate the exact mouse movements and clicks shown in the video recording." \
  --video workflow_recording.mp4 \
  --type pyautogui \
  --out desktop_bot.py
```

#### API / Telegram Bot Generation
```bash
python omnibot_architect.py \
  --prompt "Build a Telegram bot that accepts image uploads, checks prices, and replies with alerts." \
  --type telegram \
  --out telegram_bot.py
```

---

## 🛡️ Key Features
- **Multimodal Video & Image Ingestion**: Analyzes video recordings frame-by-frame or via native cloud video streaming to understand UI user actions.
- **AST Code Validation**: Ensures synthetic code passes Python abstract syntax tree parsing before delivery.
- **Autonomous Self-Healing**: Automatically catches compilation errors and feeds the stack trace back into Gemini for iterative code repair.
- **Multi-Framework Support**: Generates Playwright, Selenium, PyAutoGUI, OpenCV, or API-based bots on demand.
