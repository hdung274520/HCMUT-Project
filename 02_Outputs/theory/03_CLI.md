# Hướng dẫn các lệnh CLI cơ bản

Tài liệu này tổng hợp các lệnh cơ bản và thông dụng nhất cho 4 nhóm công cụ dòng lệnh (CLI): **Linux/Bash CLI cơ bản**, **Claude CLI (Claude Code)**, **Antigravity CLI (`agy`)**, và **GitHub CLI (`gh`)**.

---

## 1. Các lệnh CLI cơ bản (Linux/Bash)

Dưới đây là các lệnh dòng lệnh cơ bản để làm việc với hệ điều hành Linux (Fedora, Ubuntu...) hoặc môi trường macOS/Git Bash.

### Quản lý thư mục & tập tin
*   `pwd` (Print Working Directory): Hiển thị đường dẫn thư mục hiện tại.
*   `ls` (List): Liệt kê danh sách file và thư mục con.
    *   `ls -la`: Liệt kê tất cả (bao gồm cả file ẩn bắt đầu bằng dấu `.`) dưới dạng danh sách chi tiết.
*   `cd <path>` (Change Directory): Di chuyển đến thư mục khác.
    *   `cd ..`: Di chuyển lên thư mục cha.
    *   `cd ~` hoặc chỉ `cd`: Di chuyển về thư mục Home của người dùng.
*   `mkdir <dir_name>` (Make Directory): Tạo thư mục mới.
*   `touch <file_name>`: Tạo file trống mới hoặc cập nhật thời gian sửa đổi của file.
*   `cp <source> <destination>` (Copy): Sao chép file/thư mục.
    *   `cp -r <src_dir> <dest_dir>`: Sao chép thư mục và toàn bộ nội dung bên trong.
*   `mv <source> <destination>` (Move): Di chuyển hoặc đổi tên file/thư mục.
*   `rm <file>` (Remove): Xóa file.
    *   `rm -rf <dir>`: Xóa thư mục và toàn bộ nội dung con (Lưu ý: lệnh này có tính xóa vĩnh viễn, cần cẩn trọng khi dùng `-rf`).

### Xem & Tìm kiếm nội dung
*   `cat <file>`: Hiển thị toàn bộ nội dung file ra màn hình.
*   `less <file>`: Xem nội dung file theo từng trang (nhấn `q` để thoát, phím mũi tên để cuộn).
*   `head -n <N> <file>`: Xem `N` dòng đầu tiên của file.
*   `tail -n <N> <file>`: Xem `N` dòng cuối cùng của file.
*   `grep "<pattern>" <file>`: Tìm kiếm từ khóa hoặc mẫu (regex) trong file.
    *   `grep -ri "<pattern>" <dir>`: Tìm kiếm không phân biệt chữ hoa/thường, đệ quy trong thư mục.
*   `find <path> -name "<filename>"`: Tìm kiếm file hoặc thư mục theo tên.

### Quản lý tiến trình & Quyền hạn
*   `ps aux` hoặc `ps -ef`: Liệt kê các tiến trình đang chạy trên hệ thống.
*   `kill <PID>`: Dừng một tiến trình qua ID (PID).
    *   `kill -9 <PID>`: Bắt buộc dừng tiến trình ngay lập tức.
*   `top` hoặc `htop`: Trình quản lý tiến trình tương tác theo thời gian thực.
*   `chmod <options> <file>`: Thay đổi quyền truy cập của file (đọc/ghi/thực thi).
    *   `chmod +x <file>`: Cấp quyền thực thi cho file chạy.
*   `sudo <command>`: Chạy lệnh với quyền quản trị viên (SuperUser).

---

## 2. Claude CLI (Claude Code)

**Claude Code** là một công cụ lập trình tự động hóa (agentic CLI) của Anthropic giúp bạn tương tác với Claude trực tiếp trong terminal của mình.

