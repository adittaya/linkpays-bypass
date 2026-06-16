#!/usr/bin/env python3
"""
linkpays.in bypass — fully automated
=====================================
Usage:
  python3 bypass.py

Does everything automatically:
  1. Clicks goBtn on linkpays.in → registers view
  2. Navigates unlock chain (timer → verify → continue)
  3. Auto-types "OPEN" in the gate
  4. Auto-opens destination in your phone's browser
"""

import asyncio, os, random, pathlib, subprocess, sys
from playwright.async_api import async_playwright
from undetected_playwright import stealth_async

SHORT_LINK = 'https://linkpays.in/GE9Ky'
DEST      = 'https://getmodsapk.com/'
GATE_HTML = os.path.abspath(os.path.join(os.path.dirname(__file__) or '.', 'gate.html'))

PROXY = {}
if h := os.environ.get('PROXY_HOST'):
    PROXY['server'] = f'http://{h}:{os.environ["PROXY_PORT"]}'
    if os.environ.get('PROXY_USER'):
        PROXY['username'] = os.environ['PROXY_USER']
        PROXY['password'] = os.environ['PROXY_PASS']
    print(f'[+] Proxy: {h}:{os.environ["PROXY_PORT"]}')
else:
    print('[i] No proxy set — running from home/phone IP')

VIEWPORTS = [
    {'width': 1366, 'height': 768}, {'width': 1920, 'height': 1080},
    {'width': 1536, 'height': 864}, {'width': 1440, 'height': 900},
    {'width': 1280, 'height': 720}, {'width': 1440, 'height': 900},
]
UAS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
]

async def delay(b=0.5, e=1.5):
    await asyncio.sleep(b + random.random() * e)

async def scroll(page):
    for _ in range(random.randint(3, 6)):
        await page.evaluate(f'window.scrollBy(0, {random.randint(200,600) * random.choice([1,-1])})')
        await delay(0.3, 1.0)

async def move_mouse(page, x=None, y=None):
    vp = await page.evaluate('({w: window.innerWidth, h: window.innerHeight})')
    tx, ty = x or random.randint(100, vp['w']-100), y or random.randint(100, vp['h']-100)
    cur = await page.evaluate('({x: window.mx||0, y: window.my||0})')
    for i in range(1, random.randint(8, 16)):
        t = i / 16
        await page.mouse.move(
            cur['x'] + (tx - cur['x']) * t + random.randint(-15, 15),
            cur['y'] + (ty - cur['y']) * t + random.randint(-15, 15)
        )
        await asyncio.sleep(random.uniform(0.01, 0.04))
    await page.evaluate(f'window.mx={tx};window.my={ty}')

async def click(page, sel):
    el = page.locator(sel)
    box = await el.bounding_box()
    if box:
        cx = box['x'] + box['width']/2 + random.randint(-5, 5)
        cy = box['y'] + box['height']/2 + random.randint(-5, 5)
        await move_mouse(page, cx, cy)
        await delay(0.1, 0.2)
        await page.mouse.click(cx, cy)
        await delay(0.2, 0.4)
    else:
        await el.click(force=True)

async def make_ctx(p):
    vp, ua = random.choice(VIEWPORTS), random.choice(UAS)
    # Use full Chromium with --headless=new (not headless shell)
    browser = await p.chromium.launch(
        headless=False,
        proxy=PROXY or None,
        args=[
            '--headless=new',
            '--no-sandbox','--disable-gpu',
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
        ]
    )
    ctx = await browser.new_context(
        viewport=vp, user_agent=ua,
        locale=random.choice(['en-US','en-IN','en-GB']),
        timezone_id=random.choice(['Asia/Kolkata','America/New_York','Europe/London']),
        device_scale_factor=random.choice([1, 2]),
        has_touch=False,
        is_mobile=False,
    )
    ctx = await stealth_async(ctx)
    await ctx.add_init_script('''
        Object.defineProperty(navigator,'webdriver',{get:()=>false});
        Object.defineProperty(navigator,'plugins',{get:()=>[{name:'Chrome PDF Plugin'},{name:'Chrome PDF Viewer'},{name:'Chrome PDF Plugin'}]});
        window.chrome={runtime:{},app:{isInstalled:false}};
        const origQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (p) => p.name==='notifications'
            ? Promise.resolve({state:'denied'}) : origQuery(p);
    ''')
    page = await ctx.new_page()
    await page.evaluate('window.mx=0;window.my=0;')
    return browser, ctx, page, vp

