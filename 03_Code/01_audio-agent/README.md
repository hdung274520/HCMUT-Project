# Voice Agent — Chatbot giao tiếp bằng âm thanh

Trợ lý hội thoại bằng giọng nói cho dự án *Medical Signal Audio Assistant*.
Pipeline: **Microphone → STT → LLM → TTS → Loa**, chạy tốt trên laptop CPU-only
(Intel i5-1135G7, không GPU NVIDIA).

Mỗi khối (STT / TTS / LLM) có **2 lựa chọn: API (online) hoặc Local (offline)**,
chọn qua biến môi trường.

| Khối | Local (offline) | API (online) |
|------|-----------------|--------------|
| STT  | `faster_whisper` (mặc định `distil-medium.en` trên PC, `tiny` trên Pi — int8 CPU) | `gemini` (đa phương thức, chỉ cần GEMINI key) |
| LLM  | `ollama` (mặc định `qwen2.5:0.5b`) | `gemini` (gemini-1.5-flash) |
| TTS  | `piper` (ONNX, rất nhanh — mặc định) | `gtts` (Google Translate, không cần key) |

Các model mặc định trên là **kết quả benchmark**, không phải lựa chọn tuỳ ý — xem
[mục Benchmark](#benchmark-chọn-model) bên dưới.

Hai profile dựng sẵn qua `MODE`:
- `MODE=api`  → STT=gemini, LLM=gemini, TTS=gtts — chỉ cần **GEMINI_API_KEY**, không tốn CPU.
- `MODE=local` → STT=faster_whisper, LLM=ollama, TTS=piper — **100% offline**.

Bạn cũng có thể trộn (vd STT local + LLM api) bằng các biến `STT_PROVIDER` / `LLM_PROVIDER` / `TTS_PROVIDER`.

---

## 1. Cài đặt (một lần)

```bash
cd 04_Code/01_audio-agent
bash setup.sh
```

Script sẽ: cài Miniconda (nếu chưa có) → tạo env `voice-agent` (Python 3.11) kèm
`ffmpeg`, `libsndfile`, `portaudio` → cài thư viện Python → tạo `.env.local` →
tải Piper voice.

> Vì sao Conda? Python hệ thống của bạn là 3.14 (quá mới cho `faster-whisper`/`ctranslate2`),
> và các thư viện âm thanh cần binary hệ thống. Conda cài Python 3.11 + các binary này
> mà không cần `sudo`. Xem [03_Outputs/02_Conda.md](../../03_Outputs/02_Conda.md).

## 2. Cấu hình

Sửa `.env.local`:
- Dùng cloud: đặt `MODE=api` và điền `GEMINI_API_KEY`
  (lấy miễn phí ở https://aistudio.google.com/apikey).
- Dùng offline: đặt `MODE=local` (xem bước Ollama bên dưới).
- `LANGUAGE=vi` hoặc `en`.

## 3. Chạy

### a) Giao diện Web (khuyên dùng) — thu âm ngay trong trình duyệt

```bash
conda activate voice-agent
python server.py                 # mở http://localhost:8000
PORT=8080 python server.py       # đổi port nếu 8000 đang bận
```

Mở trình duyệt vào `http://localhost:8000`:
- Nhấn nút 🎤 để nói, nhấn lần nữa để gửi → bot trả lời bằng chữ + đọc ra loa.
- Hoặc gõ tin nhắn vào ô bên dưới.
- Nút ↺ để xoá hội thoại.

Truy cập từ điện thoại/máy khác trong cùng mạng LAN: `http://<IP-máy-chủ>:8000`
(lưu ý: micro trong trình duyệt cần `https` hoặc `localhost`; trên LAN dùng IP có thể
bị chặn micro — khi đó dùng máy chủ tại chỗ hoặc bật https).

### b) Dòng lệnh (CLI)

```bash
python run.py            # hội thoại rảnh tay bằng giọng nói (Ctrl+C để thoát)
python run.py --text     # gõ chữ để test nhanh (vẫn đọc câu trả lời ra loa)
```

Nói "tạm biệt" / "goodbye" để kết thúc lượt thoại.

## 4. (Tùy chọn) Chạy LLM offline với Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh   # cài Ollama
ollama pull qwen2.5:0.5b                          # model mặc định — ~400MB, nhanh nhất trong benchmark
ollama serve                                      # chạy nền (thường tự chạy)
```
Rồi đặt `MODE=local` (hoặc `LLM_PROVIDER=ollama`) trong `.env.local`.

## 5. Tinh chỉnh micro

Nếu agent ngắt lời quá sớm/muộn, chỉnh trong `.env.local`:
- `SILENCE_THRESHOLD` — ngưỡng coi là im lặng (phòng ồn thì tăng lên).
- `SILENCE_DURATION` — số giây im lặng để kết thúc lượt nói.

## Cấu trúc

```
01_audio-agent/
├── run.py               # chạy CLI (giọng nói / --text)
├── server.py            # web server (FastAPI), phục vụ dashboard ở ../04_web-app
├── download_models.py   # tải Piper voice
├── setup.sh             # dựng môi trường conda
├── requirements.txt
├── .env.example         # mẫu cấu hình -> copy thành .env.local
└── src/
    ├── config.py        # đọc .env, chọn provider theo MODE
    ├── audio.py         # thu mic (VAD theo năng lượng) + phát loa
    ├── stt.py           # FasterWhisperSTT | GeminiSTT
    ├── tts.py           # PiperTTS | GTTSTTS
    ├── llm.py           # GeminiLLM | OllamaLLM
    └── agent.py         # vòng lặp hội thoại
```

> Gợi ý cho Raspberry Pi 4 (target edge): dùng `MODE=local` với `WHISPER_MODEL=tiny`
> và TTS `piper` để chạy nhẹ; hoặc STT `gemini` nếu có mạng để tiết kiệm CPU.

## Benchmark chọn model

Ba harness độc lập trong `test_ui/` (`/test` = STT, `/test2` = TTS, `/test3` = LLM)
dùng để so sánh các model trong từng khối trên cùng 3 câu mẫu (ngắn/vừa/dài, có số
liệu sinh hiệu). Kết quả log tại `logs/{stt_test_time,tts_test_times,llm_test_times}.csv`.
Model mặc định trong `src/config.py` hiện đã chốt theo kết quả này:

- **TTS → `piper`**: RTF ~0.04-0.05× (rất nhanh, dưới thời gian thực), điểm chất
  lượng trung bình 3.67/5, không có ghi chú lỗi. `silero` chậm hơn nhiều (RTF có
  lúc lên 2×) và bị ghi chú "robot, mất số" ở câu dài; `kokoro` chất lượng tương
  đương piper nhưng chậm hơn 20-50 lần; `mms`/`espeak` phát âm sai số hoặc quá máy móc.
- **LLM → `qwen2.5:0.5b`**: nhanh nhất (1.3-1.4s/lượt) trong khi vẫn đồng hạng
  điểm chất lượng cao nhất (3.67/5) với các model lớn hơn nhiều (`qwen2.5:1.5b`,
  `llama3.1:8b`). Các model "thinking" (`qwen3:4b/8b`) mất 40-120s/lượt — không
  dùng được cho hội thoại thời gian thực.
- **STT → `distil-medium.en`** (PC) / **`tiny`** (Pi): độ chính xác số liệu y tế
  (huyết áp, nhịp tim) tương đương `medium` gốc ở cả 3 câu test, nhưng nhanh hơn
  ~26% (~3.6s so với ~4.9s/lượt) — quan trọng cho độ trễ hội thoại thời gian thực.

Muốn test lại hoặc thử model khác: mở `/test`, `/test2`, `/test3` khi server đang
chạy, rồi cập nhật lựa chọn trong `src/config.py` / `.env.local` nếu kết quả thay đổi.
