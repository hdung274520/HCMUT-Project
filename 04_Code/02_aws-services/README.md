# AWS Cloud Backend - Medical Signal Audio Assistant

Thư mục này chứa mã nguồn hạ tầng đám mây (Infrastructure as Code - IaC) và các hàm xử lý serverless (AWS Lambda) phục vụ việc tiếp nhận, phân tích bất thường và lưu trữ các chỉ số sinh học (nhịp tim, HRV, SpO2, huyết áp, sóng não EEG) theo chuẩn Serverless của AWS.

---

## 1. Kiến Trúc Hạ Tầng (Architecture)

```text
[Raspberry Pi 4 / Mobile App]
            │
            ▼  (POST /vitals, /sessions)
   [AWS API Gateway (HTTP API)]
            │
    ┌───────┴────────────────────────┐
    ▼                                ▼
[Lambda: Ingest Vitals]     [Lambda: Query Vitals / Sessions]
    │                                │
    ├──────────────────┬─────────────┤
    ▼                  ▼             ▼
[DynamoDB: Vitals] [DynamoDB: Sessions] [S3: Raw Biosignals]
```

- **AWS API Gateway (HTTP API)**: Cổng giao tiếp REST API có độ trễ cực thấp, tích hợp CORS để Web Dashboard và Mobile App gọi trực tiếp.
- **AWS Lambda (Python 3.11)**:
  - `ingest_vitals.py`: Tiếp nhận dữ liệu, phát hiện bất thường nhịp tim (Tachycardia/Bradycardia), nồng độ oxy (Hypoxia) và lưu trữ.
  - `query_vitals.py`: Trả về dữ liệu mới nhất và thống kê lịch sử theo giờ cho Web Dashboard.
  - `session_handler.py`: Quản lý các phiên đo EEG, phân tích phổ sóng não (Alpha, Beta, Theta, Delta) và các giai đoạn ngủ.
- **Amazon DynamoDB**: Cơ sở dữ liệu NoSQL tốc độ mili-giây, cơ chế **Pay-Per-Request (On-Demand)** tối ưu chi phí (nằm trọn trong AWS Free Tier).
- **Amazon S3**: Lưu trữ các file tín hiệu thô, báo cáo định kỳ.

---

## 2. Chuẩn Bị & Cài Đặt (Prerequisites)

### Bước 1: Cài đặt AWS CLI & AWS SAM CLI trên Fedora Linux

```bash
# 1. Cài đặt AWS CLI
sudo dnf install -y awscli

# 2. Cài đặt AWS SAM CLI
# Tải bản cài đặt chính thức từ AWS
curl -Lo aws-sam-cli-linux-x86_64.zip https://github.com/aws/aws-sam-cli/releases/latest/download/aws-sam-cli-linux-x86_64.zip
unzip aws-sam-cli-linux-x86_64.zip -d sam-installation
sudo ./sam-installation/install
rm -rf aws-sam-cli-linux-x86_64.zip sam-installation

# Kiểm tra cài đặt
aws --version
sam --version
```

### Bước 2: Cấu hình thông tin xác thực AWS

Chạy lệnh sau và nhập `Access Key ID` và `Secret Access Key` (được tạo từ AWS IAM Console):

```bash
aws configure
# AWS Access Key ID [None]: <NHẬP_ACCESS_KEY_CỦA_BẠN>
# AWS Secret Access Key [None]: <NHẬP_SECRET_KEY_CỦA_BẠN>
# Default region name [None]: ap-southeast-1 (Singapore) hoặc us-east-1
# Default output format [None]: json
```

---

## 3. Thử Nghiệm Cục Bộ (Local Testing)

Bạn có thể chạy thử API ngay trên máy dev Fedora trước khi deploy lên cloud:

```bash
cd 04_Code/02_aws-services

# Build template SAM
sam build

# Khởi chạy API Gateway giả lập trên cổng 3000 (cần cài đặt Docker)
sam local start-api --port 3000
```

---

## 4. Triển Khai Lên AWS Cloud (Deployment)

Chỉ cần chạy lệnh sau:

```bash
cd 04_Code/02_aws-services

# Build mã nguồn và thư viện
sam build

# Triển khai có hướng dẫn (chỉ cần chạy --guided ở lần đầu tiên)
sam deploy --guided
```

