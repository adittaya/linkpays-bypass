#!/usr/bin/env bash
set -e

echo "=================================="
echo " linkpays-bypass — Auto Setup"
echo "=================================="

# ---- Check Python ----
if ! command -v python3 &>/dev/null; then
    echo "[!] Python3 not found. Install it first."
    echo "    Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "    macOS: brew install python3"
    exit 1
fi

# ---- Install pip packages ----
echo "[1/3] Installing Python dependencies..."
python3 -m pip install --quiet --upgrade pip
python3 -m pip install --quiet playwright undetected_playwright
echo "  Done."

# ---- Install Playwright system deps if on Linux ----
if [[ "$(uname)" == "Linux" ]]; then
    echo "[2/3] Installing Playwright system dependencies..."
    python3 -m playwright install-deps chromium 2>/dev/null || true
fi

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
