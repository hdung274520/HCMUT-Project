#!/usr/bin/env bash
# =============================================================
# One-shot environment setup for the Voice Agent (Ubuntu / CPU-only).
# Creates a Conda env "voice-agent" (Python 3.11) with the system audio
# libs, installs Python deps, and prepares .env.local.
# =============================================================
set -euo pipefail

ENV_NAME="voice-agent"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

# --- 1. Make sure conda exists (install Miniconda if missing) -------------
if ! command -v conda >/dev/null 2>&1; then
  if [ -x "$HOME/miniconda3/bin/conda" ]; then
    :
  else
    echo "==> Miniconda chưa có. Đang cài vào ~/miniconda3 ..."
    tmp="$(mktemp -d)"
    curl -fsSL https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o "$tmp/mc.sh"
    bash "$tmp/mc.sh" -b -p "$HOME/miniconda3"
    rm -rf "$tmp"
  fi
  export PATH="$HOME/miniconda3/bin:$PATH"
fi
# shellcheck disable=SC1091
source "$(conda info --base)/etc/profile.d/conda.sh"

# --- 2. Create the env with Python 3.11 + system audio binaries -----------
if ! conda env list | grep -qE "^${ENV_NAME}\s"; then
  echo "==> Tạo môi trường conda '${ENV_NAME}' (Python 3.11)..."
  conda create -y -n "$ENV_NAME" -c conda-forge \
    python=3.11 pip ffmpeg libsndfile portaudio
fi

conda activate "$ENV_NAME"

# --- 3. Python dependencies ----------------------------------------------
# Use `python -m pip` so packages always land in THIS env (a bare `pip` can
# fall through to the base env if the env's pip is missing).
echo "==> Cài thư viện Python..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# --- 4. .env.local --------------------------------------------------------
if [ ! -f .env.local ]; then
  cp .env.example .env.local
  echo "==> Đã tạo .env.local — nhớ điền GEMINI_API_KEY nếu dùng MODE=api."
fi

# --- 5. Local model assets (Piper voice for the chosen language) ----------
echo "==> Tải Piper voice (cho TTS offline)..."
python download_models.py || echo "  (bỏ qua — chỉ cần khi dùng TTS=piper)"

echo
echo "================================================================"
echo " Hoàn tất! Lần sau chỉ cần:"
echo "   conda activate ${ENV_NAME}"
echo "   python run.py            # chat bằng giọng nói"
echo "   python run.py --text     # chat bằng cách gõ (test nhanh)"
echo "================================================================"
