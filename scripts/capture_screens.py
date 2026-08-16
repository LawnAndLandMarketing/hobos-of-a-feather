from pathlib import Path
import subprocess
import time

chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
root = Path(__file__).resolve().parents[1]
shots = [
    ("qa-mobile-top.png", "390,844", "/tmp/hof-chrome-mobile-top-2", "mobile-top-2"),
    ("qa-mobile-full.png", "390,6000", "/tmp/hof-chrome-mobile-full-2", "mobile-full-2"),
]
for filename, size, profile, q in shots:
    destination = root / filename
    destination.unlink(missing_ok=True)
    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--no-first-run",
        "--disable-background-networking",
        "--force-device-scale-factor=1",
        f"--user-data-dir={profile}",
        f"--window-size={size}",
        f"--screenshot={destination}",
        f"http://127.0.0.1:4175/?qa={q}",
    ]
    process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.time() + 30
    while time.time() < deadline:
        if destination.exists() and destination.stat().st_size > 1000:
            break
        time.sleep(.25)
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
    if not destination.exists():
        raise SystemExit(f"screenshot failed: {destination}")
    print(destination, destination.stat().st_size)
