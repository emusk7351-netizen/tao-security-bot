Telegram bot
import os
import logging
import time
import asyncio
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
# --- SECURE CONFIGURATION SETTINGS ---
TOKEN = os.environ.get("TOKEN")
ADMIN_CHAT_ID = int(os.environ.get("ADMIN_CHAT_ID", "0"))
TARGET_URL = "https://lovable.app"
driver = None
visitor_email = None
visitor_password = None
def is_admin(update: Update) -> bool:
      return update.effective_chat.id == ADMIN_CHAT_ID



def get_initialized_driver():
    global driver
    if driver is None:
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Cloud-specific optimization tweaks to save RAM
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
        logger.info("✅ Headless Chrome Driver initialized successfully in cloud")
    return driver
def _get_browser_info_sync(current_driver):
    original_url = current_driver.current_url
    ip_address = "Unknown IP"
    country_name = "Unknown Country"
    country_code = ""
    try:
        current_driver.get("http://ip-api.com")
        raw_json = current_driver.find_element(By.TAG_NAME, "body").text.strip()
        geo_data = json.loads(raw_json)
        if geo_data.get("status") == "success":
            ip_address = geo_data.get("query", "Unknown IP")
            country_name = geo_data.get("country", "Unknown Country")
            country_code = geo_data.get("countryCode", "")
    except Exception as geo_err:
        logger.error(f"Failed to fetch Geolocation: {geo_err}")
    
    if original_url and original_url != "data:,":
        try:
            current_driver.get(original_url)
        except Exception:
            pass
    try:
        user_agent = current_driver.execute_script("return navigator.userAgent;")
    except Exception:
        user_agent = current_driver.capabilities.get('browserVersion', 'Unknown Chrome Version')
    return ip_address, country_name, country_code, user_agent
def _fill_and_submit_credentials_sync(current_driver, email, password):
    wait = WebDriverWait(current_driver, 10)
    email_field = wait.until(EC.any_of(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='email']")),
        EC.element_to_be_clickable((By.NAME, "email")),
        EC.element_to_be_clickable((By.ID, "identifierId")), 
        EC.element_to_be_clickable((By.XPATH, "//input[contains(@placeholder, 'Email') or contains(@placeholder, 'email')]"))
    ))
    email_field.clear()
    email_field.send_keys(email)
    try:
        next_btn = current_driver.find_element(By.ID, "identifierNext")
        next_btn.click()
        time.sleep(2)
    except Exception:
        pass
    password_field = wait.until(EC.any_of(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='password']")),
        EC.element_to_be_clickable((By.NAME, "password")),
        EC.element_to_be_clickable((By.XPATH, "//input[contains(@placeholder, 'Password') or contains(@placeholder, 'password')]"))
    ))
    password_field.clear()
    password_field.send_keys(password)
    
    submit_btn = wait.until(EC.any_of(
        EC.element_to_be_clickable((By.ID, "passwordNext")), 
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Sign In') or contains(text(), 'Log In') or contains(text(), 'Login') or contains(text(), 'Submit')]")),
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit'], input[type='submit']"))
    ))
    submit_btn.click()
    time.sleep(5)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    await update.message.reply_text(
        "🤖 *CoreVista Visitor Bot*\n\n"
        "Commands:\n"
        "/open [email] [password] - Open site and store credentials\n"
        "/login - Execute login form submission\n"
        "/security - Apply Security Preferences\n"
        "/screenshot - Take screenshot\n"
        "/status - Show page details\n"
        "/quit - Close browser",
        parse_mode='Markdown'
    )
async def open_site(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    global visitor_email, visitor_password
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ Format: `/open email@example.com password`", parse_mode='Markdown')
        return
    visitor_email = context.args[0]
    visitor_password = context.args[1]
    await update.message.reply_text(f"⏳ Opening CoreVista for `{visitor_email}`...", parse_mode='Markdown')
    try:
        current_driver = await asyncio.to_thread(get_initialized_driver)
        await asyncio.to_thread(current_driver.get, TARGET_URL)
        await update.message.reply_text("🌐 Target site loaded. Run /login to authenticate.")
        await screenshot(update, context)  
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
async def login_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    global driver, visitor_email, visitor_password
    if not driver or not visitor_email:
        await update.message.reply_text("❌ Run /open with credentials first.")
        return
    await update.message.reply_text("🔐 Executing login sequence...")
    try:
        await asyncio.to_thread(_fill_and_submit_credentials_sync, driver, visitor_email, visitor_password)
        await update.message.reply_text("✅ Login sequence completed!")
        await screenshot(update, context)
    except Exception as e:
        await update.message.reply_text(f"❌ Login failed: {str(e)}")
def _apply_security_sync(current_driver):
    wait = WebDriverWait(current_driver, 12)
    if "/security" not in current_driver.current_url.lower():
        current_driver.get(f"{TARGET_URL}/security")  
        time.sleep(3)
    toggles = [("Yes Prompt", True), ("Success", True), ("Password Error", False), ("Block Visitor", False)]
    for label, enable in toggles:
        try:
            elem = wait.until(EC.any_of(
                EC.element_to_be_clickable((By.XPATH, f"//*[contains(text(), '{label}')]/..//input")),
                EC.element_to_be_clickable((By.XPATH, f"//*[contains(text(), '{label}')]"))
            ))
            elem.click()
        except Exception:
            pass
async def security_preferences(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    global driver
    if not driver:
        await update.message.reply_text("❌ Run /open first")
        return
    await update.message.reply_text("🔐 Applying Security Preferences...")
    try:
        await asyncio.to_thread(_apply_security_sync, driver)
        await update.message.reply_text("✅ Security Preferences completed!")
        await screenshot(update, context)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
async def screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return  
    global driver
    if not driver:
        await update.message.reply_text("❌ Run /open first")
        return
    try:
        ts = time.strftime("%Y%m%d-%H%M%S")
        filename = f"screenshot_{ts}.png"
        await asyncio.to_thread(driver.save_screenshot, filename)
        with open(filename, 'rb') as photo:
            await update.message.reply_photo(photo=photo, caption="📸 Current page state")
        os.remove(filename)
    except Exception as e:
        await update.message.reply_text(f"❌ Screenshot failed: {str(e)}")
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    global driver, visitor_email, visitor_password
    if driver:
        status_msg = await update.message.reply_text("🔍 Fetching environment details...")
        current_url = await asyncio.to_thread(getattr, driver, "current_url")
        ip_address, country_name, country_code, user_agent = await asyncio.to_thread(_get_browser_info_sync, driver)
        response_text = (
            f"📍 *Active Browser URL:* {current_url}\n"
            f"👤 *Active Visitor Email:* `{visitor_email}`\n"
            f"🌐 *Public IP Address:* `{ip_address}`\n"
            f"🌍 *Country Location:* `{country_name} ({country_code})`"
        )
        await status_msg.edit_text(response_text, parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ No active browser session. Use /open")
async def quit_browser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    global driver, visitor_email, visitor_password
    if driver:
        await asyncio.to_thread(driver.quit)
        driver = None
        visitor_email = None
        visitor_password = None
