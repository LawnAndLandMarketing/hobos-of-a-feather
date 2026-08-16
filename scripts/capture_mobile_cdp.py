import asyncio
import base64
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path

import websockets

ROOT = Path(__file__).resolve().parents[1]
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PORT = 9339
TARGET_URL = os.environ.get("TARGET_URL", "http://127.0.0.1:4175/?qa=cdp-mobile")


def get_ws_url():
    with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json", timeout=2) as r:
        pages = json.load(r)
    page = next((p for p in pages if p.get("type") == "page"), None)
    return page["webSocketDebuggerUrl"]


async def run():
    seq = 0
    async with websockets.connect(get_ws_url(), max_size=20_000_000) as ws:
        async def call(method, params=None):
            nonlocal seq
            seq += 1
            await ws.send(json.dumps({"id": seq, "method": method, "params": params or {}}))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get("id") == seq:
                    if "error" in msg:
                        raise RuntimeError(msg["error"])
                    return msg.get("result", {})

        await call("Page.enable")
        await call("Runtime.enable")
        await call("Emulation.setDeviceMetricsOverride", {
            "width": 390,
            "height": 844,
            "deviceScaleFactor": 1,
            "mobile": True,
            "screenWidth": 390,
            "screenHeight": 844,
        })
        await call("Emulation.setTouchEmulationEnabled", {"enabled": True, "maxTouchPoints": 5})
        await call("Page.navigate", {"url": TARGET_URL})
        await asyncio.sleep(2)
        metrics = await call("Runtime.evaluate", {"expression": "JSON.stringify({innerWidth,innerHeight,scrollWidth:document.documentElement.scrollWidth,scrollHeight:document.documentElement.scrollHeight,bodyWidth:document.body.getBoundingClientRect().width})", "returnByValue": True})
        print(metrics["result"]["value"])
        shot = await call("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": True, "fromSurface": True})
        (ROOT / "qa-mobile-cdp-full.png").write_bytes(base64.b64decode(shot["data"]))
        shot_top = await call("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": False, "fromSurface": True})
        (ROOT / "qa-mobile-cdp-top.png").write_bytes(base64.b64decode(shot_top["data"]))


proc = subprocess.Popen([
    CHROME,
    "--headless=new",
    "--disable-gpu",
    "--hide-scrollbars",
    "--no-first-run",
    "--disable-background-networking",
    f"--remote-debugging-port={PORT}",
    "--user-data-dir=/tmp/hof-cdp-mobile",
    "about:blank",
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    for _ in range(80):
        try:
            get_ws_url()
            break
        except Exception:
            time.sleep(.25)
    else:
        raise SystemExit("Chrome CDP did not start")
    asyncio.run(run())
finally:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
