from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import os
import time

# Load environment variables
load_dotenv()
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

def log(msg):
    print(msg, flush=True)

# --- Setup Chrome ---
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=chrome_options)

def click_attendance(action):
    wait = WebDriverWait(driver, 20)
    xpath = f"//button[contains(@ng-click,'{action}')]"

    # Wait for button to appear
    button = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))

    # Wait until button is enabled
    for _ in range(20):
        if button.is_enabled():
            break
        time.sleep(1)
    else:
        raise Exception(f"{action} button did not become clickable in time")

    # Scroll and click button
    driver.execute_script("arguments[0].scrollIntoView(true);", button)
    time.sleep(0.5)
    driver.execute_script("arguments[0].click();", button)
    log(f"🎉 {action} clicked, waiting for popup...")

    # Wait for popup "Yes" button and click it
    try:
        yes_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(),'Yes')]")
        ))
        driver.execute_script("arguments[0].click();", yes_btn)
        log("✅ 'Yes' clicked in popup!")
    except:
        log("ℹ️ No confirmation popup appeared.")

    # Optional: wait until the main button is disabled (action reflected)
    WebDriverWait(driver, 15).until(lambda d: not button.is_enabled())
    log(f"✅ {action} reflected on dashboard.")

try:
    log("🚀 Script started.")
    driver.get("https://addoai.resourceinn.com/#/core/login")
    wait = WebDriverWait(driver, 20)

    log("⏳ Starting login...")
    username_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
    password_field = driver.find_element(By.ID, "password")
    username_field.send_keys(USERNAME)
    password_field.send_keys(PASSWORD)

    login_btn = driver.find_element(By.XPATH, "//button[contains(text(),'Login')]")
    login_btn.click()
    log("✅ Login submitted.")

    # MFA handling
    try:
        wait.until(EC.presence_of_element_located((By.ID, "otp-input")))
        log("🔐 Two-Step Auth detected! Enter OTP manually...")
        time.sleep(30)
    except:
        log("ℹ️ No MFA, continuing...")

    # Load attendance page
    ATTENDANCE_URL = "https://addoai.resourceinn.com/#/app/dashboard"
    driver.get(ATTENDANCE_URL)
    wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(@ng-click,'punchAttendance')]")))
    log("✅ Attendance page loaded.")

    # Click Check-In or Check-Out
    try:
        click_attendance("markCheckin")
    except Exception:
        click_attendance("markCheckout")

finally:
    log("🏁 Script ended.")
    driver.quit()
