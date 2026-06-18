# Hướng dẫn Ứng dụng Conda trong Dự án Medical Signal Audio Assistant

Tài liệu này giải thích chi tiết về Conda, lợi ích của việc sử dụng nó, cách nó giải quyết các vấn đề đặc thù trong dự án **Medical Signal Audio Assistant**, và hướng dẫn cấu hình môi trường ảo đồng nhất trên cả máy trạm phát triển (**Fedora Bridge PC**) và thiết bị nhúng (**Raspberry Pi 4 Edge**).

---

## 1. Conda là gì?

**Conda** là một hệ thống quản lý gói (Package Manager) và quản lý môi trường ảo (Environment Manager) mã nguồn mở, hoạt động đa nền tảng (Linux, macOS, Windows). 

*   **Quản lý môi trường (Environment Management):** Giúp tạo ra các không gian làm việc cô lập (sandbox). Mỗi môi trường có thể chạy một phiên bản Python riêng và các thư viện riêng, hoàn toàn độc lập với các môi trường khác và hệ thống gốc, tránh lỗi xung đột phiên bản ("Dependency Hell").
*   **Quản lý gói (Package Management):** Giúp cài đặt, cập nhật, gỡ bỏ các thư viện. Điểm mạnh vượt trội của Conda là khả năng quản lý và cài đặt các thư viện biên dịch nhị phân hệ thống (như CUDA Toolkit, FFmpeg, OpenSSL, Compilers...) chứ không chỉ giới hạn ở gói Python thuần túy.

### Phân biệt Conda, Miniconda và Anaconda

*   **Conda:** Là công cụ dòng lệnh (CLI tool) thực hiện các tác vụ quản lý gói và môi trường.
*   **Miniconda:** Là phiên bản tối giản được khuyên dùng cho lập trình viên. Chỉ chứa Python, Conda và một vài gói tối thiểu. Dung lượng cài đặt nhỏ gọn (~100-200MB).
*   **Anaconda:** Là phiên bản phân phối đầy đủ cho Khoa học dữ liệu (Data Science). Nó tích hợp sẵn Conda kèm hơn 1,500 thư viện khoa học phổ biến (như NumPy, Pandas, Scipy, Jupyter Notebook, TensorFlow...). Dung lượng cài đặt rất lớn (~3GB+).

### So sánh chi tiết: Conda vs. Pip + Venv

| Tiêu chí so sánh | `pip` + `venv` (Mặc định của Python) | Conda (Miniconda / Anaconda) |
| :--- | :--- | :--- |
| **Phạm vi quản lý** | Chỉ quản lý các gói Python (PyPI). | Quản lý gói đa ngôn ngữ (Python, C/C++, R, Node.js...) và các nhị phân hệ thống. |
| **Quản lý phiên bản Python** | Phụ thuộc vào phiên bản Python cài sẵn trên hệ điều hành. Rất khó để chạy một môi trường chạy Python 3.9 trên máy chỉ cài Python 3.11 nếu không tự biên dịch Python. | Tự động tải xuống và cài đặt bất kỳ phiên bản Python nào được yêu cầu mà không phụ thuộc hệ điều hành. |
| **Dependencies hệ thống (C/C++, Audio, CUDA...)** | Không tự cài được. Người dùng phải tự cài thủ công qua trình quản lý hệ thống (như `dnf` trên Fedora, `apt` trên Debian/Pi) bằng quyền root `sudo`. | Tự động tải các gói nhị phân đã biên dịch sẵn (như `ffmpeg`, `libsndfile`, `cuda-toolkit`) trực tiếp vào môi trường ảo, không cần quyền root. |
| **Độ tin cậy cài đặt** | Thường phải biên dịch từ mã nguồn đối với một số thư viện C/C++ phức tạp, dễ gây lỗi compile thất bại nếu thiếu thư viện dev trên máy. | Cung cấp sẵn các gói nhị phân (Pre-compiled binaries) đã được tối ưu hóa cho từng kiến trúc CPU (x86_64, ARM64). |

---

## 2. Ứng dụng Conda vào dự án Medical Signal Audio Assistant

