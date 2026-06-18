# Quy trình Làm việc và Đồng bộ Hàng ngày (Fedora <-> Windows)

Dự án này sử dụng mô hình 2 nhánh song song để phù hợp với từng môi trường phát triển:
* **Nhánh `fedora` [CHÍNH]**: Nhánh phát triển chính trên máy Fedora Linux.
* **Nhánh `window` [PHỤ]**: Nhánh trạm phụ trên máy Windows 11 dùng để chạy thử hoặc bổ trợ.

---

## 1. Khi bạn đang phát triển chính trên Fedora (Nhánh `fedora`)

- Viết code và commit bình thường trên nhánh `fedora`.
- Sau khi hoàn thành, đẩy code mới lên GitHub để lưu trữ:
  ```bash
  git add .
  git commit -m "Nội dung thay đổi trên Fedora"
  git push origin fedora
  ```

---

## 2. Khi bạn muốn chạy thử hoặc làm việc phụ trên Windows (Nhánh `window`)

- Trước khi bắt đầu, hãy lấy code mới nhất từ nhánh chính (`fedora`) gộp vào nhánh phụ (`window`):
  ```bash
  git checkout window
  git pull origin window
  git fetch origin
  git merge origin/fedora
  ```
  *(Lúc này, toàn bộ thay đổi mới từ Fedora sẽ được đồng bộ sang Windows).*

- Nếu bạn có chỉnh sửa gì thêm trên Windows và muốn lưu lại:
  ```bash
  git add .
  git commit -m "Chỉnh sửa bổ sung từ Windows"
  git push origin window
  ```

---

## 3. Khi bạn quay lại máy Fedora Linux (Nhánh `fedora`)

- Nếu trước đó bạn có chỉnh sửa trên Windows và muốn gộp các chỉnh sửa đó vào nhánh chính:
  ```bash
  git checkout fedora
  git pull origin fedora
  git fetch origin
  git merge origin/window
  git push origin fedora
  ```
