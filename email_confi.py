from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import os
import time

# Email Libraries
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.mime.text import MIMEText

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

# ---------------------------------------------------------
# SEND EMAIL WITH SCREENSHOT
# ---------------------------------------------------------
def send_email_with_screenshot(file_path):
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    receiver = os.getenv("EMAIL_RECEIVER")

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = "Attendance Marked Successfully ✔"

    msg.attach(MIMEText("Your attendance was marked successfully. Screenshot attached.", "plain"))

    # Attach Screenshot
    with open(file_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())

    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f"attachment; filename=attendance_success.png")
    msg.attach(part)

    # Send email using Gmail SMTP
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender, password)
    server.send_message(msg)
    server.quit()

    log("📧 Email sent successfully!")

# ---------------------------------------------------------
# CLICK ATTENDANCE BUTTON + TAKE SCREENSHOT
# ---------------------------------------------------------
def click_attendance(action):
    wait = WebDriverWait(driver, 20)
    xpath = f"//button[contains(@ng-click,'{action}')]"

    button = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))

    # Wait for the button to become enabled
    for _ in range(20):
        if button.is_enabled():
            break
        time.sleep(1)
    else:
        raise Exception(f"{action} button did not become clickable in time")

    driver.execute_script("arguments[0].scrollIntoView(true);", button)
    time.sleep(0.5)
    driver.execute_script("arguments[0].click();", button)
    log(f"🎉 {action} clicked, waiting for popup...")

    # Handle Popup "Yes"
    try:
        yes_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Yes')]")))
        driver.execute_script("arguments[0].click();", yes_btn)
        log("✅ 'Yes' clicked in popup!")
    except:
        log("ℹ️ No confirmation popup appeared.")

    # Wait until action reflects
    WebDriverWait(driver, 15).until(lambda d: not button.is_enabled())
    log(f"✅ {action} reflected on dashboard.")

    # --- TAKE SCREENSHOT ---
    screenshot_path = "attendance_success.png"
    driver.save_screenshot(screenshot_path)
    log("📸 Screenshot captured!")

    return screenshot_path

# ---------------------------------------------------------
# MAIN SCRIPT EXECUTION
# ---------------------------------------------------------
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

    # MFA Handling
    try:
        wait.until(EC.presence_of_element_located((By.ID, "otp-input")))
        log("🔐 Two-Step Auth detected! Enter OTP manually...")
        time.sleep(30)
    except:
        log("ℹ️ No MFA, continuing...")

    # Load Attendance Page
    ATTENDANCE_URL = "https://addoai.resourceinn.com/#/app/dashboard"
    driver.get(ATTENDANCE_URL)

    wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(@ng-click,'punchAttendance')]")))
    log("✅ Attendance page loaded.")

    # Try Check-in → If fails, Check-out
    try:
        screenshot = click_attendance("markCheckin")
    except Exception:
        screenshot = click_attendance("markCheckout")

    # Send Email
    send_email_with_screenshot(screenshot)

finally:
    log("🏁 Script ended.")
    driver.quit()
