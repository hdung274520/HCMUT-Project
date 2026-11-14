# Giai đoạn 6: Web đọc chỉ số theo ngày (30/10 – 14/11/2026)

**Mục tiêu:** web dashboard hiện chỉ số theo ngày từ AWS thay cho dữ liệu mẫu.

## Tasks

- [x] Web đọc `GET /vitals/daily` thay cho `data/daily_vitals.json` (`ca9e823`)
- [x] Script vẽ biểu đồ phiên đo `plot_session.py` (`ca9e823`)
- [x] Báo cáo Week45 (01/09 – 01/11), bản Markdown và LaTeX, thay các báo cáo cũ (`ca9e823`)
- [x] Đổi tên thư mục: `02_Outputs`, `03_Code`, `04_Data`, cập nhật mọi đường dẫn (`8eed566`, `e34aeef`)
- [x] Sửa lỗi cú pháp `app.js` (dấu backtick thừa) (`287f3ed`)
- [x] Sửa lỗi không chuyển được tab, hiện `--` khi chưa có huyết áp (`a78582f`)
- [x] Kiểm tra web trên trình duyệt: ONLINE, 4 tab chuyển được, không lỗi Console
- [x] Dọn branch đã merge, đồng bộ máy với GitHub
- [ ] Mở Pull Request `feature/web-daily-vitals` → `main`, CI đạt, merge, xóa branch
- [ ] Sửa crontab trên Pi nếu còn trỏ đường dẫn cũ `05_Data/...`

## Ghi chú

- HRV trung bình hiện 6.1 ms, thấp bất thường (thường từ 20 ms trở lên): cần kiểm tra cách tính trong `04_Data/gateway/features.py`.
- Tab Sleep & EEG còn trống vì chưa có dữ liệu giấc ngủ và chuỗi EEG.
