# Medical Signal Audio Assistant (EEG, Sleep & Vital Monitoring)

An AI-powered, real-time Audio Agent integrated with AWS cloud services and a mobile application, specifically designed for monitoring, analyzing, and reporting medical signals (such as EEG sleep stages, blood pressure, and other physiological vital signs).

---

## Project Overview

This research and development project aims to bridge the gap between physiological signal acquisition and hands-free, user-friendly interaction. By employing state-of-the-art voice technologies, secure cloud analytics, and accessible mobile interfaces, the system enables users and healthcare professionals to monitor critical medical signals seamlessly.

### Core Components

1. **Audio Agent**
   * Real-time voice assistant enabling users to query their sleep metrics, ask about blood pressure levels, and receive voice-guided notifications or health recommendations.
   * Leverages local or cloud-based LLM, TTS, and STT pipelines.

2. **AWS Services Integration**
   * Secure cloud computing infrastructure for storing raw medical signals.
   * Automated pipelines for signal processing, anomaly detection, and running machine learning models.
   * Ensures high scalability, reliability, and security compliance for health data.

3. **Mobile Application**
   * User-friendly mobile dashboard showing real-time graphs and historical analysis.
   * Receives notifications from the Audio Agent and reads stats from AWS cloud databases (sensor data is uploaded by the Raspberry Pi, not the phone).

---

## Directory Structure

```text
/home/hdung274520/Project/
├── README.md                         <-- This document (Project introduction & guide)
├── device_constraints.yaml            <-- Hardware resource constraints configuration
├── 01_Documents/                     <-- Research documents, books, and reference guides
│   ├── 02_cambridge-core_how-to-read-an-eeg_31Aug2025/  <-- Reference book: How to Read an EEG (PDFs)
│   ├── 23_AETA2025_ID63.pdf          <-- Literature reference paper
│   ├── yy_Brainstorms/               <-- Brainstorming slides and notes
│   │   └── 01_Brainstorm 11 06 2026.pdf
│   └── zz_Mininotes.gdoc             <-- Project scratchpad and notes
├── 03_Outputs/                       <-- Reports, pipelines, and publications outputs
│   ├── 01_Pipeline.md                <-- System pipeline architecture design (Markdown)
│   ├── 02_Conda.md                   <-- Conda environment setup instructions
│   └── 03_CLI.md                     <-- Command Line Interface documentation
├── GIT_WORKFLOW_GUIDE.md             <-- Cẩm nang quản lý phiên bản với Git & GitHub CI/CD
├── 04_Code/                          <-- Source code of the actual implementation
│   ├── 01_audio-agent/               <-- Core Voice Agent & Edge Client (FastAPI, Vosk/Whisper, Piper, Gemini)
│   ├── 02_aws-services/              <-- Cloud Infrastructure on AWS (Being rebuilt)
│   ├── 03_mobile-app/                <-- iOS/Android mobile dashboard (React Native / Expo) (Planned)
│   └── 04_web-app/                   <-- Web Dashboard for monitoring sleep, eeg & vitals
├── 05_Data/                          <-- Dataset storage & JSON Schemas (user profile, active session, vitals)
├── 06_Models/                        <-- Trained AI models and neural net checkpoints
└── 07_Experiments/                   <-- Performance metrics, logs, and evaluation reports
```

---

## Getting Started (Ubuntu Linux Development Environment)

This project is fully designed and configured to run on **Ubuntu Linux 26.04 LTS** (as the development/bridge machine) and **Raspberry Pi OS / Linux** (on the Raspberry Pi 4 edge device). Windows compatibility is not supported.

### 1. Prerequisites Installation on Ubuntu

To configure your Ubuntu development machine, install the required packages:

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python 3, build tools, audio and Bluetooth libraries
sudo apt install -y python3 python3-pip python3-venv python3-dev build-essential git curl \
    bluez libbluetooth-dev ffmpeg libsndfile1 portaudio19-dev

# Install Node.js 22 (shipped in the Ubuntu 26.04 repositories)
sudo apt install -y nodejs npm

# Verify installations
python3 --version
node --version
npm --version
```

### 2. Setting Up the Environment (Audio Agent)

The quickest way is the one-shot setup script (installs Miniconda if needed, creates the `voice-agent` Conda env with Python 3.11):

```bash
cd 04_Code/01_audio-agent
bash setup.sh
conda activate voice-agent
```

Alternatively, use a plain virtual environment:

```bash
cd 04_Code/01_audio-agent
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. AWS CLI Setup on Ubuntu

Install and configure the AWS CLI to interact with the backend services:

```bash
# Install AWS CLI
sudo apt install -y awscli

# Configure default profile
aws configure --profile default
# (Enter your AWS Access Key, Secret Key, and region "ap-southeast-1")
```

### 4. Raspberry Pi 4 Connection & Deployment

Since the Audio Agent (with local STT/TTS) and all sensor connections run directly on the Raspberry Pi 4, use SSH to sync code and control the edge gateway from Ubuntu. The Pi is the only gateway that uploads sensor data to AWS (there is no 24/7 wearable):

| Sensor | Measures | Link to Pi |
|---|---|---|
| Muse 2 | EEG (4 channels, 256 Hz) + PPG heart rate | BLE (BrainFlow) |
| Magene H303 | ECG heart rate + RR intervals (HRV) | BLE Heart Rate Service |
| Yuwell YX110 | SpO₂ + pulse (spot measurement) | Bluetooth |

```bash
# Connect to Raspberry Pi via SSH from Ubuntu terminal
ssh pi@<raspberry-pi-ip-address>

# Pair and trust each sensor (Muse 2, Magene H303, Yuwell YX110) via bluetoothctl on Raspberry Pi 4 / Ubuntu:
bluetoothctl
[bluetooth]# power on
[bluetooth]# scan on
[bluetooth]# pair <DEVICE_MAC_ADDRESS>
[bluetooth]# trust <DEVICE_MAC_ADDRESS>
[bluetooth]# connect <DEVICE_MAC_ADDRESS>
```

### 5. Version Control & CI with GitHub

- **Workflow Guide**: Refer to [GIT_WORKFLOW_GUIDE.md](file:///home/hdung274520/Project/GIT_WORKFLOW_GUIDE.md) for branch strategy, commit conventions, tags, and secrets management.
- **Automated CI**: Runs on every pull request / push to validate JSON schemas (`.github/workflows/ci.yml`).

