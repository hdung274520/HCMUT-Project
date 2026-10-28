# Việc tiếp theo (bàn giao cho session mới, cập nhật 28/10/2026)

## Bối cảnh

- Hướng làm: **lát cắt dọc nhỏ nhất**, cảm biến → Pi → AWS → web. Không hoàn thiện từng milestone trước.
- Đã xong: Bước 1 (3 cảm biến trên Pi, không cần dongle), Bước 2 (`05_Data/gateway/`), Bước 3 đến **3.7.3** (AWS `POST/GET /sessions`; `upload.py` chạy tay trên Pi gửi được 2 phiên). **Chưa làm từ 3.7.4**: cron, kiểm tra từ đầu đến cuối, commit `upload.py`. Chi tiết ở `03_Outputs/report/02_Report_2026-10-27_to_2026-10-28.md`.
- Người dùng **tự setup AWS**, chỉ cần hướng dẫn từng bước. Không tự deploy.
- Người dùng đã quyết định: **H303 là nguồn nhịp tim chính và không phải vấn đề**; PPG của Muse 2 chỉ để tham khảo.

## Thông tin kỹ thuật cần biết

- Git: đang ở nhánh `feature/aws-sessions` (commit `72358cb`). `main` đã có phần cảm biến và gateway. `05_Data/gateway/upload.py` **chưa commit**. Chưa rõ đã push `main` chưa.
- Pi: `ssh hdung274520@dras`, code ở `~/sensors/`, gateway ở `~/sensors/gateway` (venv riêng).
- Chép code PC → Pi (luôn loại `queue.db`):
  `rsync -av --exclude venv --exclude raw_captures --exclude __pycache__ --exclude queue.db --exclude gateway.log --exclude sessions ~/Project/05_Data/ hdung274520@dras:~/sensors/`
- AWS: stack `sensors-backend`, `ap-southeast-1`. URL và key nằm trong `~/.sensors_env` (trên PC và Pi, không commit).
- Deploy: `cd 04_Code/02_aws-services && source venv/bin/activate && sam build && sam deploy`. **Phải kích hoạt venv**, vì Python 3.14 của hệ thống không có pip, khiến `sam build` lỗi.
- Pi chưa có `sqlite3` CLI: đọc `queue.db` bằng `python3 -c "import sqlite3 ..."`.

## Việc cần làm, theo thứ tự

1. **3.7.4 Cài cron uploader trên Pi** (chưa cài, `crontab -l` báo trống):
   `(crontab -l 2>/dev/null; echo '* * * * * . $HOME/.sensors_env && cd $HOME/sensors/gateway && python3 upload.py >> upload.log 2>&1') | crontab -`
   Kiểm tra bằng `crontab -l`. Sau khoảng 1 phút, `upload.log` phải xuất hiện.
2. **3.7.5 Kiểm tra từ đầu đến cuối:** đeo Muse và H303, chạy `gateway.py --minutes 2`, đợi cron gửi. Kiểm tra theo thứ tự:
   - `gateway.log` có dòng `Session ... saved` với HR khác 0;
   - trong `queue.db`, phiên mới có `sent=1`;
   - `upload.log` có dòng `sent session::...`;
   - phiên mới có trong `GET /sessions`.

   Lưu ý: trong `queue.db` trên Pi đã có một phiên thử `2026-10-28T15:58:29` với **HR = 0** và `sent=0`. Khi cron chạy, phiên này cũng sẽ được gửi lên. Chưa rõ vì sao HR = 0; xem `gateway.log`.
   Tùy người dùng: sửa gateway để không ghi tóm tắt khi phiên không có nhịp tim.
3. **3.7.6 Git:**
   - commit `upload.py`;
   - kiểm tra lần sửa thông báo lỗi `400` trong `src/sessions.py` (`getattr(exc, "message", ...)`) đã được deploy chưa;
   - gộp `feature/aws-sessions` vào `main`, rồi push.
4. **3.8 Web app đọc từ API** (`04_Code/04_web-app/`):
   - tạo `config.js` chứa `API_URL` và `API_KEY`, thêm nó vào `.gitignore`, và nạp nó trước `app.js` trong `index.html`;
   - trong `loadAllData()` của `app.js`, thay `fetch('data/active_session.json')` bằng `GET ${API_URL}/sessions?limit=1` với header `x-api-key`;
   - phải đặt mặc định `eeg_series: []` và `vitals_series: []`, nếu không `renderSleep()` và `renderSleepVitals()` sẽ lỗi `.map`.
   - Đạt khi web hiện phiên thật.
5. **3.9 Kiểm tra từ đầu đến cuối và mất mạng:** ngắt Wi-Fi Pi (chỉ khi ngồi trước Pi hoặc có cáp LAN), ghi một phiên, bật mạng lại, rồi xác nhận phiên được gửi bù đúng một lần.
6. **Bước 4**, khi lát cắt đã chạy:
   - `SpotMeasurements` + `POST /measurements` (dữ liệu YX110 đã có trong queue với `kind='spot'`);
   - Lambda tổng hợp `DailyVitals` hằng đêm;
   - Voice Agent gọi `GET /vitals/latest`;
   - PWA.
7. **Còn mở:**
   - định nghĩa `overall_score` (hiện luôn bằng 0);
   - xác nhận cách chia 72 đặc trưng EEG;
   - dọn `sessions/` trên Pi định kỳ (khoảng 75 MB/giờ) cho đến khi có S3.