### Lệnh chạy bên ngoài terminal
*   `claude`: Khởi chạy một phiên trò chuyện tương tác với Claude trong thư mục hiện tại.
*   `claude "câu hỏi"`: Bắt đầu phiên làm việc trực quan kèm theo một câu hỏi/yêu cầu ban đầu.
*   `claude -p "câu hỏi"` (Prompt mode): Gửi câu hỏi đến Claude, nhận câu trả lời và tự động thoát (hữu ích cho việc viết script).
*   `claude -c` (Continue): Tiếp tục cuộc trò chuyện gần nhất trong thư mục hiện hành.
*   `claude -r "<session_id>"` (Resume): Tiếp tục một phiên làm việc cụ thể bằng ID phiên.
*   `claude auth login`: Xác thực tài khoản Anthropic của bạn để kết nối với dịch vụ.
*   `claude auth logout`: Đăng xuất khỏi tài khoản đang kết nối.
*   `claude update`: Cập nhật Claude CLI lên phiên bản mới nhất.
*   `claude agents`: Mở giao diện quản lý các tác vụ nền (background tasks) của tác nhân.

### Các lệnh đặc biệt (Slash Commands) bên trong phiên tương tác
Khi đã vào môi trường chat của `claude`, bạn có thể gõ các lệnh bắt đầu bằng dấu `/`:
*   `/help`: Hiển thị danh sách các lệnh hỗ trợ và phím tắt trong phiên trò chuyện.
*   `/clear`: Xóa lịch sử hội thoại hiện tại để bắt đầu một hội thoại mới (giúp tiết kiệm token).
*   `/permissions`: Quản lý quyền hạn cho các công cụ (ví dụ: cấp quyền tự động chạy lệnh, sửa file hoặc chặn các thao tác cụ thể).
*   `/init`: Tạo file cấu hình `CLAUDE.md` cho dự án để hướng dẫn Claude về cấu trúc thư mục, quy chuẩn code và kiểm thử của dự án.
*   `/goal <nội dung>`: Thiết lập hoặc cập nhật mục tiêu chính cho phiên làm việc hiện tại.

---

## 3. Antigravity CLI (`agy`)

**Antigravity CLI** (sử dụng lệnh `agy`) là giao diện dòng lệnh dạng terminal (TUI) thuộc hệ sinh thái phát triển phần mềm bằng AI của Google, được tối ưu hóa cho các thao tác lập trình tự động bằng bàn phím trên terminal hoặc phiên làm việc từ xa (SSH).

### Cách sử dụng cơ bản
*   Khởi chạy CLI bằng cách gõ: `agy` trong terminal tại thư mục dự án của bạn.
*   Để chạy một lệnh hệ thống trực tiếp từ thanh nhập liệu của `agy`, bắt đầu bằng dấu `!` (ví dụ: `!git status`).
*   Nhập `@` để kích hoạt gợi ý tự động hoàn thành đường dẫn file (path autocomplete).
*   Nhấn phím `Esc` hai lần liên tiếp để xóa nhanh nội dung đang nhập ở prompt (khi không có luồng phản hồi nào đang chạy).

