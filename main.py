import hashlib
import json
import requests
import time
from flask import Flask, request
import telegram
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
import os
from urllib.parse import urlencode

# === Конфігурація ===
TELEGRAM_TOKEN = '7971113554:AAEHlyaoqnKDT7pLSCKjpKi4pYDfrwy7S7E'
WFP_MERCHANT = 'forms_gle7'
WFP_SECRET = '7921e3bad21153d0e467066b5285511d390a16d4'
WFP_URL = 'https://secure.wayforpay.com/pay'
BASE_URL = 'https://pniabzyk.onrender.com'  # ваш render URL

BOT = telegram.Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)

# === Dropbox-посилання ===
DROPBOX_LINKS = {
    'issue1': 'https://www.dropbox.com/scl/fi/qm5hiudd87tpyljw89v83/1-27.01.pdf?rlkey=ij38rwju1owjrhm9ngnbe4em6&st=iw7rfoua&dl=0',
    'issue2': 'https://www.dropbox.com/scl/fi/nq957bo5ukp7axg1e9y5q/2-28.02.pdf?rlkey=1hfnpx1dqje36j3b66hjpfppc&st=vos3iv46&dl=0',
    'issue3': 'https://www.dropbox.com/scl/fi/hpg0gf9lh207hiw1uw50x/3-09.04.pdf?rlkey=d6s3iiup02aye3xul8898lg3c&st=ute9v9tz&dl=0'
}

# === Підпис ===
def generate_signature(data: dict, secret: str):
    keys = sorted(data)
    signature_str = ';'.join(str(data[k]) for k in keys)
    return hashlib.sha1((signature_str + secret).encode('utf-8')).hexdigest()

# === Генерація платіжного посилання ===
def create_payment_link(chat_id: int, issue_id: str):
    order_ref = f"pnzbz_{issue_id}_{chat_id}"
    data = {
        "orderReference": order_ref,
        "merchantAccount": WFP_MERCHANT,
        "orderDate": int(time.time()),
        "amount": "50",
        "currency": "UAH",
        "productName": [f"Пнябзик №{issue_id[-1]} (PDF)"],
        "productCount": [1],
        "productPrice": [50],
        "clientEmail": f"user{chat_id}@bot.fake",
        "serviceUrl": f"{BASE_URL}/webhook",
        "returnUrl": BASE_URL
    }
    data["merchantSignature"] = generate_signature(data, WFP_SECRET)
    return f"{WFP_URL}?{urlencode(data, doseq=True)}"

# === Надсилання кнопки

def send_payment_button(chat_id, issue_id):
    url = create_payment_link(chat_id, issue_id)
    BOT.send_message(
        chat_id,
        f"Оплатіть випуск №{issue_id[-1]}:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("💳 Оплатити 50 грн", url=url)
        ]])
    )

# === Telegram Webhook ===
@app.route('/telegram', methods=['POST'])
def telegram_webhook():
    update = telegram.Update.de_json(request.get_json(force=True), BOT)
    if not update.message or not update.message.text:
        return 'ok'
    chat_id = update.message.chat_id
    text = update.message.text.strip()

    if text == '/start':
        BOT.send_message(
            chat_id,
            "Привіт! Оберіть випуск, який хочете купити:",
            reply_markup=telegram.ReplyKeyboardMarkup([
                ['📘 Пнябзик №1', '📘 Пнябзик №2', '📘 Пнябзик №3']
            ], one_time_keyboard=True)
        )
    elif text == '📘 Пнябзик №1':
        send_payment_button(chat_id, 'issue1')
    elif text == '📘 Пнябзик №2':
        send_payment_button(chat_id, 'issue2')
    elif text == '📘 Пнябзик №3':
        send_payment_button(chat_id, 'issue3')

    return 'ok'

# === Wayforpay Webhook ===
@app.route('/webhook', methods=['POST'])
def wfp_webhook():
    data = request.get_json(force=True)
    if data.get('transactionStatus') == 'Approved':
        ref = data.get('orderReference')
        parts = ref.split('_')
        if len(parts) == 3 and parts[0] == 'pnzbz':
            issue = parts[1]
            chat_id = int(parts[2])
            link = DROPBOX_LINKS.get(issue)
            if link:
                BOT.send_message(chat_id, f"Дякуємо за оплату! Ось ваше посилання:\n{link}")
    return 'OK'

# === Запуск сервера ===
@app.route('/', methods=['GET'])
def index():
    return 'Бот працює.'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
