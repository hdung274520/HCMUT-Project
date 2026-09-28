# Cẩm Nang Quản Lý Phiên Bản Dự Án Với Git & GitHub

Tài liệu này hướng dẫn chi tiết quy trình quản lý mã nguồn, phân nhánh (branching), quy chuẩn commit, phát hành phiên bản (release tag) và thiết lập tự động hóa CI/CD cho dự án **Medical Signal Audio Assistant (HCMUT-Project)**.

---

## 1. Mô Hình Phân Nhánh (Branching Strategy)

Dự án áp dụng mô hình phân nhánh chuẩn **Git Flow / GitHub Flow**:

```text
  main (Production / Stable) ────●─────────────● (v1.0.0 Tag)
                                 │             ▲
  develop (Staging / Dev)  ──────●──────●──────┘ (Merge khi test xong)
                                 │      ▲
  feature/aws-services   ────────┴──────┘ (Nhánh tính năng riêng)
```

1. **`main`**:
   - Nhánh chính, chứa mã nguồn ổn định nhất.
   - Khi merge code vào nhánh `main`, GitHub Actions sẽ tự động kích hoạt pipeline kiểm thử (`ci.yml`).
   - Tuyệt đối **không** commit trực tiếp vào `main` khi làm việc nhóm.

2. **`develop`**:
   - Nhánh tích hợp dành cho quá trình phát triển và kiểm thử nội bộ.

3. **`feature/<ten-tinh-nang>`**:
   - Nhánh phát triển một tính năng cụ thể.
   - Ví dụ: `feature/aws-dynamodb-sync`, `feature/muse-ble-reconnect`.
   - Sau khi hoàn thành, tạo Pull Request (PR) để merge vào `develop` hoặc `main`.

4. **`bugfix/<ten-loi>`**:
   - Nhánh sửa lỗi phát sinh. Ví dụ: `bugfix/fix-spo2-calculation`.

---

## 2. Quy Chuẩn Đặt Tên Commit (Conventional Commits)

Để lịch sử Git rõ ràng và dễ theo dõi phiên bản, áp dụng cấu trúc:

```text
<loai>(<pham-vi>): <mo-ta-ngan-gon>
```

### Các tiền tố thông dụng:
- **`feat`**: Thêm tính năng mới.
  - Ví dụ: `feat(aws): add lambda handler for vital anomaly detection`
- **`fix`**: Sửa lỗi.
  - Ví dụ: `fix(audio-agent): handle websocket disconnection gracefully`
- **`docs`**: Cập nhật tài liệu (README, hướng dẫn).
  - Ví dụ: `docs: update AWS deployment and GitHub workflow guides`
- **`refactor`**: Tái cấu trúc mã nguồn (không thay đổi tính năng).
  - Ví dụ: `refactor(web-app): optimize chart rendering for heart rate`
- **`chore`**: Công việc bảo trì, cập nhật dependencies, cấu hình CI/CD.
  - Ví dụ: `chore: add github actions workflow for automated AWS deploy`
- **`test`**: Thêm hoặc cập nhật unit test.
  - Ví dụ: `test: add schema validation tests for active session`

---

## 3. Các Lệnh Git Cơ Bản & Thao Tác Hàng Ngày

### 3.1. Bắt đầu một tính năng mới
```bash
# 1. Cập nhật nhánh main mới nhất
git checkout main
git pull origin main

# 2. Tạo và chuyển sang nhánh tính năng mới
git checkout -b feature/tich-hop-cam-bien-moi
```

### 3.2. Lưu lại các thay đổi (Commit)
```bash
# Xem trạng thái các tệp đã sửa
git status

# Đưa các tệp vào khu vực chuẩn bị commit
git add .

# Tạo commit với thông điệp chuẩn
git commit -m "feat(sensor): add BLE connection timeout handler for Muse 2"
```

### 3.3. Đẩy code lên GitHub & Tạo Pull Request
```bash
# Đẩy nhánh lên GitHub
git push -u origin feature/tich-hop-cam-bien-moi

# Sau đó truy cập https://github.com/hdung274520/HCMUT-Project/pulls để tạo PR
# Hoặc sử dụng GitHub CLI (gh):
gh pr create --title "feat: add BLE connection timeout handler" --body "Chi tiết các thay đổi..."
```

### 3.4. Cập nhật code mới từ GitHub về máy
```bash
# Kéo code mới về và rebase để lịch sử commit thẳng đẹp
git pull --rebase origin main
```

---

## 4. Quản Lý Phiên Bản & Đánh Dấu Release (Semantic Versioning & Git Tags)

Định dạng phiên bản chuẩn: `vMAJOR.MINOR.PATCH` (ví dụ: `v1.0.0`):
- **MAJOR**: Thay đổi lớn, có thể làm thay đổi kiến trúc hoặc API.
- **MINOR**: Thêm tính năng mới tương thích ngược.
- **PATCH**: Các bản vá sửa lỗi nhỏ.

### Các bước gắn Tag phiên bản:
```bash
# 1. Chuyển về nhánh main đã merge đầy đủ
git checkout main
git pull origin main

# 2. Tạo tag có chú thích (annotated tag)
git tag -a v1.0.0 -m "Release v1.0.0: Hệ thống hoàn chỉnh tích hợp AWS Cloud và Voice Agent"

# 3. Đẩy tag lên GitHub
git push origin v1.0.0

# 4. Kiểm tra danh sách tag
git tag -n
```

Sau khi đẩy tag, bạn có thể vào mục **Releases** trên GitHub để bấm **Draft a new release**, chọn tag `v1.0.0` và ghi chép Release Notes.

---

## 5. Xử Lý Xung Đột (Merge Conflicts)

Nếu xảy ra xung đột khi pull code:
1. Mở các tệp có thông báo xung đột (`<<<<<<< HEAD`, `=======`, `>>>>>>>`).
2. Chọn giữ lại đoạn code đúng.
3. Đánh dấu đã giải quyết và hoàn tất rebase/merge:
   ```bash
   git add <ten_tep_da_sua>
   git rebase --continue
   # Hoặc nếu là git merge:
   git commit -m "chore: resolve merge conflict"
   git push origin <ten-nhanh>
   ```
