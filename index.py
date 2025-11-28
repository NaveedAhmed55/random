import os
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

USERNAME = os.environ.get("USERNAME")
PASSWORD = os.environ.get("PASSWORD")
ACTION = os.environ.get("ACTION", "markCheckin")
MAX_RANDOM_DELAY = int(os.environ.get("MAX_RANDOM_DELAY", "1800"))
HEADLESS = os.environ.get("HEADLESS", "true").lower() in ("1", "true", "yes")

LOGIN_URL = "https://addoai.resourceinn.com/#/core/login"
ATTENDANCE_URL = "https://addoai.resourceinn.com/#/app/dashboard"

def log(msg):
    print(msg, flush=True)

def make_driver():
    chrome_options = Options()
    if HEADLESS:
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")

    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-infobars")

    # ⭐ MUST ADD FOR GITHUB ACTIONS
    chrome_options.binary_location = "/usr/bin/chromium-browser"

    try:
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        log(f"❌ Failed to initialize Chrome: {e}")
        raise
    return driver


def _attendance_reflected(d, xpath):
    try:
        btn = d.find_element(By.XPATH, xpath)
        return not btn.is_enabled()
    except Exception:
        return True


def click_attendance(driver, action):
    wait = WebDriverWait(driver, 20)
    xpath = f"//button[contains(@ng-click,'{action}')]"

    button = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))

    for _ in range(20):
        try:
            if button.is_enabled():
                break
        except Exception:
            try:
                button = driver.find_element(By.XPATH, xpath)
                if button.is_enabled():
                    break
            except Exception:
                pass
        time.sleep(1)
    else:
        raise Exception(f"{action} button did not become clickable in time")

    driver.execute_script("arguments[0].scrollIntoView(true);", button)
    time.sleep(0.4)
    driver.execute_script("arguments[0].click();", button)
    log(f"🎉 {action} clicked — waiting for popup...")

    try:
        yes_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Yes')]")))
        driver.execute_script("arguments[0].click();", yes_btn)
        log("✅ 'Yes' clicked in popup.")
    except Exception:
        log("ℹ️ No confirmation popup appeared.")

    try:
        WebDriverWait(driver, 15).until(lambda d: _attendance_reflected(d, xpath))
        log(f"✅ {action} reflected on dashboard.")
    except Exception:
        log(f"⚠️ Could not verify {action} reflection.")


def main():
    if not USERNAME or not PASSWORD:
        log("❌ USERNAME or PASSWORD not set.")
        raise SystemExit(1)

    if MAX_RANDOM_DELAY > 0:
        delay = random.randint(0, MAX_RANDOM_DELAY)
        log(f"⏱ Sleeping random {delay} seconds before action ({ACTION})...")
        time.sleep(delay)

    driver = make_driver()
    try:
        log("🚀 Navigating to login page...")
        driver.get(LOGIN_URL)
        wait = WebDriverWait(driver, 20)

        log("⏳ Starting login...")
        username_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
        password_field = driver.find_element(By.ID, "password")
        username_field.send_keys(USERNAME)
        password_field.send_keys(PASSWORD)

        login_btn = driver.find_element(By.XPATH, "//button[contains(text(),'Login')]")
        login_btn.click()
        log("✅ Login submitted.")

        try:
            wait.until(EC.presence_of_element_located((By.ID, "otp-input")))
            log("🔐 OTP detected! Cannot automate.")
            raise SystemExit(2)
        except:
            log("ℹ️ No OTP — continuing...")

        driver.get(ATTENDANCE_URL)
        wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(@ng-click,'punchAttendance')]")))
        log("✅ Attendance page loaded.")

        click_attendance(driver, ACTION)

    finally:
        log("🏁 Done — quitting driver.")
        driver.quit()


if __name__ == "__main__":
    main()
