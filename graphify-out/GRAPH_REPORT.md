# Graph Report - Project  (2026-11-21)

## Corpus Check
- 149 files · ~99,226 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 19 file(s) not represented in the graph (top: .jsonl 11, (none) 5, .tex 1)

## Summary
- 1459 nodes · 1990 edges · 105 communities (89 shown, 16 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 72 edges (avg confidence: 0.83)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Bluetooth Sensor Acquisition
- Cloud API & Daily Vitals
- EEG Session Analysis
- Web Dashboard & Voice UI
- User Profile Data Model
- User Profile Data Model
- User Profile Data Model
- Telemetry JSON Schemas
- Telemetry JSON Schemas
- EEG Session Analysis
- EEG Reference Documentation
- EEG Session Analysis
- Cloud API & Daily Vitals
- Cloud API & Daily Vitals
- Cloud API & Daily Vitals
- serverpy Component
- Bluetooth Sensor Acquisition
- User Profile Data Model
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
- friendlyerror Component
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
- vadpy Component
- EEG Session Analysis
- EEG Session Analysis
- EEG Session Analysis
- EEG Session Analysis
- downloadmodelspy Component
- config Component
- assistantalertsjson Component
- EEG Session Analysis
- EEG Session Analysis
- Cloud API & Daily Vitals
- EEG Session Analysis
- Telemetry JSON Schemas
- Telemetry JSON Schemas
- Cloud API & Daily Vitals
- EEG Session Analysis
- Hyperventilation Component
- Community 69
- Web Dashboard & Voice UI
- EEG Session Analysis
- Telemetry JSON Schemas
- Phase 1 Project init Component
- Benign Sporadic Sleep Spi Component
- Epileptiform Discharges Component
- Periodic Discharges Component
- Cloud API & Daily Vitals
- Cloud API & Daily Vitals
- Cloud API & Daily Vitals
- Cloud API & Daily Vitals
- Community 81
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
- Community 92
- Community 93
- CLI guide Component
- Phase 4 Data acquisition Component
- Index How to Read an EEG Component
- Community 97
- Web Dashboard & Voice UI
- Web Dashboard & Voice UI
- Web Dashboard & Voice UI
- Web Dashboard & Voice UI
- Web Dashboard & Voice UI
- Web Dashboard & Voice UI

## God Nodes (most connected - your core abstractions)
1. `How to Read an EEG (Jadeja, Cambridge)` - 22 edges
2. `Session` - 12 edges
3. `stream()` - 11 edges
4. `resolve_system_prompt()` - 10 edges
5. `t()` - 10 edges
6. `get_llm()` - 9 edges
7. `get_stt()` - 9 edges
8. `get_tts()` - 9 edges
9. `eeg_features()` - 9 edges
10. `summarize()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `Voice agent on EC2 (Docker + Tailscale HTTPS)` --semantically_similar_to--> `Milestone 3: Gemini 1.5 Flash voice on Pi 4`  [INFERRED] [semantically similar]
  00_Tasks/07_2026-W46_09-11_to_15-11.md → 02_Outputs/theory/01_Pipeline.md
- `Alpha relative power AF7/AF8 eyes open vs closed` --semantically_similar_to--> `Band power features`  [INFERRED] [semantically similar]
  02_Outputs/report/01_Report_Week45/figures/alpha-psd.pdf → 01_Documents/23_AETA2025_ID63.pdf
- `Week 46 tasks` --conceptually_related_to--> `PR template`  [INFERRED]
  00_Tasks/07_2026-W46_09-11_to_15-11.md → .github/pull_request_template.md
- `Week 46 tasks` --conceptually_related_to--> `Assistant fabricated readings and fix`  [INFERRED]
  00_Tasks/07_2026-W46_09-11_to_15-11.md → 02_Outputs/report/02_Report_Week46_2026-11-09_to_2026-11-15.md
- `Backlog` --conceptually_related_to--> `Proactive voice alerting`  [INFERRED]
  00_Tasks/99_Backlog.md → 02_Outputs/theory/01_Pipeline.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Phased project plan (phases 1-6)** — 00_tasks_01_2026_06_khoi_tao_du_an, 00_tasks_02_2026_07_08_voice_agent_va_web, 00_tasks_03_2026_09_doi_kien_truc, 00_tasks_04_2026_10_thu_nhan_du_lieu, 00_tasks_05_2026_10_gateway_va_aws, 00_tasks_06_2026_11_web_daily_vitals [EXTRACTED 1.00]
- **Weekly tasks and reports cycle** — 00_tasks_07_2026_w46_09_11_to_15_11, 00_tasks_08_2026_w47_16_11_to_22_11, 02_outputs_report_01_report_week45_2026_09_01_to_2026_11_01, 02_outputs_report_02_report_week46_2026_11_09_to_2026_11_15, 00_tasks_99_backlog [INFERRED 0.85]
- **STT/TTS/LLM benchmark harnesses** — 03_code_01_audio_agent_test_ui_index, 03_code_01_audio_agent_test_ui_test2, 03_code_01_audio_agent_test_ui_test3, 03_code_01_audio_agent_readme_model_benchmark [EXTRACTED 1.00]
- **Per-device BLE sensor readers** — 04_data_magene_h303_readme_ble_protocol, 04_data_muse2_readme_ble_protocol, 04_data_yuwell_yx110_readme_ble_protocol [INFERRED 0.85]
- **EEG localization basics: polarity, montage, reference** — 01_documents_02_cambridge_core_how_to_read_an_eeg_31aug2025_10_2_pp_15_16_polarity_polarity, 01_documents_02_cambridge_core_how_to_read_an_eeg_31aug2025_10_3_pp_17_22_montages_montages, 01_documents_02_cambridge_core_how_to_read_an_eeg_31aug2025_10_4_pp_23_28_localization_phase_reversal, 01_documents_02_cambridge_core_how_to_read_an_eeg_31aug2025_10_5_pp_29_31_active_reference_active_reference [INFERRED 0.85]
- **EEG specific conditions chapters** — 01_documents_02_cambridge_core_how_to_read_an_eeg_31aug2025_12_1_pp_169_176_common_seizure_mimics_chapter, 01_documents_02_cambridge_core_how_to_read_an_eeg_31aug2025_12_2_pp_177_186_seizures_chapter, 01_documents_02_cambridge_core_how_to_read_an_eeg_31aug2025_12_3_pp_187_194_epilepsies_chapter, 01_documents_02_cambridge_core_how_to_read_an_eeg_31aug2025_12_4_pp_195_213_epilepsy_syndromes_chapter, 01_documents_02_cambridge_core_how_to_read_an_eeg_31aug2025_12_7_pp_230_238_status_epilepticus_chapter [EXTRACTED 1.00]
- **STT/TTS/LLM benchmark test pages** — 02_outputs_screenshots_test_ui_stt, 02_outputs_screenshots_test_ui_tts, 02_outputs_screenshots_test_ui_llm [INFERRED 0.95]

## Communities (105 total, 16 thin omitted)

### Community 0 - "Bluetooth Sensor Acquisition"
Cohesion: 0.06
Nodes (40): find(), main(), run_device(), ble_loop(), handler(), broadcast(), find_device(), main() (+32 more)

### Community 1 - "Cloud API & Daily Vitals"
Cohesion: 0.06
Nodes (32): respond(), day_range(), handler(), latest_vitals(), query_day(), summarize(), handler(), handler() (+24 more)

### Community 2 - "EEG Session Analysis"
Cohesion: 0.06
Nodes (36): mean_bpm(), ppg_bpm(), samples(), ts(), _channel_features(), eeg_features(), hrv(), ppg_bpm() (+28 more)

### Community 3 - "Web Dashboard & Voice UI"
Cohesion: 0.07
Nodes (43): activeSources, addAgentBubble(), api(), buildSystemInstruction(), chatArea, chatPanel, clearAgentHistory(), closeChatBtn (+35 more)

### Community 4 - "User Profile Data Model"
Cohesion: 0.05
Nodes (43): max, min, max, min, alpha, beta, delta, theta (+35 more)

### Community 5 - "User Profile Data Model"
Cohesion: 0.05
Nodes (42): description, type, type, properties, type, description, type, type (+34 more)

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
Cohesion: 0.06
Nodes (32): description, type, type, description, items, type, type, type (+24 more)

### Community 12 - "Cloud API & Daily Vitals"
Cohesion: 0.09
Nodes (28): Phase 2: Voice agent and web, Benchmarked voice defaults (distil-whisper, qwen2.5, Piper), Phase 3: Architecture change, Phase 5: Gateway and AWS, Offline queue resend exactly once, Minimal vertical slice sensors->Pi->AWS->web, Phase 6: Web daily vitals, Week 46 tasks (+20 more)

### Community 13 - "Cloud API & Daily Vitals"
Cohesion: 0.08
Nodes (26): description, maximum, minimum, type, properties, required, type, properties (+18 more)

### Community 14 - "Cloud API & Daily Vitals"
Cohesion: 0.08
Nodes (26): description, maximum, minimum, type, properties, required, type, properties (+18 more)

### Community 15 - "serverpy Component"
Cohesion: 0.14
Nodes (13): llm_test(), llm_test_log(), LLMTestLogRequest, LLMTestRequest, _log_llm_test(), _log_tts_test(), _log_turn(), _synth() (+5 more)

### Community 16 - "Bluetooth Sensor Acquisition"
Cohesion: 0.11
Nodes (21): Voice agent docker-compose (Ollama + agent), Voice Agent README, Response Time Test Harness, TTS-Only Test Harness, LLM-Only Test Harness, SAM template, DailyFunction nightly 00:05, DailyVitalsTable (+13 more)

### Community 17 - "User Profile Data Model"
Cohesion: 0.08
Nodes (24): maximum, minimum, type, type, description, type, properties, type (+16 more)

### Community 18 - "llmsurveyproviderspy Component"
Cohesion: 0.15
Nodes (8): ask(), BaseLLM, GeminiLLM, get_llm(), OllamaLLM, resolve_system_prompt(), _system_prompt(), _time_context()

### Community 19 - "Cloud API & Daily Vitals"
Cohesion: 0.10
Nodes (20): activities, active_minutes, calories_burned_kcal, diastolic, systolic, blood_oxygen_log, daily_summary, average_blood_oxygen_pct (+12 more)

### Community 20 - "ttspy Component"
Cohesion: 0.16
Nodes (6): BaseTTS, get_tts(), GTTSTTS, _load_silero_model(), PiperTTS, SileroTTS

### Community 21 - "EEG Session Analysis"
Cohesion: 0.10
Nodes (20): type, type, type, properties, diastolic, end_time, heart_rate, hrv (+12 more)

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
Nodes (6): _startup(), resolve_whisper_model(), BaseSTT, FasterWhisperSTT, GeminiSTT, get_stt()

### Community 28 - "agentpy Component"
Cohesion: 0.18
Nodes (5): decode_to_mono16k(), play_samples(), play_wav(), record_until_silence(), save_wav()

### Community 29 - "friendlyerror Component"
Cohesion: 0.21
Nodes (4): _friendly_error(), Session, read_from_gemini(), ws_endpoint()

### Community 30 - "EEG Session Analysis"
Cohesion: 0.12
Nodes (17): type, properties, duration_seconds, raw_data_s3_key, session_id, session_type, timestamp_end, timestamp_start (+9 more)

### Community 31 - "Syncope Component"
Cohesion: 0.12
Nodes (16): Part III Specific Conditions (How to Read an EEG), Common Seizure Mimics (How to Read an EEG), Psychogenic Nonepileptic Seizures, Syncope, Seizures (How to Read an EEG), Focal Seizure, Generalized Seizure, Epilepsies (How to Read an EEG) (+8 more)

### Community 32 - "ttssurveyproviderspy Component"
Cohesion: 0.21
Nodes (8): _synth_espeak(), _synth_gtts(), _synth_kokoro(), _synth_mms(), _synth_piper(), _synth_silero(), synthesize(), _wav_bytes_from_float()

### Community 33 - "EEG Session Analysis"
Cohesion: 0.12
Nodes (16): properties, required, type, type, type, description, enum, type (+8 more)

### Community 34 - "EEG Session Analysis"
Cohesion: 0.12
Nodes (16): properties, required, type, type, type, description, enum, type (+8 more)

### Community 35 - "Ekg Artifact Component"
Cohesion: 0.15
Nodes (14): EEG Common Artifacts (How to Read an EEG), Ekg Artifact, Electrode Pop Artifact, Eye Blink Artifact, Muscle Artifact, Band power features, Emotiv EPOC 14-channel dataset, Session/subject-independent protocols (+6 more)

### Community 36 - "EEG Session Analysis"
Cohesion: 0.14
Nodes (13): description, type, required, type, properties, eeg_series, metadata, vitals_series (+5 more)

### Community 37 - "EEG Session Analysis"
Cohesion: 0.14
Nodes (13): description, type, required, type, properties, eeg_series, metadata, vitals_series (+5 more)

### Community 38 - "EEG Session Analysis"
Cohesion: 0.15
Nodes (13): items, type, type, maximum, minimum, type, ai_summary_bullets, alerts (+5 more)

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
Cohesion: 0.18
Nodes (4): Config, detect_device_profile(), _env_or(), _pick()

### Community 49 - "Cloud API & Daily Vitals"
Cohesion: 0.18
Nodes (11): minimum, type, description, properties, required, type, minimum, type (+3 more)

### Community 50 - "Telemetry JSON Schemas"
Cohesion: 0.18
Nodes (11): properties, required, type, metadata, session_id, timestamp, user_id, type (+3 more)

### Community 51 - "Cloud API & Daily Vitals"
Cohesion: 0.18
Nodes (11): minimum, type, description, properties, required, type, minimum, type (+3 more)

### Community 53 - "EEG Session Analysis"
Cohesion: 0.20
Nodes (10): description, type, type, type, activity_state, age, gender, user_context (+2 more)

### Community 54 - "EEG Session Analysis"
Cohesion: 0.20
Nodes (10): type, properties, required, type, cognitive_states, state_blocks, state_distribution, type (+2 more)

### Community 55 - "EEG Session Analysis"
Cohesion: 0.27
Nodes (10): items, items, required, type, rr_intervals_ms, description, items, type (+2 more)

### Community 56 - "EEG Session Analysis"
Cohesion: 0.20
Nodes (10): type, properties, required, type, cognitive_states, state_blocks, state_distribution, type (+2 more)

### Community 57 - "downloadmodelspy Component"
Cohesion: 0.28
Nodes (4): _download(), fetch_voice(), main(), setup.sh script

### Community 58 - "config Component"
Cohesion: 0.31
Nodes (7): config(), index(), llm_models(), test2_ui(), test3_ui(), test_ui(), tts_providers()

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
Cohesion: 0.53
Nodes (6): items, items, required, type, items, items

### Community 64 - "Telemetry JSON Schemas"
Cohesion: 0.33
Nodes (5): description, required, $schema, title, type

### Community 65 - "Telemetry JSON Schemas"
Cohesion: 0.33
Nodes (6): properties, type, action_details, context_tokens_used, intent_detected, tool_called

### Community 66 - "Cloud API & Daily Vitals"
Cohesion: 0.33
Nodes (5): description, required, $schema, title, type

### Community 67 - "EEG Session Analysis"
Cohesion: 0.40
Nodes (5): description, items, type, enum, devices

### Community 68 - "Hyperventilation Component"
Cohesion: 0.50
Nodes (4): Activation Procedures (How to Read an EEG), Hyperventilation, Photic Stimulation, Sleep Deprivation

### Community 69 - "Community 69"
Cohesion: 0.50
Nodes (4): Alpha PSD figure (Muse 2, eyes open vs closed), Alpha peak ~11 Hz at TP9/TP10 when eyes closed, Heart rate comparison figure (H303 vs YX110 vs Muse 2 PPG), Muse 2 PPG HR outliers (20 s window) vs agreeing H303/YX110

### Community 70 - "Web Dashboard & Voice UI"
Cohesion: 0.50
Nodes (4): Health Hub web dashboard screenshot, AI Insights - Sleep Analysis panel, Vital cards: HR, blood pressure, SpO2, sleep score, Voice assistant mic button

### Community 71 - "EEG Session Analysis"
Cohesion: 0.50
Nodes (4): rr_intervals_ms, description, items, type

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

### Community 81 - "Community 81"
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

## Knowledge Gaps
- **89 isolated node(s):** `CI workflow`, `Phase 1: Project init`, `Benchmarked voice defaults (distil-whisper, qwen2.5, Piper)`, `Phase 3: Architecture change`, `Phase 4: Data acquisition` (+84 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 717 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **16 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `properties` connect `EEG Session Analysis` to `EEG Session Analysis`, `EEG Session Analysis`, `EEG Session Analysis`?**
  _High betweenness centrality (0.004) - this node is a cross-community bridge._
- **What connects `CI workflow`, `Phase 1: Project init`, `Benchmarked voice defaults (distil-whisper, qwen2.5, Piper)` to the rest of the system?**
  _89 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Bluetooth Sensor Acquisition` be split into smaller, more focused modules?**
  _Cohesion score 0.05924978687127025 - nodes in this community are weakly interconnected._
- **Should `Cloud API & Daily Vitals` be split into smaller, more focused modules?**
  _Cohesion score 0.06321334503950835 - nodes in this community are weakly interconnected._
- **Should `EEG Session Analysis` be split into smaller, more focused modules?**
  _Cohesion score 0.05706760316066725 - nodes in this community are weakly interconnected._
- **Should `Web Dashboard & Voice UI` be split into smaller, more focused modules?**
  _Cohesion score 0.07346938775510205 - nodes in this community are weakly interconnected._
- **Should `User Profile Data Model` be split into smaller, more focused modules?**
  _Cohesion score 0.045454545454545456 - nodes in this community are weakly interconnected._