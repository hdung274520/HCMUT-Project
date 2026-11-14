# Giai đoạn 5: Thiết bị biên và backend AWS (27/10 – 29/10/2026)

**Mục tiêu:** làm "lát cắt dọc nhỏ nhất": dữ liệu thật đi được từ cảm biến → Pi → AWS → web.

## Tasks

### Chạy trên Raspberry Pi
- [x] Kiểm tra chạy đồng thời 3 thiết bị BLE trên Pi, không cần dongle (`8ce8fe2`)
- [x] Công cụ đo phiên mắt mở / mắt nhắm (`session_timer.py`, `analyze_session.py`) (`8ce8fe2`)
- [x] `gateway.py`: đọc cả 3 thiết bị trong một tiến trình, xếp hàng đợi SQLite (`ec6d8ec`)
- [x] Ghi mỗi lần chạy thành một phiên: log thô + tóm tắt đúng schema (`ea7666f`)
- [x] `upload.py` chạy bằng cron mỗi phút, gửi phiên và số đo chưa gửi (`0e6a3e6`)
- [x] Giả lập mất mạng: phiên được gửi bù đúng một lần

### Backend AWS (stack `sensors-backend`, `ap-southeast-1`)
- [x] Bảng `Sessions` + `POST/GET /sessions`, bảo vệ bằng API key (`72358cb`)
- [x] Bảng `SpotMeasurements` + `POST/GET /measurements`, gửi số đo YX110 lên (`a7769f1`)
- [x] Lambda tổng hợp `DailyVitals` mỗi đêm lúc 00:05 (giờ VN) + `GET /vitals/daily` (`ba6a79b`)
- [x] `GET /vitals/latest`: chỉ số mới nhất, kèm nguồn và thời điểm đo (`26f6277`)

### Web
- [x] Web đọc phiên mới nhất từ `GET /sessions`, API key để trong `config.js` (không commit) (`152f788`)

### Báo cáo
- [x] Báo cáo 27/10 – 28/10 và 29/10, kèm file bàn giao việc tiếp theo (`c48e92e`, `0de9b08`)

## Kết quả

Lát cắt khép kín ngày 29/10: Pi tự gửi dữ liệu lên AWS mỗi phút, web hiện phiên thật. Trên AWS có 2 phiên và 231 số đo YX110 ngày 28/10.