### Các lệnh đặc biệt (Slash Commands) trong `agy` TUI
Gõ dấu `/` trong khung nhập liệu để mở menu lệnh:
*   `/help`: Hiển thị danh sách các lệnh và các phím tắt hệ thống.
*   `/add-dir <path>`: Thêm một thư mục vào workspace làm việc hiện tại của agent.
*   `/open <path>`: Mở trực tiếp file được chỉ định bằng trình biên tập mặc định của hệ thống.
*   `/agents`: Mở Bảng quản lý Agent (Agent Manager Panel) để theo dõi các tiến trình đang thực thi.
*   `/planning`: Bật chế độ lập kế hoạch nhiều bước trước khi thực hiện chỉnh sửa code.
*   `/fast`: Bật chế độ chạy nhanh (Fast mode) - bỏ qua các bước lập kế hoạch chi tiết để tối ưu thời gian.
*   `/diff`: Hiển thị thay đổi dưới dạng Unified Diff của những file đã chỉnh sửa.
*   `/model`: Lựa chọn hoặc đổi mô hình AI đang dùng.
*   `/mcp`: Quản lý các kết nối đến máy chủ giao thức MCP (Model Context Protocol) bên ngoài.
*   `/permissions`: Cấu hình các cấp độ quyền hạn (ví dụ: Auto-approve, Ask, Deny) đối với hành vi đọc/ghi file hoặc chạy lệnh terminal.
*   `/fork` hoặc `/branch`: Nhân bản phiên trò chuyện hiện tại thành một nhánh độc lập mới.
*   `/rename <name>`: Đổi tên phiên hội thoại hiện tại.
*   `/config` hoặc `/settings`: Mở trình chỉnh sửa cài đặt cấu hình dạng tương tác trực quan.
*   `/keybindings`: Thay đổi các phím tắt theo sở thích cá nhân.
*   `/btw <query>`: Đặt một câu hỏi bên lề (bằng cách mở một luồng phụ) mà không làm loãng mạch hội thoại chính.
*   `/clear`: Dọn sạch khung terminal và xóa ngữ cảnh hội thoại hiện thời.
*   `/exit`: Đóng phiên làm việc của Antigravity TUI.

---

## 4. GitHub CLI (`gh`)

**GitHub CLI** (`gh`) giúp bạn tương tác trực tiếp với các tính năng của GitHub (Issues, Pull Requests, Actions, Repositories...) ngay trong terminal mà không cần truy cập trang web.

### Xác thực tài khoản
*   `gh auth login`: Đăng nhập vào tài khoản GitHub của bạn (qua trình duyệt hoặc token).
*   `gh auth logout`: Đăng xuất khỏi tài khoản GitHub trên thiết bị.
*   `gh auth status`: Kiểm tra trạng thái đăng nhập hiện tại và tài khoản đang liên kết.

### Làm việc với Repository (Kho lưu trữ)
*   `gh repo clone <owner>/<repo>`: Nhân bản kho lưu trữ về máy cá nhân (nhanh hơn lệnh `git clone` truyền thống vì tự cấu hình ssh/https).
*   `gh repo create <name> [flags]`: Tạo một repository mới trên GitHub.
*   `gh repo view [<owner>/<repo>]`: Hiển thị thông tin tổng quan (README, mô tả) của repo hiện tại.

### Làm việc với Pull Request (PR)
*   `gh pr list`: Liệt kê các PR đang mở của repo.
*   `gh pr checkout <number>`: Tải mã nguồn của PR có số thứ tự `<number>` về nhánh cục bộ để chạy thử hoặc review.
*   `gh pr create [flags]`: Tạo một PR mới gửi lên GitHub từ nhánh hiện tại.
*   `gh pr status`: Xem trạng thái của các PR liên quan đến bạn hoặc nhánh hiện hành.
*   `gh pr view <number>`: Xem mô tả chi tiết, bình luận và trạng thái kiểm tra (checks) của một PR cụ thể.

### Làm việc với Issue (Vấn đề phát sinh)
*   `gh issue list`: Hiển thị danh sách các Issues trong dự án.
*   `gh issue create`: Tạo một Issue mới để báo cáo lỗi hoặc đề xuất tính năng.
*   `gh issue view <number>`: Xem chi tiết cuộc thảo luận của một Issue cụ thể.

### Làm việc với GitHub Actions & Workflows
*   `gh run list`: Xem danh sách các lượt chạy (runs) gần nhất của các workflow trong repo.
*   `gh run view <run-id>`: Xem tiến trình, logs và trạng thái chi tiết của một lượt chạy cụ thể.
*   `gh workflow list`: Liệt kê các workflow đã định nghĩa trong thư mục `.github/workflows/`.
*   `gh workflow run <filename>`: Kích hoạt thủ công một workflow (yêu cầu sự kiện `workflow_dispatch`).
