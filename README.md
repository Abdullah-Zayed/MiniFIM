# 🛡️ MiniFIM - File Integrity Monitor

<img width="943" height="730" alt="image" src="https://github.com/user-attachments/assets/0b48a21f-d919-46f9-818c-8d7c1d14c1e1" />

A lightweight File Integrity Monitoring (FIM) tool built with Python that tracks changes in files and detects unauthorized modifications, creations, and deletions in real time.

---

## 🚀 Features

* 📂 Monitor any selected directory
* 🔐 SHA-256 hashing for file integrity verification
* ⚠️ Detects:

  * File creation
  * File modification
  * File deletion
* 🖥️ Simple GUI built with Tkinter
* 📝 Real-time logging of alerts
* 💾 Baseline storage using JSON

---

## 🧠 How It Works

MiniFIM creates a **baseline snapshot** of all files in a selected directory using SHA-256 hashes.

It then continuously scans the directory and compares current file states against the baseline:

* **New File** → 🚨 Alert triggered
* **Modified File** → 🚨 Alert triggered
* **Deleted File** → 🚨 Alert triggered

Example:

If a file’s content changes (even slightly), its hash changes → detected immediately.

---

## 📸 Interface Overview

* Select folder to monitor
* Start/Stop monitoring
* Real-time integrity logs
* Status indicator

---

## 🛠️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/MiniFIM.git
cd MiniFIM
```

### 2. Run the program

```bash
python main.py
```

---

## ⚠️ Requirements

* Python 3.x
* No external dependencies (uses standard library only)

---

## 🧪 Testing Tips

Try these to see alerts in action:

* Create a new file inside the monitored folder → 🚨
* Edit an existing file → 🚨
* Delete a file → 🚨

---

## ⚙️ Configuration

You can adjust monitoring behavior in the code:

```python
time.sleep(3)  # Scan interval (seconds)
```

---

## 🔒 Disclaimer

This tool is intended for **educational and defensive security purposes only**.
Do not use it for unauthorized monitoring of systems you do not own or have permission to analyze.



---
