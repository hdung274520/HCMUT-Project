# Giai đoạn 3: Đổi kiến trúc và thiết bị đeo (01/09 – 28/09/2026)

**Mục tiêu:** dựng backend AWS đầu tiên, rồi chốt kiến trúc mới, trong đó Raspberry Pi là cổng dữ liệu duy nhất.

## Tasks

- [ ] *01/09 – 19/09: chưa ghi lại (git không có commit trong khoảng này, báo cáo Week45 cũng còn TODO)*
- [x] Dựng thử backend serverless bằng AWS SAM, kèm CI/CD trên GitHub (`371664f`)
- [x] Sửa CI: đường dẫn schema, tên stack SAM (`6b584ec`, `d826d41`)
- [x] Gỡ backend SAM và workflow deploy để làm lại theo kiến trúc mới (`fab019c`)
- [x] Chuyển máy phát triển từ Fedora sang Ubuntu 26.04 LTS (`5e78634`)
- [x] Thay đồng hồ Galaxy Fit 3 bằng Magene H303 (nhịp tim) và Yuwell YX110 (SpO₂) (`2a7a8d8`)
- [x] Bỏ Mobile App + Google Health Connect: mọi thiết bị đeo kết nối BLE thẳng vào Pi
- [x] Cập nhật schema theo kiến trúc mới (thêm `spot_measurement_schema.json`)

## Kết quả

Kiến trúc chốt: **Muse 2 + H303 + YX110 → Raspberry Pi 4 → AWS → web và trợ lý giọng nói.**
