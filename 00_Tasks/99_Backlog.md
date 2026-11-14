# Việc còn lại

Theo thứ tự ưu tiên trong báo cáo Week45 (mục 7).

## Ưu tiên
- [ ] Nối trợ lý giọng nói với `GET /vitals/latest`: hỏi được nhịp tim và SpO₂ gần nhất bằng giọng nói
- [ ] Kiểm tra trọn đường với thiết bị thật: đeo Muse + H303, chạy `gateway.py --minutes 2`, thấy phiên tự hiện trên web
- [ ] Ngắt Wi-Fi thật trên Pi, xác nhận phiên được gửi bù đúng một lần (bản giả lập đã đạt)
- [ ] Kẹp YX110, xem số đo mới tự lên `GET /measurements`
- [ ] Kiểm tra trọn vẹn phần tổng hợp hằng đêm với nhiều ngày dữ liệu
- [ ] Lưu dữ liệu thô lên S3; tới lúc đó, dọn `sessions/` trên Pi định kỳ (khoảng 75 MB/giờ)

## Cần quyết định
- [ ] Định nghĩa `overall_score` (hiện luôn bằng 0)
- [ ] Phạm vi phân giai đoạn giấc ngủ từ EEG
- [ ] Xác nhận cách chia 72 đặc trưng EEG

## Sửa nhỏ
- [ ] Gateway không ghi tóm tắt khi phiên không có nhịp tim (phiên thử HR = 0 lúc 15:58:29 ngày 28/10)
- [ ] Gộp số đo YX110 từng giây thành một lần đo (hiện khoảng 60 bản ghi mỗi phút)
- [ ] Kiểm tra HRV 6.1 ms (xem giai đoạn 6)
- [ ] Prompt gửi trợ lý không chứa `undefined`/`NaN` khi thiếu huyết áp hoặc giấc ngủ (`app.js` dòng 206–208)

## Nếu còn thời gian
- [ ] Đo lại pipeline giọng nói trên Raspberry Pi 4
- [ ] Đăng nhập người dùng (Cognito)
- [ ] Cảnh báo bất thường
- [ ] CI/CD tự động deploy
- [ ] Ứng dụng di động dạng PWA (`03_Code/03_mobile-app/` đang trống)
- [ ] Điền phần 01/09 – 19/09 trong báo cáo Week45
