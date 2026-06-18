# Hướng dẫn Thiết lập và Đồng bộ Dự án giữa Fedora Linux và Windows 11

Dự án này sử dụng mô hình 2 nhánh song song để phù hợp với từng môi trường phát triển:
* **Nhánh `fedora` [CHÍNH]**: Nhánh phát triển chính trên máy Fedora Linux.
* **Nhánh `window` [PHỤ]**: Nhánh trạm phụ trên máy Windows 11 dùng để chạy thử hoặc bổ trợ.

---

## BƯỚC 1: Thiết lập trên máy Fedora Linux (Môi trường chính)

Trên máy Fedora, bạn sử dụng thư mục `/home/hdung274520/Project`:
1. Luôn làm việc trên nhánh `fedora`:
   ```bash
   git checkout fedora
   ```
2. Tạo môi trường ảo Python và cài đặt thư viện (nếu cần):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r 04_Code/audio-agent/requirements.txt
   ```
3. Tạo tập tin `.env.local` chứa các biến môi trường đặc thù của Linux.

---

## BƯỚC 2: Thiết lập trên máy Windows 11 (Môi trường phụ)

Trên máy Windows 11 (thư mục `D:\Project`), thư mục này đã được kết nối với nhánh `window`:

1. **Cấu hình Git cho dự án** (đã thực hiện tự động):
   ```bash
   git config core.autocrlf true
   git config core.fileMode false
   ```

2. **Làm việc trên nhánh `window`** (đã thực hiện tự động):
   ```bash
   git checkout window
   ```
   *(Nhờ cấu hình `autocrlf true`, Git trên Windows sẽ tự động hiển thị định dạng dòng CRLF cục bộ để tránh các lỗi hiển thị trên Windows).*

3. **Cài đặt thư viện trên Windows**:
   * **Python** (Tạo môi trường ảo và kích hoạt):
     ```bash
     python -m venv venv
     .\venv\Scripts\activate
     pip install -r 04_Code/audio-agent/requirements.txt
     ```
   * **Node.js** (Next.js/React Native - nếu có dependencies trong tương lai):
     Vào thư mục `web-app` hoặc `mobile-app` và chạy:
     ```bash
     npm install
     ```
     *(Thư mục `node_modules` cài trên Windows sẽ chỉ nằm trên Windows, không bị đồng bộ sang Linux nhờ cấu hình trong `.gitignore`).*

4. **Tạo tập tin `.env.local` trên Windows**:
   * Thiết lập các đường dẫn cục bộ kiểu Windows (ví dụ: `D:\\Project\\...`) tại đây.

---

## BƯỚC 3: Quy trình làm việc và đồng bộ hàng ngày

### 1. Khi phát triển chính trên Fedora (Nhánh `fedora`)
- Viết code và commit bình thường trên nhánh `fedora`.
- Sau khi hoàn thành, đẩy code lên GitHub:
  ```bash
  git add .
  git commit -m "Nội dung thay đổi trên Fedora"
  git push origin fedora
  ```

### 2. Khi chạy thử hoặc làm việc phụ trên Windows (Nhánh `window`)
- Trước khi bắt đầu, lấy code mới nhất từ nhánh chính (`fedora`) gộp vào nhánh phụ (`window`):
  ```bash
  git checkout window
  git pull origin window
  git fetch origin
  git merge origin/fedora
  ```
  *(Lúc này, toàn bộ thay đổi mới từ Fedora sẽ được đồng bộ sang Windows).*
- Nếu có chỉnh sửa thêm trên Windows và muốn lưu lại:
  ```bash
  git add .
  git commit -m "Chỉnh sửa bổ sung từ Windows"
  git push origin window
  ```
- Khi quay lại máy Fedora, hãy gộp các thay đổi từ Windows vào nhánh chính:
  ```bash
  git checkout fedora
  git pull origin fedora
  git fetch origin
  git merge origin/window
  git push origin fedora
  ```