Trong quá trình `--guided`, hệ thống sẽ hỏi một số câu hỏi:
- **Stack Name**: `hcmut-medical-backend` (hoặc tên tùy chọn)
- **AWS Region**: `ap-southeast-1`
- **Parameter Environment**: `prod`
- **Confirm changes before deploy**: `y`
- **Allow SAM CLI IAM role creation**: `y`
- **Disable rollback for faster debugging**: `n`
- **IngestVitalsFunction has no authentication. Is this okay?**: `y`
- **Save arguments to configuration file**: `y` (sẽ lưu vào `samconfig.toml`)

Sau khi hoàn tất, SAM sẽ in ra mục **Outputs**, trong đó có đường dẫn:
```text
HttpApiUrl: https://abcdef1234.execute-api.ap-southeast-1.amazonaws.com
```

---

## 5. Kiểm Thử API Sau Khi Triển Khai (API Testing)

### 1. Đẩy chỉ số sinh học lên AWS (POST /vitals)
```bash
API_URL="https://abcdef1234.execute-api.ap-southeast-1.amazonaws.com"

curl -X POST "$API_URL/vitals" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "usr_998877",
    "timestamp": "2026-09-20T09:30:00Z",
    "source": "raspberry_pi4_muse2",
    "vitals": {
      "heart_rate": 78,
      "hrv": 45.2,
      "spo2": 98.5,
      "blood_pressure": {
        "systolic": 118,
        "diastolic": 76
      }
    }
  }'
```

Phản hồi mẫu:
```json
{
  "status": "success",
  "message": "Vital signs recorded successfully",
  "user_id": "usr_998877",
  "timestamp": "2026-09-20T09:30:00Z",
  "anomalies_detected": 0,
  "anomalies": []
}
```

### 2. Đọc chỉ số mới nhất (GET /vitals/latest)
```bash
curl "$API_URL/vitals/latest?user_id=usr_998877"
```

### 3. Đọc dữ liệu lịch sử (GET /vitals/history)
```bash
curl "$API_URL/vitals/history?user_id=usr_998877&hours=24"
```

### 4. Ghi nhận phiên ngủ / thiền (POST /sessions)
```bash
curl -X POST "$API_URL/sessions" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "usr_998877",
    "session_id": "sess_sleep_001",
    "session_type": "sleep",
    "timestamp_start": "2026-09-20T23:00:00Z",
    "timestamp_end": "2026-09-21T07:00:00Z",
    "metrics": {
      "sleep_score": 85,
      "deep_sleep_ratio": 0.22,
      "rem_sleep_ratio": 0.25
    },
    "eeg_summary": {
      "average_power_bands": {
        "alpha": 0.30,
        "beta": 0.12,
        "theta": 0.35,
        "delta": 0.23
      }
    }
  }'
```

---

## 6. Kết Nối Web Dashboard Với AWS API

Để kết nối giao diện Web Dashboard (`04_Code/04_web-app`) với backend AWS:
1. Mở tệp `04_Code/04_web-app/app.js`.
2. Cập nhật biến API endpoint:
   ```javascript
   const AWS_API_ENDPOINT = "https://abcdef1234.execute-api.ap-southeast-1.amazonaws.com";
   ```
3. Web App sẽ tự động tải dữ liệu thực từ DynamoDB thay vì dùng dữ liệu giả lập.

---

## 7. Chi Phí Trên AWS (Free Tier)

Dự án được thiết kế chuẩn **Serverless Free Tier**:
- **AWS Lambda**: Miễn phí 1,000,000 requests/tháng và 3.2 triệu giây tính toán.
- **Amazon DynamoDB**: 25 GB dung lượng lưu trữ miễn phí trọn đời (On-Demand billing).
- **Amazon S3**: 5 GB dung lượng lưu trữ miễn phí trong 12 tháng đầu.
- **API Gateway**: 1,000,000 lượt gọi HTTP API miễn phí/tháng trong 12 tháng đầu.
=> **Tổng chi phí duy trì hàng tháng: ~0.00 USD** đối với lưu lượng nghiên cứu và thử nghiệm cá nhân.