Dự án [Medical Signal Audio Assistant](file:///home/hdung274520/Project/README.md) của chúng ta có các đặc thù công nghệ rất phức tạp, kết hợp giữa **Xử lý tín hiệu não bộ/y tế**, **Học máy (AI/ML)** và **Trợ lý âm thanh (Voice Agent WebRTC)**. Dưới đây là cách Conda giải quyết triệt để các bài toán này:

### 2.1. Quản lý thư viện âm thanh phức tạp không cần quyền Root
Để Voice Agent hoạt động trơn tru (như cấu hình trong [requirements.txt](file:///home/hdung274520/Project/04_Code/audio-agent/requirements.txt)), hệ thống cần các thư viện nhị phân bên ngoài:
*   `soundfile` yêu cầu thư viện hệ thống `libsndfile`.
*   `faster-whisper` và `kokoro` yêu cầu công cụ xử lý media `ffmpeg` để convert/stream luồng âm thanh WebRTC.
*   **Nếu dùng `venv`:** Ta buộc phải chạy `sudo dnf install ffmpeg libsndfile` trên Fedora PC. Nhưng trên Raspberry Pi 4, người dùng có thể gặp khó khăn hoặc không có quyền root.
*   **Giải pháp với Conda:** Ta định nghĩa `ffmpeg` và `libsndfile` trong danh sách cài đặt của Conda. Conda sẽ tải bản build portable trực tiếp vào thư mục môi trường của dự án, đảm bảo chạy ăn ngay mà không can thiệp vào hệ điều hành.

### 2.2. Đồng bộ hóa môi trường giữa Fedora và Raspberry Pi 4 (ARM64)
*   **Thách thức:** Raspberry Pi 4 chạy kiến trúc ARM64, trong khi máy trạm Fedora của bạn chạy x86_64. Khi cài đặt thư viện Bluetooth hay xử lý tín hiệu như `BrainFlow` (để kết nối Muse 2), việc biên dịch trên Pi 4 rất mất thời gian và dễ lỗi.
*   **Giải pháp với Conda:** Kênh cài đặt phổ biến `conda-forge` hỗ trợ đầy đủ các bản build nhị phân cho cả hai kiến trúc `linux-64` và `linux-aarch64` (ARM64). Bạn có thể định nghĩa chung một tệp cấu hình và chạy lệnh cài đặt giống hệt nhau ở cả 2 thiết bị.

### 2.3. Hỗ trợ huấn luyện mô hình Học máy (GRU/RNN) với GPU/CUDA
*   Khi phát triển và đánh giá mô hình học sâu tại các thư mục [06_Models/](file:///home/hdung274520/Project/06_Models) và [07_Experiments/](file:///home/hdung274520/Project/07_Experiments), bạn cần sử dụng PyTorch có hỗ trợ GPU trên Fedora để tăng tốc.
*   Việc cài đặt driver CUDA hệ thống và khớp nối phiên bản với PyTorch thường rất phức tạp trên Fedora. 
*   **Giải pháp với Conda:** Cài đặt thông qua lệnh `conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia`. Conda sẽ tự tải gói `pytorch-cuda` chứa tất cả các thư viện runtime CUDA cần thiết một cách khép kín.

---

## 3. Hướng dẫn thiết lập chi tiết trong dự án

Dưới đây là quy trình ứng dụng thực tế để chuyển đổi từ `venv` sang **Conda** cho thư mục [audio-agent/](file:///home/hdung274520/Project/04_Code/audio-agent).

### Bước 1: Cài đặt Miniconda trên Fedora Linux

Chạy các lệnh sau trong terminal của máy Fedora:

```bash
# Tải về bộ cài đặt Miniconda
mkdir -p ~/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh

# Chạy cài đặt âm thầm (silent install)
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm -rf ~/miniconda3/miniconda.sh

# Khởi tạo conda cho bash shell
~/miniconda3/bin/conda init bash
```
> [!NOTE]
> Sau khi cài đặt xong, bạn hãy **khởi động lại Terminal** (hoặc chạy lệnh `source ~/.bashrc`) để Conda được kích hoạt.

### Bước 2: Tạo tệp cấu hình `environment.yml` cho Audio Agent

Để quản lý thống nhất các gói cài đặt từ cả Conda và Pip, chúng ta tạo một file cấu hình định nghĩa môi trường mang tên `environment.yml` nằm trong thư mục [audio-agent/](file:///home/hdung274520/Project/04_Code/audio-agent):

```yaml
name: medical-audio-agent
channels:
  - conda-forge
  - pytorch
  - defaults
dependencies:
  # Cài đặt phiên bản Python cố định
  - python=3.11
  
  # Cài đặt các thư viện hệ thống cần thiết cho âm thanh và tính toán
  - ffmpeg
  - libsndfile
  - numpy
  - scipy
  - scikit-learn
  
  # Quản lý các thư viện Python chuyên biệt qua pip
  - pip
  - pip:
      - livekit-agents
      - livekit-plugins-google
      - livekit-plugins-silero
      - faster-whisper
      - kokoro
      - python-dotenv
      - brainflow
      - mne
```

### Bước 3: Tạo và Kích hoạt Môi trường ảo

Di chuyển vào thư mục code và tạo môi trường từ file cấu hình trên:

```bash
cd /home/hdung274520/Project/04_Code/audio-agent

# Tạo môi trường dựa trên tệp environment.yml
conda env create -f environment.yml

# Kích hoạt môi trường ảo vừa tạo
conda activate medical-audio-agent
```

Nếu sau này bạn có thêm thư viện mới vào file `environment.yml`, bạn chỉ cần cập nhật môi trường bằng lệnh:
```bash
conda env update -f environment.yml --prune
```

---

## 4. Các câu lệnh Conda thông dụng ("Cheat Sheet")

Dưới đây là danh sách các lệnh bỏ túi cần thiết khi làm việc với Conda trong dự án này:

| Lệnh | Chức năng |
| :--- | :--- |
| `conda env list` | Liệt kê toàn bộ các môi trường ảo Conda đang có trên máy của bạn. |
| `conda activate <tên_môi_trường>` | Kích hoạt môi trường ảo. |
| `conda deactivate` | Tắt/thoát khỏi môi trường ảo hiện tại. |
| `conda list` | Xem danh sách các gói thư viện đã được cài đặt trong môi trường hiện tại. |
| `conda install <tên_gói>` | Cài đặt trực tiếp một thư viện từ các kênh (channels) mặc định. |
| `conda install -c conda-forge <tên_gói>` | Cài đặt thư viện từ kênh cộng đồng `conda-forge` (rất khuyến khích cho các gói Linux/Raspberry Pi). |
| `conda remove <tên_gói>` | Gỡ cài đặt thư viện khỏi môi trường ảo. |
| `conda env remove -n <tên_môi_trường>` | Xóa hoàn toàn một môi trường ảo để giải phóng ổ đĩa. |

---
> [!IMPORTANT]
> **Khuyến nghị cho dự án:** Để duy trì sự sạch sẽ của mã nguồn và tính nhất quán, hãy bổ sung thư mục `.conda` hoặc các tệp cache conda vào `.gitignore` để tránh đẩy dữ liệu rác lên Git repository.
