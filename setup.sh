#!/usr/bin/env bash
set -e

echo "=================================="
echo " linkpays-bypass — Auto Setup"
echo "=================================="

if ! command -v python3 &>/dev/null; then
    echo "[!] Python3 not found: apt install python3 python3-pip python3-venv"
    exit 1
fi

echo "[1/3] Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate
python3 -m pip install --quiet --upgrade pip
python3 -m pip install --quiet playwright undetected_playwright
echo "  Done."

echo "[2/3] Installing system dependencies..."
if command -v apt &>/dev/null; then
    apt update -qq && apt install -y -qq libnss3 libnspr4 libatk-bridge2.0-0 libdrm2 \
        libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
        libpango-1.0-0 libcairo2 libasound2 libatspi2.0-0 2>/dev/null || true
fi
python3 -m playwright install-deps chromium 2>/dev/null || true
echo "  Done."

echo "[3/3] Installing Chromium browser..."
python3 -m playwright install chromium 2>&1 | tail -1

echo ""
echo "=================================="
echo " Setup complete! Starting bypass..."
echo "=================================="
echo ""

# Run bypass using venv python
VENV_PYTHON="$(dirname "$0")/venv/bin/python3"
if [ -f "$VENV_PYTHON" ]; then
    "$VENV_PYTHON" "$(dirname "$0")/bypass.py"
else
    python3 "$(dirname "$0")/bypass.py"
fi