async def handle_unlock(page):
    body = (await page.evaluate('document.body?.innerText?.substring(0,200)')) or ''
    if 'Access Denied' in body or 'Automated access' in body:
        print('  [!] Blocked'); return None
    has = await page.evaluate('''()=>({
        w1:!!document.getElementById('tp-wait1'),
        unlockBtn:!!document.getElementById('tp-unlock-btn'),
        verify:!!document.getElementById('tp-verify'),
        snp2:!!document.getElementById('tp-snp2')
    })''')
    if not any(has.values()):
        print('  [-] No unlock elements'); return None
    if has['snp2']:
        return {'action': 'click', 'sel': '#tp-snp2'}
    await scroll(page); await delay(1, 2)
    print('  [~] Waiting for timer...', end='', flush=True)
    for s in range(60):
        try:
            if await page.locator('#tp-unlock-btn').is_visible():
                print(f' {s}s'); break
        except: pass
        await asyncio.sleep(1)
    else: print(' timed out'); return None
    await scroll(page); await delay(0.5, 1)
    await click(page, '#tp-unlock-btn'); print('  [+] unlock clicked')
    await delay(1, 2)
    for s in range(15):
        try:
            if await page.locator('#tp-verify').is_visible():
                await click(page, '#tp-verify'); print(f'  [+] verify clicked ({s}s)'); break
        except: pass
        await asyncio.sleep(1)
    else: return None
    await delay(1, 3)
    for s in range(30):
        try:
            if await page.locator('#tp-snp2').is_visible():
                print(f'  [+] continue visible ({s}s)')
                return {'action': 'click', 'sel': '#tp-snp2'}
        except: pass
        await asyncio.sleep(1)
    print('  [-] Continue never appeared'); return None

