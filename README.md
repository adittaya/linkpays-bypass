# linkpays-bypass

Automated click bot for linkpays.in short links — registers a view on your dashboard, navigates the unlock chain, and presents a type-to-unlock gate page.

## Quick Start

```bash
git clone https://github.com/adittaya/linkpays-bypass.git
cd linkpays-bypass
chmod +x setup.sh
./setup.sh
```

This installs everything (Playwright, Chromium, dependencies) and runs the script.

## What it does

1. Opens `linkpays.in/GE9Ky` — clicks the `goBtn` to register a view
2. Navigates through the redirect chain (rank1st.in → savepe.in → ...)
3. Handles unlock flows (timer → unlock → verify → continue)
4. Opens a gate page — type **OPEN** to reveal the destination button
5. Click the button — destination opens in a new tab

## Usage

```bash
# From home (no proxy needed):
python3 bypass.py

# With residential proxy:
PROXY_HOST=res.example.com PROXY_PORT=12345 \
PROXY_USER=user PROXY_PASS=pass \
python3 bypass.py
```

## Requirements

- Python 3.8+
- Internet connection
- From a **residential/home IP** for views to count (data-center IPs are filtered by linkpays.in)

## Gate Page

After the script runs, open `gate.html` in your browser. Type `OPEN` in the input field — the destination button appears. Click it to open the target URL in a new tab.
