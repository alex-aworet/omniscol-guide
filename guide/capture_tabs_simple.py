from pathlib import Path
import os
import re
import json
from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Load .env file
env_file = PROJECT_ROOT / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())

# Configuration
BASE_URL = os.getenv("OMNISCOL_BASE_URL", "https://sandboxai.omniscol.com")
USERNAME = os.getenv("OMNISCOL_USERNAME", "")
PASSWORD = os.getenv("OMNISCOL_PASSWORD", "")
AUTHTOKEN = os.getenv("OMNISCOL_AUTHTOKEN", "")
AUTHTOKEN_PEPPER = os.getenv("OMNISCOL_AUTHTOKEN_PEPPER", "")
OUT_DIR = PROJECT_ROOT / "guide/screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Routes to capture
ROUTES = [
    "/", "login",
    "dashboard", "dashboard/teachers", "dashboard/classrooms", 
    "dashboard/resources", "dashboard/subjects", "dashboard/classes", "dashboard/students",
    "schedules", "schedules/view", "schedules/reorganization",
    "schedule", "schedule/view", "schedule/reorganization",
    "absences", "absences/students", "absences/teachers", "absences/staff", "absences/classes",
    "admin", "admin/users", "admin/users/teachers", "admin/schoolyears",
    "timetables", "timetables/default", "timetables/default/general", "timetables/default/preview",
]

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # Add cookies if available
        if AUTHTOKEN or AUTHTOKEN_PEPPER:
            cookies = []
            if AUTHTOKEN:
                cookies.append({"name": "authtoken", "value": AUTHTOKEN, "url": BASE_URL})
            if AUTHTOKEN_PEPPER:
                cookies.append({"name": "authtoken_pepper", "value": AUTHTOKEN_PEPPER, "url": BASE_URL})
            context.add_cookies(cookies)
            print(f"✓ Applied {len(cookies)} cookies")

        # Try login
        page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=20000)
        try:
            page.locator('//*[@id="login-login"]').fill(USERNAME)
            page.locator('//*[@id="login-password"]').fill(PASSWORD)
            page.locator('//*[@id="login-form"]/div[3]/button').click()
            page.wait_for_load_state("networkidle", timeout=15000)
            print("✓ Login successful")
        except Exception as e:
            print(f"⚠ Login failed: {e}")

        # Capture screenshots
        print(f"\nCapturing {len(ROUTES)} pages:")
        for route in ROUTES:
            url = f"{BASE_URL}/{route}".replace("//", "/").replace(":443/", ":443")
            try:
                page.goto(url, wait_until="networkidle", timeout=15000)
                name = route.replace("/", "_") or "home"
                page.screenshot(path=str(OUT_DIR / f"{name}.png"), full_page=True)
                print(f"  ✓ {route}")
            except Exception as e:
                print(f"  ✗ {route}: {e}")

        # Save URL list
        urls_list = [{"name": r.replace("/", "_") or "home", "route": f"/{r}", "url": f"{BASE_URL}/{r}"} for r in ROUTES]
        (OUT_DIR / "captured_urls.json").write_text(json.dumps({"total": len(urls_list), "pages": urls_list}, indent=2))
        print(f"\n✓ Saved {len(urls_list)} URLs to captured_urls.json")

        browser.close()

if __name__ == "__main__":
    main()
