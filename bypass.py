#!/usr/bin/env python3
"""
linkpays.in auto-clicker + type-to-unlock gate
===============================================
Usage:
  python3 bypass.py

Environment (optional - only if using a proxy):
  PROXY_HOST   - proxy hostname
  PROXY_PORT   - proxy port
  PROXY_USER   - proxy username (optional)
  PROXY_PASS   - proxy password (optional)

The script:
  1. Clicks goBtn on linkpays.in to register a view
  2. Handles any unlock chain (timer → verify → continue)
  3. Opens a gate page — type "OPEN" to reveal the destination button
"""

import asyncio, os, random, pathlib
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
    print('[i] No proxy — will only count views from a residential/home IP')
    print('    Set PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS if needed')

VIEWPORTS = [
    {'width': 1366, 'height': 768}, {'width': 1920, 'height': 1080},
    {'width': 1536, 'height': 864}, {'width': 1440, 'height': 900},
]
UAS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
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
    browser = await p.chromium.launch(
        headless=True,
        proxy=PROXY or None,
        args=['--no-sandbox','--disable-gpu','--disable-blink-features=AutomationControlled']
    )
    ctx = await browser.new_context(
        viewport=vp, user_agent=ua,
        locale=random.choice(['en-US','en-IN']),
        timezone_id=random.choice(['Asia/Kolkata','America/New_York'])
    )
    ctx = await stealth_async(ctx)
    await ctx.add_init_script('''
        Object.defineProperty(navigator,'webdriver',{get:()=>false});
        Object.defineProperty(navigator,'plugins',{get:()=>[{name:'Chrome PDF Plugin'},{name:'Chrome PDF Viewer'}]});
        window.chrome={runtime:{},app:{isInstalled:false}};
    ''')
    page = await ctx.new_page()
    await page.evaluate('window.mx=0;window.my=0;')
    return browser, ctx, page, vp

async def handle_unlock(page):
    body = await page.evaluate('document.body?.innerText?.substring(0,200)') or ''
    if 'Access Denied' in body or 'Automated access' in body:
        print('  [!] Blocked by Cloudflare'); return None
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
    # Write gate HTML
    write_gate()

    async with async_playwright() as p:
        browser, ctx, page, vp = await make_ctx(p)
        print(f'[+] Viewport: {vp["width"]}x{vp["height"]}')

        print('\n--- linkpays.in ---')
        await page.goto(SHORT_LINK, wait_until='domcontentloaded', timeout=30000)
        await delay(2, 3); await scroll(page); await delay(3, 4)

        if await page.evaluate('!!document.getElementById("goBtn")'):
            await click(page, '#goBtn')
            print('[+] Click registered on linkpays.in')
        await delay(2, 3)
        print(f'  -> {page.url}')

        for hop in range(5):
            act = await handle_unlock(page)
            if not act: break
            if act['action'] == 'click':
                sel = act['sel']
                try:
                    await click(page, sel)
                except:
                    await page.evaluate(f'document.querySelector("{sel}")?.dispatchEvent(new MouseEvent("click",{{bubbles:true}}))')
                await delay(2, 4)
                print(f'  -> {page.url}')

        print('\n--- Gate ---')
        await page.goto(f'file://{GATE_HTML}', wait_until='domcontentloaded')
        await page.screenshot(path=os.path.join(os.path.dirname(GATE_HTML) or '.', 'final.png'))
        print(f'[+] Gate ready: file://{GATE_HTML}')
        print('    Type "OPEN" → click button → destination')

        await page.wait_for_timeout(3000)
        await ctx.close()
        await browser.close()

def write_gate():
    pathlib.Path(GATE_HTML).write_text(f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Unlock Destination</title><style>
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
