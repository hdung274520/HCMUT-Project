# Graph Report - Project  (2026-11-21)

## Corpus Check
- 80 files · ~100,780 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 19 file(s) not represented in the graph (top: .jsonl 11, (none) 5, .tex 1)

## Summary
- 1477 nodes · 2035 edges · 111 communities (94 shown, 17 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 75 edges (avg confidence: 0.83)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7f8af58d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Bluetooth Sensor Acquisition
- Cloud API & Daily Vitals
- EEG Session Analysis
- Web Dashboard & Voice UI
- User Profile Data Model
- properties
- User Profile Data Model
- Telemetry JSON Schemas
- Telemetry JSON Schemas
- EEG Session Analysis
- EEG Reference Documentation
- EEG Session Analysis
- Cloud API & Daily Vitals
- Cloud API & Daily Vitals
- Cloud API & Daily Vitals
- server.py
- Bluetooth Sensor Acquisition
- properties
- llmsurveyproviderspy Component
- Cloud API & Daily Vitals
- ttspy Component
- EEG Session Analysis
- Cloud API & Daily Vitals
- EEG Session Analysis
- Telemetry JSON Schemas
- Cloud API & Daily Vitals
- Web Dashboard & Voice UI
- startup Component
- agentpy Component
- metadata
- EEG Session Analysis
- Syncope Component
- ttssurveyproviderspy Component
- EEG Session Analysis
- EEG Session Analysis
- Ekg Artifact Component
- EEG Session Analysis
- EEG Session Analysis
- EEG Session Analysis
- Cloud API & Daily Vitals
- EEG Session Analysis
- Cloud API & Daily Vitals
- runpy Component
- EEG Session Analysis
- Cloud API & Daily Vitals
- EEG Session Analysis
- Telemetry JSON Schemas
- Cloud API & Daily Vitals
- configpy Component
- Cloud API & Daily Vitals
- Telemetry JSON Schemas
- Cloud API & Daily Vitals
- properties
- properties
- EEG Session Analysis
- type
- EEG Session Analysis
- downloadmodelspy Component
- synth_question_audio
- assistantalertsjson Component
- EEG Session Analysis
- EEG Session Analysis
- Cloud API & Daily Vitals
- EEG Session Analysis
- Telemetry JSON Schemas
- Telemetry JSON Schemas
- Cloud API & Daily Vitals
- user_profile_schema.json
- Hyperventilation Component
- Alpha PSD figure (Muse 2, eyes open vs closed)
- Web Dashboard & Voice UI
- properties
- Telemetry JSON Schemas
- Phase 1 Project init Component
- Benign Sporadic Sleep Spi Component
- Epileptiform Discharges Component
- Periodic Discharges Component
- Cloud API & Daily Vitals
- Cloud API & Daily Vitals
- Cloud API & Daily Vitals
- Cloud API & Daily Vitals
- Concurrent BLE test Pi wifi-on (0 drops)
- Magene H303 dashboard pag Component
- Muse 2 dashboard page Component
- Telemetry JSON Schemas
- Telemetry JSON Schemas
- Telemetry JSON Schemas
- Cloud API & Daily Vitals
- Cloud API & Daily Vitals
- Cloud API & Daily Vitals
- Cloud API & Daily Vitals
- Electrographic Seizure Component
- How to Write an EEG Report (How to Read an EEG)
- Health Hub Vitals page (DEMO data)
- CLI guide Component
- Phase 4 Data acquisition Component
- Index How to Read an EEG Component
- Brainstorm 11-06-2026 (image-only PDF)
- Web Dashboard & Voice UI
- Web Dashboard & Voice UI
- Web Dashboard & Voice UI
- Web Dashboard & Voice UI
- Web Dashboard & Voice UI
- Web Dashboard & Voice UI
- devices
- rr_intervals_ms
- height_cm
- weight_kg
- source_device
- AGENTS.md

## God Nodes (most connected - your core abstractions)
1. `How to Read an EEG (Jadeja, Cambridge)` - 22 edges
2. `Session` - 12 edges
3. `get_llm()` - 11 edges
4. `get_tts()` - 11 edges
5. `stream()` - 11 edges
6. `run_bench()` - 10 edges
7. `resolve_system_prompt()` - 10 edges
8. `t()` - 10 edges
9. `get_stt()` - 9 edges
10. `eeg_features()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `Voice agent on EC2 (Docker + Tailscale HTTPS)` --semantically_similar_to--> `Milestone 3: Gemini 1.5 Flash voice on Pi 4`  [INFERRED] [semantically similar]
  00_Tasks/07_2026-W46_09-11_to_15-11.md → 02_Outputs/theory/01_Pipeline.md
- `Alpha relative power AF7/AF8 eyes open vs closed` --semantically_similar_to--> `Band power features`  [INFERRED] [semantically similar]
  02_Outputs/report/01_Report_Week45/figures/alpha-psd.pdf → 01_Documents/23_AETA2025_ID63.pdf
- `Week 46 tasks` --conceptually_related_to--> `Assistant fabricated readings and fix`  [INFERRED]
  00_Tasks/07_2026-W46_09-11_to_15-11.md → 02_Outputs/report/02_Report_Week46_2026-11-09_to_2026-11-15.md
- `Backlog` --conceptually_related_to--> `Proactive voice alerting`  [INFERRED]
  00_Tasks/99_Backlog.md → 02_Outputs/theory/01_Pipeline.md
- `Week 46 tasks` --conceptually_related_to--> `PR template`  [INFERRED]
  00_Tasks/07_2026-W46_09-11_to_15-11.md → .github/pull_request_template.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **STT/TTS/LLM benchmark harnesses** — 03_code_01_audio_agent_test_ui_index, 03_code_01_audio_agent_test_ui_test2, 03_code_01_audio_agent_test_ui_test3, 03_code_01_audio_agent_readme_model_benchmark [EXTRACTED 1.00]
- **EEG specific conditions chapters** — 01_documents_02_cambridge_core_how_to_read_an_eeg_31aug2025_12_1_pp_169_176_common_seizure_mimics_chapter, 01_documents_02_cambridge_core_how_to_read_an_eeg_31aug2025_12_2_pp_177_186_seizures_chapter, 01_documents_02_cambridge_core_how_to_read_an_eeg_31aug2025_12_3_pp_187_194_epilepsies_chapter, 01_documents_02_cambridge_core_how_to_read_an_eeg_31aug2025_12_4_pp_195_213_epilepsy_syndromes_chapter, 01_documents_02_cambridge_core_how_to_read_an_eeg_31aug2025_12_7_pp_230_238_status_epilepticus_chapter [EXTRACTED 1.00]
- **Phased project plan (phases 1-6)** — 00_tasks_01_2026_06_khoi_tao_du_an, 00_tasks_02_2026_07_08_voice_agent_va_web, 00_tasks_03_2026_09_doi_kien_truc, 00_tasks_04_2026_10_thu_nhan_du_lieu, 00_tasks_05_2026_10_gateway_va_aws, 00_tasks_06_2026_11_web_daily_vitals [EXTRACTED 1.00]
- **Per-device BLE sensor readers** — 04_data_magene_h303_readme_ble_protocol, 04_data_muse2_readme_ble_protocol, 04_data_yuwell_yx110_readme_ble_protocol [INFERRED 0.85]
- **EEG localization basics: polarity, montage, reference** — 01_documents_02_cambridge_core_how_to_read_an_eeg_31aug2025_10_2_pp_15_16_polarity_polarity, 01_documents_02_cambridge_core_how_to_read_an_eeg_31aug2025_10_3_pp_17_22_montages_montages, 01_documents_02_cambridge_core_how_to_read_an_eeg_31aug2025_10_4_pp_23_28_localization_phase_reversal, 01_documents_02_cambridge_core_how_to_read_an_eeg_31aug2025_10_5_pp_29_31_active_reference_active_reference [INFERRED 0.85]
- **Weekly tasks and reports cycle** — 00_tasks_07_2026_w46_09_11_to_15_11, 00_tasks_08_2026_w47_16_11_to_22_11, 02_outputs_report_01_report_week45_2026_09_01_to_2026_11_01, 02_outputs_report_02_report_week46_2026_11_09_to_2026_11_15, 00_tasks_99_backlog [INFERRED 0.85]
- **STT/TTS/LLM benchmark test pages** — 02_outputs_screenshots_test_ui_stt, 02_outputs_screenshots_test_ui_tts, 02_outputs_screenshots_test_ui_llm [INFERRED 0.95]

## Communities (111 total, 17 thin omitted)

### Community 0 - "Bluetooth Sensor Acquisition"
Cohesion: 0.06
Nodes (37): ble_loop(), handler(), broadcast(), find_device(), main(), serve_http(), __init__(), ws_handler() (+29 more)

### Community 1 - "Cloud API & Daily Vitals"
Cohesion: 0.05
Nodes (36): respond(), day_range(), handler(), latest_vitals(), query_day(), summarize(), handler(), handler() (+28 more)

### Community 2 - "EEG Session Analysis"
Cohesion: 0.06
Nodes (34): mean_bpm(), ppg_bpm(), samples(), ts(), _channel_features(), eeg_features(), hrv(), ppg_bpm() (+26 more)

### Community 3 - "Web Dashboard & Voice UI"
Cohesion: 0.07
Nodes (43): activeSources, addAgentBubble(), api(), buildSystemInstruction(), chatArea, chatPanel, clearAgentHistory(), closeChatBtn (+35 more)

### Community 4 - "User Profile Data Model"
Cohesion: 0.05
Nodes (43): max, min, max, min, alpha, beta, delta, theta (+35 more)

### Community 5 - "properties"
Cohesion: 0.18
Nodes (11): type, properties, type, type, type, alpha, average_power_bands, beta (+3 more)

### Community 6 - "User Profile Data Model"
Cohesion: 0.05
Nodes (40): properties, type, properties, type, type, properties, required, type (+32 more)

### Community 7 - "Telemetry JSON Schemas"
Cohesion: 0.05
Nodes (38): allOf, description, type, description, type, type, description, type (+30 more)

### Community 8 - "Telemetry JSON Schemas"
Cohesion: 0.05
Nodes (38): allOf, description, type, description, type, type, description, type (+30 more)

### Community 9 - "EEG Session Analysis"
Cohesion: 0.05
Nodes (36): alpha, beta, delta, theta, diastolic_bp, heart_rate_bpm, heart_rate_source, hrv_ms (+28 more)

### Community 10 - "EEG Reference Documentation"
Cohesion: 0.07
Nodes (32): ii How to Read an EEG, iii How to Read an EEG, iv Copyright page, vi Dedication, vii Contents, viii Figure Contributions, x Foreword, xi Preface (+24 more)

### Community 11 - "EEG Session Analysis"
Cohesion: 0.12
Nodes (17): type, properties, duration_seconds, raw_data_s3_key, session_id, session_type, timestamp_end, timestamp_start (+9 more)

### Community 12 - "Cloud API & Daily Vitals"
Cohesion: 0.09
Nodes (28): Phase 2: Voice agent and web, Benchmarked voice defaults (distil-whisper, qwen2.5, Piper), Phase 3: Architecture change, Phase 5: Gateway and AWS, Offline queue resend exactly once, Minimal vertical slice sensors->Pi->AWS->web, Phase 6: Web daily vitals, Week 46 tasks (+20 more)

### Community 13 - "Cloud API & Daily Vitals"
Cohesion: 0.08
Nodes (26): description, maximum, minimum, type, properties, required, type, properties (+18 more)

### Community 14 - "Cloud API & Daily Vitals"
Cohesion: 0.08
Nodes (26): description, maximum, minimum, type, properties, required, type, properties (+18 more)

### Community 15 - "server.py"
Cohesion: 0.06
Nodes (28): config(), _friendly_error(), index(), llm_models(), llm_test(), llm_test_log(), LLMTestLogRequest, LLMTestRequest (+20 more)

### Community 16 - "Bluetooth Sensor Acquisition"
Cohesion: 0.11
Nodes (21): Voice agent docker-compose (Ollama + agent), Voice Agent README, Response Time Test Harness, TTS-Only Test Harness, LLM-Only Test Harness, SAM template, DailyFunction nightly 00:05, DailyVitalsTable (+13 more)

### Community 17 - "properties"
Cohesion: 0.20
Nodes (10): maximum, minimum, type, type, properties, enum, type, age (+2 more)

### Community 18 - "llmsurveyproviderspy Component"
Cohesion: 0.15
Nodes (7): ask(), BaseLLM, GeminiLLM, OllamaLLM, resolve_system_prompt(), _system_prompt(), _time_context()

### Community 19 - "Cloud API & Daily Vitals"
Cohesion: 0.10
Nodes (20): activities, active_minutes, calories_burned_kcal, diastolic, systolic, blood_oxygen_log, daily_summary, average_blood_oxygen_pct (+12 more)

### Community 20 - "ttspy Component"
Cohesion: 0.15
Nodes (5): BaseTTS, GTTSTTS, _load_silero_model(), PiperTTS, SileroTTS

### Community 21 - "EEG Session Analysis"
Cohesion: 0.12
Nodes (17): type, type, type, properties, diastolic, end_time, heart_rate, hrv (+9 more)

### Community 22 - "Cloud API & Daily Vitals"
Cohesion: 0.10
Nodes (20): type, type, type, properties, type, average_heart_rate, bpm, duration_seconds (+12 more)

### Community 23 - "EEG Session Analysis"
Cohesion: 0.10
Nodes (20): type, type, type, properties, diastolic, end_time, heart_rate, hrv (+12 more)

### Community 24 - "Telemetry JSON Schemas"
Cohesion: 0.10
Nodes (20): type, type, properties, alert_id, alert_text, raw_statement, text, threshold (+12 more)

### Community 25 - "Cloud API & Daily Vitals"
Cohesion: 0.10
Nodes (20): type, type, type, properties, type, average_heart_rate, bpm, duration_seconds (+12 more)

### Community 26 - "Web Dashboard & Voice UI"
Cohesion: 0.14
Nodes (11): LLM-Only Test Harness (Test 3) screenshot, logs/llm_test_times.csv, Response Time Test Harness (STT mic test) screenshot, Patient context + 24 test sentences (short/medium/long), logs/response_times.csv, TTS-Only Test Harness (Test 2) screenshot, logs/tts_test_times.csv, Unready TTS providers (MeloTTS, sherpa-onnx VITS, StyleTTS2, NeMo FastPitch, Matcha-TTS, Coqui VITS) (+3 more)

### Community 27 - "startup Component"
Cohesion: 0.16
Nodes (9): main(), run_bench(), _startup(), get_llm(), BaseSTT, FasterWhisperSTT, GeminiSTT, get_stt() (+1 more)

### Community 28 - "agentpy Component"
Cohesion: 0.19
Nodes (5): decode_to_mono16k(), play_samples(), play_wav(), record_until_silence(), save_wav()

### Community 29 - "metadata"
Cohesion: 0.20
Nodes (10): properties, required, type, metadata, updated_at, user_id, format, type (+2 more)

### Community 30 - "EEG Session Analysis"
Cohesion: 0.06
Nodes (32): description, type, type, description, items, type, type, type (+24 more)

### Community 31 - "Syncope Component"
Cohesion: 0.12
Nodes (16): Part III Specific Conditions (How to Read an EEG), Common Seizure Mimics (How to Read an EEG), Psychogenic Nonepileptic Seizures, Syncope, Seizures (How to Read an EEG), Focal Seizure, Generalized Seizure, Epilepsies (How to Read an EEG) (+8 more)

### Community 32 - "ttssurveyproviderspy Component"
Cohesion: 0.21
Nodes (8): _synth_espeak(), _synth_gtts(), _synth_kokoro(), _synth_mms(), _synth_piper(), _synth_silero(), synthesize(), _wav_bytes_from_float()

### Community 33 - "EEG Session Analysis"
Cohesion: 0.15
Nodes (13): properties, type, type, description, enum, type, type, diastolic_bp (+5 more)

### Community 34 - "EEG Session Analysis"
Cohesion: 0.07
Nodes (26): description, type, type, properties, required, type, type, type (+18 more)

### Community 35 - "Ekg Artifact Component"
Cohesion: 0.15
Nodes (14): EEG Common Artifacts (How to Read an EEG), Ekg Artifact, Electrode Pop Artifact, Eye Blink Artifact, Muscle Artifact, Band power features, Emotiv EPOC 14-channel dataset, Session/subject-independent protocols (+6 more)

### Community 36 - "EEG Session Analysis"
Cohesion: 0.15
Nodes (12): description, required, type, properties, metadata, summary_insights, required, $schema (+4 more)

### Community 37 - "EEG Session Analysis"
Cohesion: 0.14
Nodes (13): description, type, required, type, properties, eeg_series, metadata, vitals_series (+5 more)

### Community 38 - "EEG Session Analysis"
Cohesion: 0.20
Nodes (10): type, required, type, maximum, minimum, type, alerts, average_vitals (+2 more)

### Community 39 - "Cloud API & Daily Vitals"
Cohesion: 0.15
Nodes (13): description, format, type, pattern, type, properties, required, type (+5 more)

### Community 40 - "EEG Session Analysis"
Cohesion: 0.15
Nodes (13): items, type, type, maximum, minimum, type, ai_summary_bullets, alerts (+5 more)

### Community 41 - "Cloud API & Daily Vitals"
Cohesion: 0.15
Nodes (13): description, format, type, pattern, type, properties, required, type (+5 more)

### Community 43 - "EEG Session Analysis"
Cohesion: 0.17
Nodes (12): type, properties, required, type, type, type, alpha, average_eeg (+4 more)

### Community 44 - "Cloud API & Daily Vitals"
Cohesion: 0.23
Nodes (12): items, type, items, type, required, type, properties, blood_oxygen_log (+4 more)

### Community 45 - "EEG Session Analysis"
Cohesion: 0.17
Nodes (12): type, properties, required, type, type, type, alpha, average_eeg (+4 more)

### Community 46 - "Telemetry JSON Schemas"
Cohesion: 0.23
Nodes (12): items, type, required, type, items, type, properties, interaction_log (+4 more)

### Community 47 - "Cloud API & Daily Vitals"
Cohesion: 0.23
Nodes (12): items, type, items, type, required, type, properties, blood_oxygen_log (+4 more)

### Community 48 - "configpy Component"
Cohesion: 0.14
Nodes (5): Config, detect_device_profile(), _env_or(), _pick(), resolve_whisper_model()

### Community 49 - "Cloud API & Daily Vitals"
Cohesion: 0.18
Nodes (11): minimum, type, description, properties, required, type, minimum, type (+3 more)

### Community 50 - "Telemetry JSON Schemas"
Cohesion: 0.18
Nodes (11): properties, required, type, metadata, session_id, timestamp, user_id, type (+3 more)

### Community 51 - "Cloud API & Daily Vitals"
Cohesion: 0.18
Nodes (11): minimum, type, description, properties, required, type, minimum, type (+3 more)

### Community 52 - "properties"
Cohesion: 0.22
Nodes (9): description, type, description, type, properties, type, alpha_dominant_rhythm_hz, baseline_sessions_completed (+1 more)

### Community 53 - "properties"
Cohesion: 0.29
Nodes (7): required, type, required, type, properties, demographics, eeg_baselines

### Community 54 - "EEG Session Analysis"
Cohesion: 0.25
Nodes (8): type, properties, required, type, cognitive_states, state_distribution, additionalProperties, type

### Community 55 - "type"
Cohesion: 0.16
Nodes (15): items, type, items, items, type, required, type, ai_summary_bullets (+7 more)

### Community 56 - "EEG Session Analysis"
Cohesion: 0.20
Nodes (10): type, properties, required, type, cognitive_states, state_blocks, state_distribution, type (+2 more)

### Community 57 - "downloadmodelspy Component"
Cohesion: 0.31
Nodes (4): _download(), fetch_voice(), main(), setup.sh script

### Community 59 - "assistantalertsjson Component"
Cohesion: 0.22
Nodes (8): interaction_log, metadata, session_id, timestamp, user_id, proactive_alerts, $schema, voice_health_logs

### Community 60 - "EEG Session Analysis"
Cohesion: 0.29
Nodes (7): properties, type, AF7, AF8, channels, TP10, TP9

### Community 61 - "EEG Session Analysis"
Cohesion: 0.29
Nodes (7): properties, type, AF7, AF8, channels, TP10, TP9

### Community 62 - "Cloud API & Daily Vitals"
Cohesion: 0.33
Nodes (5): description, required, $schema, title, type

### Community 63 - "EEG Session Analysis"
Cohesion: 0.27
Nodes (10): items, items, required, type, rr_intervals_ms, description, items, type (+2 more)

### Community 64 - "Telemetry JSON Schemas"
Cohesion: 0.33
Nodes (5): description, required, $schema, title, type

### Community 65 - "Telemetry JSON Schemas"
Cohesion: 0.33
Nodes (6): properties, type, action_details, context_tokens_used, intent_detected, tool_called

### Community 66 - "Cloud API & Daily Vitals"
Cohesion: 0.33
Nodes (5): description, required, $schema, title, type

### Community 67 - "user_profile_schema.json"
Cohesion: 0.33
Nodes (5): description, required, $schema, title, type

### Community 68 - "Hyperventilation Component"
Cohesion: 0.50
Nodes (4): Activation Procedures (How to Read an EEG), Hyperventilation, Photic Stimulation, Sleep Deprivation

### Community 69 - "Alpha PSD figure (Muse 2, eyes open vs closed)"
Cohesion: 0.50
Nodes (4): Alpha PSD figure (Muse 2, eyes open vs closed), Alpha peak ~11 Hz at TP9/TP10 when eyes closed, Heart rate comparison figure (H303 vs YX110 vs Muse 2 PPG), Muse 2 PPG HR outliers (20 s window) vs agreeing H303/YX110

### Community 70 - "Web Dashboard & Voice UI"
Cohesion: 0.50
Nodes (4): Health Hub web dashboard screenshot, AI Insights - Sleep Analysis panel, Vital cards: HR, blood pressure, SpO2, sleep score, Voice assistant mic button

### Community 71 - "properties"
Cohesion: 0.33
Nodes (6): type, description, type, properties, bmi, bmr_kcal

### Community 72 - "Telemetry JSON Schemas"
Cohesion: 0.50
Nodes (4): type, additionalProperties, type, extracted_entities

### Community 73 - "Phase 1 Project init Component"
Cohesion: 0.67
Nodes (3): Phase 1: Project init, Conda guide, Conda environment.yml for audio agent

### Community 74 - "Benign Sporadic Sleep Spi Component"
Cohesion: 0.67
Nodes (3): Benign Sporadic Sleep Spikes, EEG Normal Variants (How to Read an EEG), Wicket Spikes

### Community 75 - "Epileptiform Discharges Component"
Cohesion: 0.67
Nodes (3): Sporadic Abnormalities (How to Read an EEG), Epileptiform Discharges, Focal Slowing

### Community 76 - "Periodic Discharges Component"
Cohesion: 0.67
Nodes (3): Repetitive Abnormalities (How to Read an EEG), Periodic Discharges, Rhythmic Delta Activity

### Community 77 - "Cloud API & Daily Vitals"
Cohesion: 0.67
Nodes (3): session_id, description, type

### Community 78 - "Cloud API & Daily Vitals"
Cohesion: 0.67
Nodes (3): source_device, enum, type

### Community 79 - "Cloud API & Daily Vitals"
Cohesion: 0.67
Nodes (3): timestamp, format, type

### Community 80 - "Cloud API & Daily Vitals"
Cohesion: 0.67
Nodes (3): timestamp_end, format, type

### Community 81 - "Concurrent BLE test Pi wifi-on (0 drops)"
Cohesion: 0.67
Nodes (3): Concurrent BLE test PC (muse2 1 drop), Pi Tailscale ping log during concurrent test, Concurrent BLE test Pi wifi-on (0 drops)

### Community 82 - "Magene H303 dashboard pag Component"
Cohesion: 0.67
Nodes (3): Magene H303 dashboard page, Magene H303 BLE reader README, Magene H303 BLE protocol: Heart Rate Service 0x180D / 0x2A37 with RR intervals

### Community 83 - "Muse 2 dashboard page Component"
Cohesion: 0.67
Nodes (3): Muse 2 dashboard page, Muse 2 BLE reader README, Muse 2 BLE protocol: Vendor service 0xFE8D, EEG 256Hz + PPG 64Hz, presets p50/p21

### Community 84 - "Telemetry JSON Schemas"
Cohesion: 0.67
Nodes (3): enum, type, call_status

### Community 85 - "Telemetry JSON Schemas"
Cohesion: 0.67
Nodes (3): enum, type, category

### Community 86 - "Telemetry JSON Schemas"
Cohesion: 0.67
Nodes (3): speaker, enum, type

### Community 87 - "Cloud API & Daily Vitals"
Cohesion: 0.67
Nodes (3): session_id, description, type

### Community 88 - "Cloud API & Daily Vitals"
Cohesion: 0.67
Nodes (3): source_device, enum, type

### Community 89 - "Cloud API & Daily Vitals"
Cohesion: 0.67
Nodes (3): timestamp, format, type

### Community 90 - "Cloud API & Daily Vitals"
Cohesion: 0.67
Nodes (3): timestamp_end, format, type

### Community 105 - "devices"
Cohesion: 0.40
Nodes (5): description, items, type, enum, devices

### Community 106 - "rr_intervals_ms"
Cohesion: 0.50
Nodes (4): rr_intervals_ms, description, items, type

### Community 107 - "height_cm"
Cohesion: 0.50
Nodes (4): maximum, minimum, type, height_cm

### Community 108 - "weight_kg"
Cohesion: 0.50
Nodes (4): weight_kg, maximum, minimum, type

### Community 109 - "source_device"
Cohesion: 0.67
Nodes (3): source_device, enum, type

## Knowledge Gaps
- **89 isolated node(s):** `EEG Maturation Across Age`, `Describing a Foreground Abnormality`, `ii How to Read an EEG`, `iii How to Read an EEG`, `iv Copyright page` (+84 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 727 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `properties` connect `EEG Session Analysis` to `EEG Session Analysis`?**
  _High betweenness centrality (0.004) - this node is a cross-community bridge._
- **What connects `EEG Maturation Across Age`, `Describing a Foreground Abnormality`, `ii How to Read an EEG` to the rest of the system?**
  _89 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Bluetooth Sensor Acquisition` be split into smaller, more focused modules?**
  _Cohesion score 0.06187202538339503 - nodes in this community are weakly interconnected._
- **Why does `properties` connect `properties` to `user_profile_schema.json`, `metadata`, `User Profile Data Model`?**
  _High betweenness centrality (0.004) - this node is a cross-community bridge._
- **Should `Cloud API & Daily Vitals` be split into smaller, more focused modules?**
  _Cohesion score 0.050888286660644384 - nodes in this community are weakly interconnected._
- **Should `EEG Session Analysis` be split into smaller, more focused modules?**
  _Cohesion score 0.06448087431693988 - nodes in this community are weakly interconnected._
- **Should `Web Dashboard & Voice UI` be split into smaller, more focused modules?**
  _Cohesion score 0.07346938775510205 - nodes in this community are weakly interconnected._