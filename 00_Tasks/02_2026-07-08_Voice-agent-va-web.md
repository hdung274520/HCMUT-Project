# Giai đoạn 2: Trợ lý giọng nói và web dashboard (09/07 – 21/08/2026)

**Mục tiêu:** có web dashboard chạy trên dữ liệu mẫu và pipeline trợ lý giọng nói (STT → LLM → TTS) chạy offline trên CPU.

## Tasks

### Web dashboard và schema
- [x] Xây dựng web dashboard trên dữ liệu mẫu (`6925638`)
- [x] Viết bộ JSON Schema chuẩn hóa dữ liệu: user profile, active session, daily vitals, alerts (`6925638`)
- [x] Viết `validate_schemas.py` để kiểm tra schema
- [x] Thêm trang chuyển hướng ở thư mục gốc để có link GitHub Pages cố định (`3881d99`)

### Trợ lý giọng nói
- [x] Chuyển pipeline sang tiếng Anh, thêm Silero TTS và bộ đo thời gian phản hồi (`811a80d`)
- [x] Viết công cụ khảo sát riêng cho TTS (test2) và LLM (test3) (`2094876`)
- [x] Benchmark rồi chốt cấu hình mặc định: faster-distil-whisper-medium.en, qwen2.5:0.5b, Piper (`c9ea0e5`)
  - Thời gian phản hồi giảm từ khoảng 20 s xuống dưới 5 s mỗi lượt
- [x] Đổi kiến trúc: bỏ LiveKit, dùng WebSocket trực tiếp (`b86c532`)

### Tài liệu
- [x] Thêm ảnh chụp cho báo cáo: web dashboard, công cụ thử STT/TTS/LLM (`b5e7546`)

## Kế hoạch cuối kỳ hè (chuyển sang giai đoạn sau)

- Triển khai AWS Services → giai đoạn 3 và 5
- Kết nối Mobile App và Google Health Connect → **bỏ** ở giai đoạn 3
- Đo lại pipeline giọng nói trên Raspberry Pi 4 → **chưa làm** (xem [99_Backlog.md](99_Backlog.md))