async def run():
    write_gate()

    async with async_playwright() as p:
        browser, ctx, page, vp = await make_ctx(p)
        print(f'[+] Viewport: {vp["width"]}x{vp["height"]}')

        # ---------- linkpays.in ----------
        print('\n--- linkpays.in ---')
        await page.goto(SHORT_LINK, wait_until='domcontentloaded', timeout=30000)
        await delay(3, 4); await scroll(page); await delay(2, 3)

        # Listen for requests to track the view-counter call
        view_sent = False
        async def track_request(req):
            nonlocal view_sent
            if 'linkpays' in req.url and req.method == 'POST':
                view_sent = True
                print(f'  [>] View counter hit: {req.url[:80]}')
        page.on('request', track_request)

        if await page.evaluate('!!document.getElementById("goBtn")'):
            await click(page, '#goBtn')
            print('[+] goBtn clicked — waiting for view to register...')
            # Wait for view counter POST to go out + dwell time
            await page.wait_for_timeout(6000)
            if view_sent:
                print('[+] View counter request confirmed!')
            else:
                print('[~] No explicit POST caught — view may still count')
        await delay(2, 3)
        print(f'  -> {page.url}')

        # ---------- Unlock chain ----------
        print('\n--- Monetization chain ---')
        for hop in range(5):
            act = await handle_unlock(page)
            if not act: break
            if act['action'] == 'click':
                sel = act['sel']
                try:
                    await click(page, sel)
                except:
                    await page.evaluate(f'document.querySelector("{sel}")?.dispatchEvent(new MouseEvent("click",{{bubbles:true}}))')
                await delay(3, 5)
                print(f'  -> {page.url}')

        # ---------- Gate + auto-unlock ----------
        print('\n--- Auto gate ---')
        await page.goto(f'file://{GATE_HTML}', wait_until='domcontentloaded')
        await delay(1, 1.5)

        dest_page = None
        async def on_page(new_page):
            nonlocal dest_page
            dest_page = new_page
            try:
                await new_page.wait_for_load_state()
            except:
                pass
        ctx.on('page', on_page)

        inp = page.locator('#code')
        await inp.click()
        await delay(0.2, 0.4)
        await page.keyboard.type('OPEN', delay=random.randint(60, 130))
        await delay(0.5, 1)

        btn = page.locator('#goBtn')
        await btn.wait_for(state='visible', timeout=5000)
        await click(page, '#goBtn')
        print('  [+] Gate unlocked — destination loaded in background')
        await delay(2, 3)

        if dest_page:
            print(f'  [+] Loaded: {dest_page.url}')
            await dest_page.close()

        await browser.close()

    # ---------- Open on phone ----------
    print('\n--- Opening on phone ---')
    try:
        r = subprocess.run(['termux-open-url', DEST], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            print(f'  [+] termux-open-url succeeded')
        else:
            print(f'  [!] termux-open-url failed: {r.stderr.strip()}')
    except FileNotFoundError:
        print('  [!] termux-open-url not found — install Termux:API')
    except Exception as e:
        print(f'  [!] {e}')

    print(f'\n{"="*55}')
    print(f'  DONE — ')
    print(f'  1. View sent to linkpays dashboard')
    print(f'  2. Destination ready:')
    print(f'     {DEST}')
    print(f'')
    print(f'  If browser didn\'t auto-open, paste the URL above')
    print(f'{"="*55}')

def write_gate():
    pathlib.Path(GATE_HTML).write_text(f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Unlock</title><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#0f172a,#1e293b);min-height:100vh;display:flex;align-items:center;justify-content:center}}
.card{{background:#fff;border-radius:24px;padding:3rem 2.5rem;width:100%;max-width:420px;box-shadow:0 25px 50px rgba(0,0,0,.25);text-align:center}}
.icon{{font-size:3rem;margin-bottom:1rem}}
h2{{color:#0f172a;font-size:1.5rem;margin-bottom:.5rem}}
p{{color:#64748b;font-size:.9rem;margin-bottom:1.5rem;line-height:1.5}}
input{{width:100%;padding:14px 16px;border:2px solid #e2e8f0;border-radius:12px;font-size:1rem;outline:none;transition:.2s;text-align:center;letter-spacing:2px;font-weight:600;margin-bottom:1rem}}
input:focus{{border-color:#3b82f6;box-shadow:0 0 0 3px rgba(59,130,246,.15)}}
.btn{{display:none;width:100%;padding:16px;background:linear-gradient(135deg,#2563eb,#3b82f6);color:#fff;border:none;border-radius:12px;font-size:1rem;font-weight:700;cursor:pointer;transition:.3s;box-shadow:0 4px 14px rgba(59,130,246,.4)}}
.btn:hover{{transform:translateY(-2px);filter:brightness(1.1)}}
</style></head><body><div class="card"><div class="icon">🔓</div><h2>Destination Locked</h2><p>Type <strong>OPEN</strong> to unlock your download link</p>
<input type="text" id="code" placeholder="Type OPEN here..." maxlength="4" autocomplete="off">
<button class="btn" id="goBtn" onclick="proceed()">Open Destination →</button></div>
<script>
const i=document.getElementById('code'),b=document.getElementById('goBtn');
i.addEventListener('input',()=>{{b.style.display=i.value.toUpperCase()==='OPEN'?'block':'none';i.style.borderColor=i.value.toUpperCase()==='OPEN'?'#10b981':'#e2e8f0'}});
function proceed(){{b.disabled=true;b.textContent='Opening...';window.open('{DEST}','_blank');setTimeout(()=>b.textContent='Opened!',1000)}}
</script></body></html>''')

if __name__ == '__main__':
    asyncio.run(run())
