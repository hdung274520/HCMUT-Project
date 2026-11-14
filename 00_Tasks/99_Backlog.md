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
- [ ] HRV 6.1 ms: nguyên nhân là RR của H303 lặp lại, chưa phải HRV thật. Cần RR từng nhịp thật (hoặc HRV từ PPG) thì mới hiện lại (tuần 46 T9)
- [ ] Prompt gửi trợ lý không chứa `undefined`/`NaN` khi thiếu huyết áp hoặc giấc ngủ (`app.js` dòng 206–208)

## Từ audit 14/11
- [ ] Tổng hợp hằng đêm tính lại 2 ngày gần nhất, để phiên gửi bù sau 00:05 không bị bỏ sót (`daily.py`)
- [x] ~~GitHub Pages báo DATA ERROR~~: Pages giờ chạy bằng dữ liệu mẫu (tuần 46 T10)
- [ ] `upload.py`: phiên bị server từ chối (4xx) đánh `sent=-1`, không gửi lại mỗi phút
- [ ] Gateway ghi tạm tóm tắt phiên mỗi 5 phút, để mất điện không làm mất cả phiên
- [ ] CI kiểm tra 2 bản schema (`04_Data/schemas/` và `03_Code/02_aws-services/src/`) giống nhau
- [ ] `GET /sessions`, `GET /measurements`: `limit` sai thì trả 400 thay vì làm Lambda sập

## Nếu còn thời gian
- [ ] ~~Đo lại pipeline giọng nói trên Raspberry Pi 4~~: bỏ, vì trợ lý chạy trên AWS (chốt 14/11, xem tuần 46 T6)
- [ ] Đăng nhập người dùng (Cognito): đưa vào tuần 47, T6 (web trên GitHub Pages)
- [ ] Cảnh báo bất thường
- [ ] CI/CD tự động deploy
- [ ] Ứng dụng di động dạng PWA (`03_Code/03_mobile-app/` đang trống)
- [ ] Điền phần 01/09 – 19/09 trong báo cáo Week45
