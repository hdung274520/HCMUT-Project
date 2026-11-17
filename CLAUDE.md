# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Student research project (HCMUT): a voice assistant that answers questions about the user's own physiological data. Data flows:

```
Sensors (BLE) ──► Raspberry Pi gateway ──► AWS (API Gateway + Lambda + DynamoDB) ──► Web dashboard ──► Voice agent
Muse 2 (EEG+PPG)    04_Data/gateway/          03_Code/02_aws-services/                  03_Code/04_web-app/  03_Code/01_audio-agent/
Magene H303 (HR/RR)
Yuwell YX110 (SpO2)
```

- **Gateway** (`04_Data/gateway/`, runs on the Pi as `~/sensors/gateway`): `gateway.py` reads all three sensors at once with `bleak`, writes per-second features (`features.py`) into an offline SQLite queue `queue.db`, and on exit writes a session summary (`session.py`, shaped like `active_session_schema.json`). `upload.py` runs from cron every minute and POSTs unsent rows (`sent=0`) to AWS with `x-api-key`; rows have unique keys so re-inserts are no-ops. Needs `SENSORS_API` / `SENSORS_API_KEY` env. The gateway reuses the BLE parsers from the per-device folders (`muse2/decode.py`, `magene_h303/dashboard_server.py`, `yuwell_yx110/dashboard_server.py`) — they are loaded by path because the dashboards share module names.
- **AWS** (`03_Code/02_aws-services/`, SAM, region `ap-southeast-1`): `template.yaml` defines three DynamoDB tables (Sessions, SpotMeasurements, DailyVitals; all keyed by `user_id` + time) and Lambdas `sessions.py`, `measurements.py`, `daily.py` behind one API-key-protected REST API (`/sessions`, `/measurements`, `/vitals/daily`, `/vitals/latest`). `daily.py` also runs nightly at 00:05 Asia/Ho_Chi_Minh to fold the previous day into DailyVitals. `api.respond()` is the shared response helper (converts DynamoDB `Decimal`).
- **Web app** (`03_Code/04_web-app/`, plain HTML/CSS/JS, no build step): deployed on GitHub Pages (root `index.html` redirects there). `app.js` uses the AWS API when `config.js` defines `API_URL`; with no `config.js` it is in DEMO mode and loads `data/*.json`. `config.js` is gitignored — never commit secrets into it. Moving to Cognito login for real data is in progress (see `00_Tasks/08_*`).
- **Voice agent** (`03_Code/01_audio-agent/`): STT → LLM → TTS, each provider chosen via env (`MODE=api|local`, or `STT_PROVIDER`/`LLM_PROVIDER`/`TTS_PROVIDER`; see `.env.example`, `src/config.py`). `server.py` (FastAPI) streams PCM16 over WebSocket with VAD turn detection and barge-in, serves `../04_web-app` as its UI, and logs each turn to `logs/response_times.csv`. Live vitals reach the LLM through a system prompt built in the browser (`resolve_system_prompt` in `src/llm.py`). In production it runs on EC2 via `docker-compose.yml` (Ollama + agent); model defaults come from benchmarks documented in its README — set `WHISPER_MODEL` explicitly there, since blank auto-picks by hardware.

## Schemas

JSON schemas in `04_Data/schemas/` are the data contract. `active_session`, `daily_vitals` and `spot_measurement` are **copied** into `03_Code/02_aws-services/src/` (the Lambdas validate against them) — change both copies together. CI (`.github/workflows/ci.yml`) only runs `python 03_Code/validate_schemas.py`.

## Commands

```bash
# Schema validation (what CI runs)
python 03_Code/validate_schemas.py

# Tests (pytest, each component has its own venv)
cd 03_Code/02_aws-services && venv/bin/python -m pytest -q
cd 04_Data/gateway && venv/bin/python -m pytest -q
cd 04_Data/muse2 && python -m pytest -q test_decode.py
# single test: append e.g. test_upload.py::test_spot_row_matches_schema

# Deploy AWS (check the changeset never Deletes a table)
cd 03_Code/02_aws-services && sam build && sam deploy

# Voice agent (conda env from setup.sh, Python 3.11)
cd 03_Code/01_audio-agent && conda activate voice-agent
python server.py          # http://localhost:8000; /test, /test2, /test3 = STT/TTS/LLM benchmark pages
python run.py --text      # CLI, typed input

# Gateway on the Pi
cd ~/sensors/gateway && venv/bin/python gateway.py --minutes 3
```

## Project conventions

- Planning lives in `00_Tasks/` (one file per week, Vietnamese, checkbox tasks with "Đạt khi" acceptance criteria); weekly reports in `02_Outputs/report/`. Tasks, reports and the PR template are written in Vietnamese; code and comments in English.
- Conventional commits: `feat(scope): ...`, `fix`, `docs`, `chore`, `test`, `refactor` (see `GIT_WORKFLOW_GUIDE.md`).
- Code style is deliberately minimal; known limits are marked with `# shortcut: <limit>, <when to upgrade>` comments.
- Hardware constraints (Pi 4 with 4 GB RAM, dev PC with no NVIDIA GPU) are in `device_constraints.yaml`.
- README's directory tree is partly stale (e.g. theory docs are now in `02_Outputs/theory/`); trust the filesystem.
