#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime, timezone

try:
    import jsonschema
    from jsonschema import validate
except ImportError:
    print("Thư viện 'jsonschema' chưa được cài đặt. Đang chạy cài đặt...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "jsonschema"])
    import jsonschema
    from jsonschema import validate

# Đường dẫn thư mục
SCHEMAS_DIR = "/home/hdung274520/Project/05_Data/schemas"

def load_schema(name):
    path = os.path.join(SCHEMAS_DIR, name)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_tests():
    print("=== BẮT ĐẦU KIỂM THỬ XÁC THỰC JSON SCHEMA ===\n")
    
    # 1. Kiểm thử User Profile Schema
    print("1. Kiểm tra User Profile Schema...")
    user_schema = load_schema("user_profile_schema.json")
    mock_user_data = {
        "metadata": {
            "user_id": "usr_998877",
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        "demographics": {
            "age": 28,
            "gender": "male",
            "height_cm": 178.5,
            "weight_kg": 72.0,
            "calculated_metrics": {
                "bmi": 22.6,
                "bmr_kcal": 1680.5
            }
        },
        "physiological_baselines": {
            "max_heart_rate": 192,
            "resting_heart_rate": {
                "min": 58,
                "max": 82,
                "avg": 64
            },
            "target_heart_rate_zones": {
                "warm_up": { "min": 96, "max": 115 },
                "fat_burn": { "min": 115, "max": 134 },
                "aerobic": { "min": 134, "max": 153 },
                "anaerobic": { "min": 153, "max": 172 }
            },
            "blood_pressure_baseline": {
                "systolic": 118,
                "diastolic": 76
            }
        },
        "eeg_baselines": {
          "alpha_dominant_rhythm_hz": 9.5,
          "individual_alpha_frequency_iaf": 9.8,
          "baseline_sessions_completed": 3,
          "average_power_bands": {
              "alpha": 0.35,
              "beta": 0.15,
              "theta": 0.30,
              "delta": 0.20
          }
        }
    }
    
    try:
        validate(instance=mock_user_data, schema=user_schema)
        print(" -> SUCCESS: Dữ liệu hồ sơ người dùng hợp lệ.")
    except jsonschema.exceptions.ValidationError as err:
        print(f" -> ERROR: Lỗi xác thực hồ sơ: {err.message}")
        return False

    # 2. Kiểm thử Active Session Schema (Chế độ SLEEP và MEDITATION)
    print("\n2. Kiểm tra Active Session Schema...")
    session_schema = load_schema("active_session_schema.json")
    
    # Giả lập phiên đo Sleep
    mock_sleep_session = {
        "metadata": {
            "session_id": "sess_sleep_001",
            "session_type": "sleep",
            "timestamp_start": "2026-06-25T23:00:00Z",
            "timestamp_end": "2026-06-26T07:00:00Z",
            "duration_seconds": 28800,
            "user_context": {
                "age": 28,
                "gender": "male",
                "activity_state": "resting"
            }
        },
        "summary_insights": {
            "overall_score": 85,
            "average_vitals": {
                "heart_rate_bpm": 62.5,
                "hrv_ms": 78.0,
                "systolic_bp": 110,
                "diastolic_bp": 70
            },
            "average_eeg": {
                "alpha": 0.12,
                "beta": 0.08,
                "theta": 0.35,
                "delta": 0.45
            },
            "ai_summary_bullets": [
                "Thời gian ngủ sâu đạt 2.5 giờ, phục hồi thể chất tốt.",
                "Không ghi nhận hiện tượng ngưng thở khi ngủ hoặc nhịp tim bất thường."
            ],
            "alerts": []
        },
        "cognitive_states": {
            "state_distribution": {
                "Awake": 5.0,
                "Light": 50.0,
                "Deep": 30.0,
                "REM": 15.0
            },
            "state_blocks": [
                {
                    "state": "Awake",
                    "start_time": "2026-06-25T23:00:00Z",
                    "end_time": "2026-06-25T23:15:00Z",
                    "duration_seconds": 900
                },
                {
                    "state": "Light",
                    "start_time": "2026-06-25T23:15:00Z",
                    "end_time": "2026-06-25T23:55:00Z",
                    "duration_seconds": 2400
                },
                {
                    "state": "Deep",
                    "start_time": "2026-06-25T23:55:00Z",
                    "end_time": "2026-06-26T01:15:00Z",
                    "duration_seconds": 4800
                }
            ]
        },
        "eeg_series": [
            {
                "timestamp": "2026-06-25T23:05:00Z",
                "alpha": 0.28,
                "beta": 0.35,
                "theta": 0.22,
                "delta": 0.15
            }
        ]
    }
    
    try:
        validate(instance=mock_sleep_session, schema=session_schema)
        print(" -> SUCCESS: Dữ liệu phiên đo Sleep hợp lệ.")
    except jsonschema.exceptions.ValidationError as err:
        print(f" -> ERROR: Lỗi xác thực Sleep: {err.message}")
        return False

    # Giả lập phiên đo Stress (có phát sinh alert)
    mock_stress_session = {
        "metadata": {
            "session_id": "sess_stress_002",
            "session_type": "stress",
            "timestamp_start": "2026-06-26T10:00:00Z",
            "timestamp_end": "2026-06-26T10:15:00Z",
            "duration_seconds": 900,
            "user_context": {
                "age": 28,
                "gender": "male",
                "activity_state": "working"
            }
        },
        "summary_insights": {
            "overall_score": 42,
            "average_vitals": {
                "heart_rate_bpm": 95.8,
                "hrv_ms": 28.5,
                "systolic_bp": 138,
                "diastolic_bp": 88
            },
            "average_eeg": {
                "alpha": 0.15,
                "beta": 0.48,
                "theta": 0.22,
                "delta": 0.15
            },
            "ai_summary_bullets": [
                "Mức độ stress cao liên tục, kèm theo nhịp tim tăng vọt lên 105 BPM trong quá trình làm việc.",
                "Biến thiên nhịp tim (HRV) giảm sâu thể hiện sự căng thẳng thần kinh tự chủ."
            ],
            "alerts": [
                {
                    "type": "HIGH_STRESS_ALERT",
                    "severity": "warning",
                    "message": "Phát hiện mức độ stress cao liên tục trong hơn 10 phút."
                }
            ]
        },
        "cognitive_states": {
            "state_distribution": {
                "Calm": 10.0,
                "Moderate Stress": 40.0,
                "High Stress": 50.0
            },
            "state_blocks": [
                {
                    "state": "Calm",
                    "start_time": "2026-06-26T10:00:00Z",
                    "end_time": "2026-06-26T10:01:30Z",
                    "duration_seconds": 90
                },
                {
                    "state": "High Stress",
                    "start_time": "2026-06-26T10:01:30Z",
                    "end_time": "2026-06-26T10:09:00Z",
                    "duration_seconds": 450
                }
            ]
        }
    }
    
    try:
        validate(instance=mock_stress_session, schema=session_schema)
        print(" -> SUCCESS: Dữ liệu phiên đo Stress hợp lệ.")
    except jsonschema.exceptions.ValidationError as err:
        print(f" -> ERROR: Lỗi xác thực Stress: {err.message}")
        return False

    # 3. Kiểm thử Daily Vitals Schema
    print("\n3. Kiểm tra Daily Vitals Schema...")
    daily_schema = load_schema("daily_vitals_schema.json")
    mock_daily_data = {
        "metadata": {
            "user_id": "usr_998877",
            "date": "2026-06-26",
            "synced_at": datetime.now(timezone.utc).isoformat()
        },
        "daily_summary": {
            "resting_heart_rate_bpm": 61,
            "average_blood_oxygen_pct": 98.2,
            "average_blood_pressure": {
                "systolic": 115,
                "diastolic": 74
            },
            "sleep_summary": {
                "total_sleep_seconds": 27600,
                "sleep_score": 82
            }
        },
        "activities": {
            "steps": 10450,
            "active_minutes": 45,
            "calories_burned_kcal": 450
        },
        "heart_rate_log": [
            { "timestamp": "2026-06-26T08:00:00Z", "bpm": 72 },
            { "timestamp": "2026-06-26T12:30:00Z", "bpm": 85 }
        ],
        "workout_sessions": [
            {
                "workout_id": "wk_run_01",
                "type": "running",
                "timestamp_start": "2026-06-26T18:00:00Z",
                "timestamp_end": "2026-06-26T18:30:00Z",
                "duration_seconds": 1800,
                "calories_burned_kcal": 320,
                "average_heart_rate": 145,
                "max_heart_rate": 168
            }
        ]
    }
    
    try:
        validate(instance=mock_daily_data, schema=daily_schema)
        print(" -> SUCCESS: Dữ liệu sinh hiệu nền hàng ngày hợp lệ.")
    except jsonschema.exceptions.ValidationError as err:
        print(f" -> ERROR: Lỗi xác thực Daily vitals: {err.message}")
        return False

    # 4. Kiểm thử Assistant & Alerts Schema
    print("\n4. Kiểm tra Assistant & Alerts Schema...")
    assistant_schema = load_schema("assistant_alerts_schema.json")
    mock_assistant_data = {
        "metadata": {
            "session_id": "chat_sess_102",
            "user_id": "usr_998877",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        "interaction_log": [
            {
                "timestamp": "2026-06-26T12:00:05Z",
                "speaker": "user",
                "text": "Nhịp tim hiện tại của tôi là bao nhiêu?",
                "vosk_confidence": 0.95
            },
            {
                "timestamp": "2026-06-26T12:00:08Z",
                "speaker": "assistant",
                "text": "Nhịp tim hiện tại đo được từ Muse 2 của bạn là 64 nhịp/phút, ở mức hoàn toàn bình thường.",
                "action_details": {
                    "intent_detected": "query_vitals",
                    "tool_called": "get_current_heart_rate",
                    "context_tokens_used": 150
                }
            }
        ],
        "voice_health_logs": [
            {
                "timestamp": "2026-06-26T12:01:30Z",
                "category": "medication",
                "raw_statement": "Tôi vừa uống một viên Panadol",
                "extracted_entities": {
                    "medication_name": "Panadol",
                    "dosage": "1 pill"
                }
            }
        ],
        "proactive_alerts": [
            {
                "alert_id": "pr_alt_999",
                "timestamp": "2026-06-26T12:10:00Z",
                "vital_type": "heart_rate",
                "value": 115.0,
                "threshold": 100.0,
                "alert_text": "Cảnh báo: Nhịp tim lúc nghỉ ngơi của bạn đang tăng cao bất thường ở mức 115 nhịp/phút. Bạn có cần hỗ trợ gì không?",
                "call_status": "connected"
            }
        ]
    }
    
    try:
        validate(instance=mock_assistant_data, schema=assistant_schema)
        print(" -> SUCCESS: Dữ liệu trợ lý thoại và cảnh báo chủ động hợp lệ.")
    except jsonschema.exceptions.ValidationError as err:
        print(f" -> ERROR: Lỗi xác thực Assistant: {err.message}")
        return False
        
    print("\n=== TOÀN BỘ KIỂM THỬ XÁC THỰC THÀNH CÔNG (100% OK) ===")
    return True

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
