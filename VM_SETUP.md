# Workshop VM Setup Guide

Instructions for setting up the AI Refinery demo environment on cloud VMs.

---

## Prerequisites

- VPN connected
- VM login credentials (provided by workshop organizer)
- VM OS: Windows with WSL (Ubuntu)

---

## Setup Steps

### 1. Connect to the VM

1. Connect to the corporate VPN.
2. RDP into your assigned VM using the provided credentials.
3. Open **Windows Terminal** or **Ubuntu (WSL)** from the Start menu.

### 2. Download the Code

The demo code is hosted on Azure Blob Storage. Download and extract it inside WSL:

```bash
cd ~
curl -o air.zip "https://arss1caterstg01.blob.core.windows.net/demo/air.zip"
unzip air.zip
```

If `curl` is not available:

```bash
wget -O air.zip "https://arss1caterstg01.blob.core.windows.net/demo/air.zip"
unzip air.zip
```

If `unzip` is not installed:

```bash
sudo apt install -y unzip
unzip air.zip
```

### 3. Run the Setup Script

```bash
cd air-demo-v2
bash setup.sh
```

This will:
- Detect Python 3.10+ on the system
- Create a virtual environment (`venv/`)
- Install all Python dependencies
- Install Node.js (needed for one of the demos)

The setup takes approximately 2-5 minutes depending on network speed.

### 4. Verify the Setup

After `setup.sh` completes, you should see:

```
airefinery-sdk ... OK
Core packages ... OK
MCP packages  ... OK
Setup complete!
```

If all three show `OK`, the VM is ready for the workshop.

---

## If Setup Fails

A detailed manual setup guide is included in the repo:

```bash
cat ONBOARDING.md
```

This document covers each step individually with fixes for common issues (blocked apt repos, missing packages, proxy settings, etc.).

---

## Quick Verification — Run a Demo

To confirm everything works end-to-end:

```bash
source venv/bin/activate
cd FlowSuperAgent-v2
python app_ui.py
```

Open a browser on the VM and go to `http://localhost:8000`. Type a test query (e.g., `My internet keeps dropping`). If you get a response, the VM is ready.

Press `Ctrl+C` to stop the server.

---

## Checklist

Use this checklist for each VM:

- [ ] VPN connected, RDP into VM
- [ ] Code downloaded and extracted (`~/air-demo-v2/`)
- [ ] `bash setup.sh` completed successfully
- [ ] Verification shows all three `OK`
- [ ] Test demo responds at `http://localhost:8000`
