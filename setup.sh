#!/usr/bin/env bash
set -e

echo "=================================="
echo " linkpays-bypass — Auto Setup"
echo "=================================="

# ---- Check Python ----
if ! command -v python3 &>/dev/null; then
    echo "[!] Python3 not found. Install it first."
    echo "    apt install python3 python3-pip"
    exit 1
fi

PIP_ARGS=""
python3 -m pip --version | grep -q "externally-managed" && PIP_ARGS="--break-system-packages" || true
# PEP 668 check
python3 -c "import sys; sys.exit(0)" 2>/dev/null
python3 -m pip install --quiet --upgrade pip $PIP_ARGS 2>/dev/null || true

# ---- Install pip packages ----
echo "[1/3] Installing Python dependencies..."
python3 -m pip install --quiet playwright undetected_playwright $PIP_ARGS
echo "  Done."

# ---- Install Playwright system deps ----
echo "[2/3] Installing Playwright system dependencies..."
if command -v apt &>/dev/null; then
    apt update -qq && apt install -y -qq libnss3 libnspr4 libatk-bridge2.0-0 libdrm2 \
        libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
        libpango-1.0-0 libcairo2 libasound2 libatspi2.0-0 2>/dev/null || true
fi
python3 -m playwright install-deps chromium 2>/dev/null || true
echo "  Done."

# ---- Install Chromium browser ----
echo "[3/3] Installing Chromium browser..."
python3 -m playwright install chromium 2>&1 | tail -1

echo ""
echo "=================================="
echo " Setup complete! Starting bypass..."
echo "=================================="
echo ""

# ---- Run bypass ----
python3 "$(dirname "$0")/bypass.py"
