# 🛡️ MiniFIM — File Integrity Monitor

A modern, dark-themed File Integrity Monitoring (FIM) tool built with Python and CustomTkinter. Tracks file changes in real time and detects unauthorized modifications, creations, and deletions with a premium security-dashboard UI.

---
<img width="1061" height="728" alt="image" src="https://github.com/user-attachments/assets/57828ec1-bcb3-429a-8cf5-4c40883ba0d7" />


## 🚀 Features

* 🌑 **Dark Mode UI** — Sleek, modern interface built with CustomTkinter
* 📊 **Live Dashboard** — Real-time stats: files monitored, changes detected, scan interval, uptime
* 📂 **Directory Monitoring** — Monitor any folder with SHA-256 integrity verification
* 🎨 **Color-Coded Alerts** — INFO (cyan), WARNING (yellow), CRITICAL (red) severity levels
* ⚠️ **Detects:**
  * 🟡 File creation (WARNING)
  * 🟡 File modification (WARNING)
  * 🔴 File deletion (CRITICAL)
* 📋 **Baseline Viewer** — Browse all tracked files and their SHA-256 hashes
* ⚙️ **Configurable Settings:**
  * Adjustable scan interval (1–60 seconds)
  * File exclusion patterns (glob-based)
  * Desktop notification toggle
* 📤 **CSV Export** — Export all logs to CSV for reporting
* 🔔 **Desktop Notifications** — Toast alerts for critical file events
* 🟢 **Animated Status Indicator** — Pulsing dot shows monitoring state
* 📝 **Persistent Logging** — All alerts saved to `fim_alerts.log`
* ⚡ **Parallel File Hashing** — Multi-threaded SHA-256 hashing (8 workers) for fast baseline building on large directories
* 🧭 **Bold Sidebar Navigation** — Large, prominent navigation buttons for Monitor, Baseline, and Settings views

---

## 📸 Interface

The app features a sidebar navigation with three views:

| View | Description |
|------|-------------|
| 📊 **Monitor** | Main dashboard with live stats, controls, and color-coded log |
| 📋 **Baseline** | Table of all monitored files with their SHA-256 hashes and sizes |
| ⚙️ **Settings** | Scan interval slider, exclusion patterns, notification toggle |

---

## 🛠️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/MiniFIM.git
cd MiniFIM
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the program

```bash
python main.py
```

---

## ⚠️ Requirements

* Python 3.8+
* `customtkinter` — Modern dark-themed UI widgets
* `plyer` — Cross-platform desktop notifications (optional, graceful fallback)

---

## 📁 Project Structure

```
MiniFIM/
├── main.py              # Entry point
├── app.py               # Main GUI application (CustomTkinter)
├── monitor.py           # File monitoring engine
├── notifier.py          # Desktop notification logic
├── utils.py             # Hashing, CSV export, file utilities
├── theme.py             # Color palette, fonts, style constants
├── requirements.txt     # Python dependencies
├── fim_baseline.json    # Baseline data (auto-generated)
├── fim_alerts.log       # Alert log (auto-generated)
└── README.md
```

---

## 🧪 Testing Tips

Try these to see alerts in action:

* Create a new file inside the monitored folder → 🟡 WARNING
* Edit an existing file → 🟡 WARNING
* Delete a file → 🔴 CRITICAL

---

## ⚡ Performance

MiniFIM uses **multi-threaded parallel hashing** via Python's `ThreadPoolExecutor` with 8 concurrent workers. Instead of hashing files one-by-one, all files in the monitored directory are hashed simultaneously, making baseline creation and scan cycles significantly faster — especially on directories with hundreds or thousands of files.

---

## ⚙️ Configuration

### Scan Interval
Adjust in the Settings panel (1–60 seconds slider) or in code:
```python
monitor.set_scan_interval(5)  # seconds
```

### Exclusion Patterns
Add glob patterns in Settings to ignore files:
```
*.tmp
*.log
__pycache__/*
.git/*
```

---

## 🔒 Disclaimer

This tool is intended for **educational and defensive security purposes only**.
Do not use it for unauthorized monitoring of systems you do not own or have permission to analyze.

---
