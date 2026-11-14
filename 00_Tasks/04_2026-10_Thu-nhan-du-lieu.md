# Giai đoạn 4: Thu nhận dữ liệu từ thiết bị đeo (đến 26/10/2026)

**Mục tiêu:** đọc được dữ liệu BLE từ cả ba thiết bị, mỗi thiết bị có dashboard xem trực tiếp.

## Tasks

- [x] Chương trình đọc BLE + dashboard + dữ liệu thô cho Magene H303 và Yuwell YX110 (`d2e7db4`)
- [x] Chương trình đọc BLE cho Muse 2, stream mọi kênh EEG và PPG, kèm dashboard (`64d93c3`)
- [x] Bỏ kênh AUX không dùng của Muse 2 (`0a44e35`)
- [x] Test giải mã gói Muse 2 (`04_Data/muse2/test_decode.py`)
- [x] Không đưa dữ liệu thô Muse 2 lên git, vì khoảng 10 MB/phút (`5c31828`)
- [x] Dọn file metadata thừa (`66434b4`)
- [x] Viết báo cáo tiến độ 01/09 – 26/10 (`e37a182`)

## Kết quả

Đọc được dữ liệu cả ba thiết bị trên PC; dữ liệu thô nằm trong `04_Data/*/raw_captures/`.
