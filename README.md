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
   * Receives notifications from the Audio Agent and synchronization of stats with AWS cloud databases.

---

## Directory Structure

```text
/home/hdung274520/Project/
├── README.md                      <-- This document (Project introduction & guide)
├── 00_References.gsheet           <-- Shared Google Sheet for references and literature search
├── 01_Documents/                  <-- Research documents, books, and reference guides
│   ├── 02_cambridge-core.../      <-- Reference book: How to Read an EEG
│   ├── 03_Kotai-VoiceAgent/       <-- Sample code template (Local voice assistant reference)
│   ├── 23_AETA2025_ID63.pdf       <-- Literature reference paper
│   ├── yy_Brainstorms/            <-- Initial brainstorming notes
│   └── zz_Mininotes.gdoc          <-- Project scratchpad and notes
├── 02_Tasks.gsheet                <-- Project timeline, task allocation, and milestones
├── 03_Outputs/                    <-- Reports, pipelines, and publications outputs
│   └── 01_Pipeline.gdoc           <-- System pipeline flow design link
├── 04_Code/                       <-- Source code of the actual implementation
│   ├── audio-agent/               <-- Voice agent backend scripts and configurations
│   ├── aws-services/              <-- Cloud Infrastructure as Code, Lambda functions, APIs
│   └── mobile-app/                <-- Frontend code for the iOS/Android mobile dashboard
├── 05_Data/                       <-- Dataset storage
│   ├── raw/                       <-- Unprocessed medical signals (e.g., EDF, CSV)
│   ├── processed/                 <-- Cleaned, filtered, and epoched sleep/vital sign data
│   └── metadata/                  <-- Subject metadata, channel mappings, and labels
├── 06_Models/                     <-- Trained AI models and neural net checkpoints
└── 07_Experiments/                <-- Performance metrics, logs, and evaluation reports
```

---

## Getting Started

### Prerequisites
* **Python 3.10+** (for Audio Agent & AWS Lambda local tests)
* **Node.js 18+** & **npm/pnpm/yarn** (for Mobile App development)
* **AWS CLI** (configured with appropriate IAM permissions)

*(Instructions for setting up the environment, deploying the AWS stack, and launching the mobile dashboard will be updated here as development progresses.)*
