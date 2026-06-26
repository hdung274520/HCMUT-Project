#!/usr/bin/env python3
import csv
import json
import os
import sys
from datetime import datetime

def classify_sleep_stage(alpha, beta, theta, delta):
    """
    Heuristic rule to classify sleep stage from EEG power band ratios:
    - 0: Awake
    - 1: Light
    - 2: Deep
    - 3: REM
    """
    if beta >= 0.28:
        return 0, "Awake"
    elif delta >= 0.45:
        return 2, "Deep"
    elif theta >= 0.35 and delta < 0.30:
        return 3, "REM"
    else:
        return 1, "Light"

def parse_csv_to_json(csv_path, json_path, user_profile_path=None):
    if not os.path.exists(csv_path):
        print(f"Lỗi: Không tìm thấy file CSV tại {csv_path}")
        sys.exit(1)

    # 1. Đọc User Profile mặc định hoặc từ file
    user_profile = {
        "age": 25,
        "gender": "male",
        "height_cm": 175,
        "weight_kg": 70
    }
    if user_profile_path and os.path.exists(user_profile_path):
        try:
            with open(user_profile_path, "r", encoding="utf-8") as f:
                profile_data = json.load(f)
                if "user_metadata" in profile_data:
                    meta = profile_data["user_metadata"]
                    user_profile["age"] = meta.get("age", 25)
                    user_profile["gender"] = meta.get("gender", "male")
                    user_profile["height_cm"] = meta.get("height_cm", 175)
                    user_profile["weight_kg"] = meta.get("weight_kg", 70)
        except Exception as e:
            print(f"Không thể đọc file user profile: {e}. Sử dụng cấu hình mặc định.")

    # 2. Đọc và phân tích file CSV
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "timestamp": row["timestamp"],
                "alpha": float(row["alpha"]),
                "beta": float(row["beta"]),
                "theta": float(row["theta"]),
                "delta": float(row["delta"]),
                "heart_rate": int(row["heart_rate"]),
                "systolic": int(row["systolic"]),
                "diastolic": int(row["diastolic"])
            })

    if not rows:
        print("Lỗi: File CSV rỗng.")
        sys.exit(1)

    # 3. Tính toán thời gian
    timestamp_start = rows[0]["timestamp"]
    timestamp_end = rows[-1]["timestamp"]
    
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    try:
        t_start = datetime.strptime(timestamp_start, fmt)
        t_end = datetime.strptime(timestamp_end, fmt)
    except ValueError:
        # Hỗ trợ định dạng không có Z nếu cần
        fmt = "%Y-%m-%dT%H:%M:%S"
        t_start = datetime.strptime(timestamp_start.replace("Z", ""), fmt)
        t_end = datetime.strptime(timestamp_end.replace("Z", ""), fmt)

    duration_seconds = int((t_end - t_start).total_seconds())
    sleep_duration_hours = round(duration_seconds / 3600.0, 1)

    # 4. Tạo hypnogram và tính phân bố giai đoạn giấc ngủ
    hypnogram = []
    stages_count = {0: 0, 1: 0, 2: 0, 3: 0}
    
    for r in rows:
        stage, label = classify_sleep_stage(r["alpha"], r["beta"], r["theta"], r["delta"])
        hypnogram.append({
            "timestamp": r["timestamp"],
            "stage": stage,
            "stage_label": label
        })
        stages_count[stage] += 1

    total_stages = len(rows)
    distribution_percentages = {
        "awake": round((stages_count[0] / total_stages) * 100, 1),
        "light": round((stages_count[1] / total_stages) * 100, 1),
        "deep": round((stages_count[2] / total_stages) * 100, 1),
        "rem": round((stages_count[3] / total_stages) * 100, 1)
    }

    # 5. Phân tích EEG trung bình
    avg_alpha = round(sum(r["alpha"] for r in rows) / total_stages, 3)
    avg_beta = round(sum(r["beta"] for r in rows) / total_stages, 3)
    avg_theta = round(sum(r["theta"] for r in rows) / total_stages, 3)
    avg_delta = round(sum(r["delta"] for r in rows) / total_stages, 3)
    
    eeg_time_series = []
    for r in rows:
        eeg_time_series.append({
            "timestamp": r["timestamp"],
            "alpha": r["alpha"],
            "beta": r["beta"],
            "theta": r["theta"],
            "delta": r["delta"]
        })

    # 6. Phân tích Sinh hiệu (Vitals)
    hr_values = [r["heart_rate"] for r in rows]
    avg_hr = round(sum(hr_values) / len(hr_values), 1)
    min_hr = min(hr_values)
    max_hr = max(hr_values)

    hr_time_series = []
    for r in rows:
        hr_time_series.append({
            "timestamp": r["timestamp"],
            "bpm": r["heart_rate"]
        })

    systolic_vals = [r["systolic"] for r in rows]
    diastolic_vals = [r["diastolic"] for r in rows]
    avg_systolic = int(sum(systolic_vals) / len(systolic_vals))
    avg_diastolic = int(sum(diastolic_vals) / len(diastolic_vals))

    bp_recordings = []
    # Chỉ ghi nhận các điểm đo huyết áp định kỳ (khoảng cách 1.5 - 2 giờ)
    # Ở đây chúng ta sẽ lấy 4 điểm phân phối đều từ chuỗi raw
    step = max(1, len(rows) // 4)
    for i in range(0, len(rows), step):
        r = rows[i]
        bp_recordings.append({
            "timestamp": r["timestamp"],
            "systolic": r["systolic"],
            "diastolic": r["diastolic"]
        })
    # Đảm bảo điểm cuối cùng được thêm vào
    if len(bp_recordings) < 4 or bp_recordings[-1]["timestamp"] != rows[-1]["timestamp"]:
        bp_recordings.append({
            "timestamp": rows[-1]["timestamp"],
            "systolic": rows[-1]["systolic"],
            "diastolic": rows[-1]["diastolic"]
        })

    # 7. Phân tích chỉ số huyết áp
    # Quy tắc phân loại huyết áp cơ bản:
    if avg_systolic >= 140 or avg_diastolic >= 90:
        bp_status = "Tăng huyết áp Độ 2 (Stage 2 Hypertension)"
    elif avg_systolic >= 130 or avg_diastolic >= 80:
        bp_status = "Tăng huyết áp Độ 1 (Stage 1 Hypertension)"
    elif avg_systolic >= 120 and avg_diastolic < 80:
        bp_status = "Tiền tăng huyết áp (Elevated)"
    else:
        bp_status = "Huyết áp Bình thường (Optimal)"

    # 8. Tính điểm chất lượng giấc ngủ (Sleep Score)
    # Khởi đầu với 100 điểm, trừ điểm dựa trên các bất thường:
    sleep_score = 100
    
    # Thiếu hụt thời lượng ngủ (Khuyến nghị 7-9 tiếng)
    if sleep_duration_hours < 7.0:
        deficit = 7.0 - sleep_duration_hours
        sleep_score -= int(deficit * 15)  # Trừ 15 điểm cho mỗi tiếng thiếu
    elif sleep_duration_hours > 9.5:
        sleep_score -= 10 # Ngủ quá nhiều cũng giảm điểm chất lượng nhẹ

    # Thiếu ngủ sâu (Khuyến nghị > 15%)
    deep_pct = distribution_percentages["deep"]
    if deep_pct < 15.0:
        sleep_score -= int((15.0 - deep_pct) * 2)

    # Thức dậy nhiều lần (tỷ lệ Awake > 15%)
    awake_pct = distribution_percentages["awake"]
    if awake_pct > 15.0:
        sleep_score -= int((awake_pct - 15.0) * 1.5)

    # Nhịp tim cao bất thường lúc ngủ
    if avg_hr > 75:
        sleep_score -= 10

    # Giới hạn điểm từ 0 đến 100
    sleep_score = max(0, min(100, int(sleep_score)))

    # 9. Đưa ra Cảnh báo (Alerts) và Tóm tắt cho LLM
    alerts = []
    ai_bullet_points = []

    # Thêm cảnh báo dựa trên sinh hiệu
    if max_hr > 95:
        alerts.append({
            "severity": "critical",
            "metric": "heart_rate_spikes",
            "message": f"Phát hiện nhịp tim tăng vọt đột biến lên {max_hr} BPM trong khi ngủ."
        })
    elif max_hr > 85:
        alerts.append({
            "severity": "warning",
            "metric": "heart_rate_elevated",
            "message": f"Nhịp tim có vài thời điểm tăng lên {max_hr} BPM, cao hơn mức bình thường khi ngủ."
        })

    if avg_systolic >= 130 or avg_diastolic >= 85:
        alerts.append({
            "severity": "warning",
            "metric": "blood_pressure",
            "message": f"Huyết áp trung bình ghi nhận ở mức cao: {avg_systolic}/{avg_diastolic} mmHg ({bp_status})."
        })
    elif avg_systolic < 90 or avg_diastolic < 60:
        alerts.append({
            "severity": "warning",
            "metric": "blood_pressure_low",
            "message": f"Huyết áp trung bình thấp: {avg_systolic}/{avg_diastolic} mmHg."
        })

    if deep_pct < 10.0:
        alerts.append({
            "severity": "critical",
            "metric": "deep_sleep_deficit",
            "message": f"Thiếu hụt giấc ngủ sâu nghiêm trọng (chỉ đạt {deep_pct}%). Cơ thể không được phục hồi thể chất tốt."
        })
    elif deep_pct < 15.0:
        alerts.append({
            "severity": "warning",
            "metric": "deep_sleep_low",
            "message": f"Thời lượng giấc ngủ sâu hơi thấp ({deep_pct}%). Nên tăng cường thư giãn trước khi ngủ."
        })
    else:
        alerts.append({
            "severity": "info",
            "metric": "deep_sleep_optimal",
            "message": f"Thời lượng giấc ngủ sâu đạt tỉ lệ tối ưu ({deep_pct}%), giúp phục hồi thể lực tối đa."
        })

    # Tạo AI Bullet Points thông minh
    ai_bullet_points.append(
        f"Tổng thời lượng giấc ngủ đạt {sleep_duration_hours} tiếng với điểm số chất lượng giấc ngủ là {sleep_score}/100."
    )
    
    if deep_pct >= 15.0:
        ai_bullet_points.append(
            f"Tỷ lệ giấc ngủ sâu đạt {deep_pct}%, giúp phục hồi cơ bắp và phục hồi hệ miễn dịch rất tốt."
        )
    else:
        ai_bullet_points.append(
            f"Tỷ lệ giấc ngủ sâu chỉ đạt {deep_pct}%, có thể khiến bạn cảm thấy hơi mệt mỏi vào sáng hôm sau."
        )

    ai_bullet_points.append(
        f"Nhịp tim trung bình trong đêm ổn định ở mức {avg_hr} BPM (phạm vi từ {min_hr} đến {max_hr} BPM)."
    )

    if bp_status.startswith("Huyết áp Bình thường"):
        ai_bullet_points.append(
            f"Chỉ số huyết áp ổn định ở mức tối ưu, trung bình đạt {avg_systolic}/{avg_diastolic} mmHg."
        )
    else:
        ai_bullet_points.append(
            f"Hệ thống ghi nhận trạng thái {bp_status} với huyết áp trung bình là {avg_systolic}/{avg_diastolic} mmHg. Hãy theo dõi thêm."
        )

    # 10. Lắp ráp dữ liệu cuối cùng theo Schema
    output_data = {
        "metadata": {
            "session_id": f"session_{datetime.now().strftime('%Y%m%d')}_simulated",
            "timestamp_start": timestamp_start,
            "timestamp_end": timestamp_end,
            "duration_seconds": duration_seconds,
            "user_profile": user_profile
        },
        "summary_insights": {
            "sleep_score": sleep_score,
            "sleep_duration_hours": sleep_duration_hours,
            "average_heart_rate": avg_hr,
            "blood_pressure_status": bp_status,
            "ai_bullet_points": ai_bullet_points,
            "alerts": alerts
        },
        "sleep_stages": {
            "distribution_percentages": distribution_percentages,
            "hypnogram": hypnogram
        },
        "eeg_metrics": {
            "average_power_bands": {
                "alpha": avg_alpha,
                "beta": avg_beta,
                "theta": avg_theta,
                "delta": avg_delta
            },
            "time_series": eeg_time_series
        },
        "vitals": {
            "heart_rate": {
                "average_bpm": avg_hr,
                "min_bpm": min_hr,
                "max_bpm": max_hr,
                "time_series": hr_time_series
            },
            "blood_pressure": {
                "systolic_avg": avg_systolic,
                "diastolic_avg": avg_diastolic,
                "recordings": bp_recordings
            }
        }
    }

    # Đảm bảo thư mục đầu ra tồn tại
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"Thành công! Đã tạo file JSON hợp lệ tại: {json_path}")
    print(f"Tổng quan:")
    print(f"  - Điểm giấc ngủ: {sleep_score}/100")
    print(f"  - Thời lượng: {sleep_duration_hours} giờ")
    print(f"  - Nhịp tim trung bình: {avg_hr} BPM")
    print(f"  - Trạng thái Huyết áp: {bp_status}")

if __name__ == "__main__":
    csv_file = "/home/hdung274520/Project/05_Data/raw/simulated_sensor_data.csv"
    json_file = "/home/hdung274520/Project/05_Data/processed/medical_session_output.json"
    user_profile_file = "/home/hdung274520/Project/05_Data/metadata/sample_user_profile.json"
    
    # Hỗ trợ truyền tham số từ dòng lệnh
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    if len(sys.argv) > 2:
        json_file = sys.argv[2]
    if len(sys.argv) > 3:
        user_profile_file = sys.argv[3]

    parse_csv_to_json(csv_file, json_file, user_profile_file)
