# Việc tiếp theo (bàn giao cho session mới, cập nhật 29/10/2026)

Thay cho `NEXT_TASKS.md` (28/10).

## Bối cảnh

- Hướng làm: **lát cắt dọc nhỏ nhất**, cảm biến → Pi → AWS → web. Lát cắt đã khép kín ngày 29/10: Pi tự gửi lên AWS mỗi phút, web đọc phiên thật. Chi tiết ở `03_Outputs/report/03_Report_2026-10-29.md`.
- Đã xong: Bước 1–3 (trừ hai kiểm tra cần thiết bị, xem mục 3) và phần `SpotMeasurements` của Bước 4.
- Người dùng **tự setup và tự deploy AWS**, chỉ cần hướng dẫn từng bước. Người dùng muốn **tự chạy lệnh trên Pi** và cần hướng dẫn rất cụ thể: lệnh, kết quả đúng trông thế nào, làm gì nếu sai.
- Người dùng đã quyết định: **H303 là nguồn nhịp tim chính**; PPG của Muse 2 chỉ để tham khảo.
- **Hiện không có thiết bị đeo** (Muse 2, H303, YX110). Vẫn SSH được vào Pi.

## Thông tin kỹ thuật cần biết

- Git: mọi thứ đã ở `main` và đã push (commit `a7769f1`). Các nhánh `feature/web-api` và `feature/measurements` đã gộp, có thể xóa.
- Pi: `ssh hdung274520@dras`, **chỉ nhận mật khẩu**, nên Claude không tự SSH được (BatchMode bị từ chối). Code ở `~/sensors/`, gateway ở `~/sensors/gateway`. Pi không có `git` và `sqlite3` CLI: đọc `queue.db` bằng `python3 -c "import sqlite3 ..."`.
- Chép code PC → Pi:
  `rsync -av --exclude venv --exclude raw_captures --exclude __pycache__ --exclude .pytest_cache --exclude queue.db --exclude gateway.log --exclude upload.log --exclude sessions ~/Project/05_Data/ hdung274520@dras:~/sensors/`
- Cron trên Pi (đã cài):
  `* * * * * . $HOME/.sensors_env && cd $HOME/sensors/gateway && python3 upload.py >> upload.log 2>&1`
  `upload.py` chỉ dùng thư viện chuẩn. Gửi `session` lên `POST /sessions` và `spot` lên `POST /measurements` (lô 100, tối đa 1000 mỗi lần chạy). Trạng thái trong cột `sent` của `queue`: `0` chưa gửi, `1` đã gửi, `-1` server từ chối.
- AWS: stack `sensors-backend`, `ap-southeast-1`, stage `dev`. URL và key nằm trong `~/.sensors_env` (trên PC và Pi, không commit; biến `SENSORS_API`, `SENSORS_API_KEY`).
  - `POST/GET /sessions`: bảng `Sessions`, khóa `user_id` + `timestamp_start`.
  - `POST/GET /measurements`: bảng `SpotMeasurements`, khóa `user_id` + `timestamp`. POST nhận một danh sách, trả `{"saved": [...], "rejected": [...]}`.
  - Code ở `04_Code/02_aws-services/src/`: `sessions.py`, `measurements.py`, `api.py` (`respond()` dùng chung). Schema được chép từ `05_Data/schemas/` vào `src/`; khi sửa schema phải chép lại.
- Deploy: `cd 04_Code/02_aws-services && source venv/bin/activate && sam build && sam deploy`. **Phải kích hoạt venv**, vì Python 3.14 của hệ thống không có pip. Changeset hợp lệ có thể `Delete` một `SensorApiDeployment...` cũ (bình thường); nếu thấy `Delete` bảng thì dừng.
- Test:
  - gateway: `cd 05_Data/gateway && python3 -m pytest -q` (pytest của hệ thống);
  - Lambda: `cd 04_Code/02_aws-services && venv/bin/python -m pytest -q test_measurements.py` (hệ thống không có `boto3`; đã cài `pytest` vào venv).
- Web: `cd 04_Code/04_web-app && python3 -m http.server 8000`. Cần `config.js` (không commit), tạo từ `~/.sensors_env`:
  `printf "const API_URL = '%s';\nconst API_KEY = '%s';\n" "$SENSORS_API" "$SENSORS_API_KEY" > config.js`

## Dữ liệu hiện có trên AWS

- `Sessions`: 2 phiên thật ngày 28/10 (`15:21:29`, `15:23:12`). Phiên thử `15:58:29` (HR = 0) **không** được gửi; trong `queue.db` trên Pi nó được đánh dấu `sent=1`.
- `SpotMeasurements`: 231 số đo YX110, 15:21–15:26 ngày 28/10. Bản ghi thử `test-1` đã xóa.

## Việc cần làm, theo thứ tự

1. **Lambda tổng hợp `DailyVitals` hằng đêm** (không cần thiết bị):
   - EventBridge Scheduler gọi Lambda mỗi đêm, gom `Sessions` và `SpotMeasurements` của ngày hôm trước vào bảng `DailyVitals` (khóa `user_id` + `date`), theo `05_Data/schemas/daily_vitals_schema.json`.
   - Trường nào không có dữ liệu thì bỏ trống, không điền giá trị giả (xem `03_Outputs/01_Pipeline.md`, mục "Tổng hợp hằng ngày").
   - Cần quyết định múi giờ của "một ngày" (dữ liệu lưu UTC, người dùng ở UTC+7).
   - Có thể thêm `GET /vitals/daily` để web thay `data/daily_vitals.json`.
2. **`GET /vitals/latest`** cho Voice Agent: giá trị mới nhất của nhịp tim và SpO₂, **kèm nguồn và thời điểm đo**.
3. **Khi có thiết bị:**
   - **3.7.5** kiểm tra trọn đường: đeo Muse và H303, chạy `gateway.py --minutes 2`, rồi kiểm tra lần lượt: `gateway.log` có `Session ... saved` với HR khác 0 → trong `queue.db` phiên mới có `sent=1` → `upload.log` có `sent session::...` → phiên hiện trên web.
   - **3.9** ngắt Wi-Fi thật (chỉ khi ngồi trước Pi hoặc có cáp LAN): ghi một phiên khi mất mạng, bật lại mạng, xác nhận phiên được gửi bù đúng một lần. Bản giả lập đã đạt ngày 29/10.
   - Kẹp YX110 để xem số đo mới tự lên `GET /measurements`.
4. **Tùy người dùng:**
   - Sửa gateway để không ghi tóm tắt khi phiên không có nhịp tim. Nguyên nhân HR = 0 của phiên `15:58:29` chưa rõ; xem `gateway.log` trên Pi quanh 22:58 giờ VN.
   - Gộp số đo YX110 từng giây thành một lần đo (hiện khoảng 60 bản ghi mỗi phút kẹp tay).
5. **Còn mở:**
   - định nghĩa `overall_score` (hiện luôn bằng 0);
   - xác nhận cách chia 72 đặc trưng EEG;
   - dọn `sessions/` trên Pi định kỳ (khoảng 75 MB/giờ) cho đến khi có S3;
   - Voice Agent, PWA, Cognito, S3, cảnh báo.
