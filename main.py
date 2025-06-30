import hashlib
import json
import os
import time
from flask import Flask, request
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

app = Flask(__name__)

# ====== КОНФІГУРАЦІЯ ======
TELEGRAM_TOKEN = '7971113554:AAEHlyaoqnKDT7pLSCKjpKi4pYDfrwy7S7E'
WFP_MERCHANT = 'forms_gle7'  # твій Merchant Login
WFP_SECRET = '7921e3bad21153d0e467066b5285511d390a16d4'  # твій секретний ключ
WFP_URL = 'https://secure.wayforpay.com/pay'

BOT = telegram.Bot(token=TELEGRAM_TOKEN)

DROPBOX_LINKS = {
    'issue1': 'https://www.dropbox.com/scl/fi/qm5hiudd87tpyljw89v83/1-27.01.pdf?rlkey=ij38rwju1owjrhm9ngnbe4em6&st=iwqjtkf5&dl=0',
    'issue2': 'https://www.dropbox.com/scl/fi/nq957bo5ukp7axg1e9y5q/2-28.02.pdf?rlkey=1hfnpx1dqje36j3b66hjpfppc&st=6xwrs52a&dl=0',
    'issue3': 'https://www.dropbox.com/scl/fi/hpg0gf9lh207hiw1uw50x/3-09.04.pdf?rlkey=d6s3iiup02aye3xul8898lg3c&st=ovah6jzc&dl=0'
}

# ====== СТВОРЕННЯ ПІДПИСУ ======
def generate_signature(data: dict, secret: str) -> str:
    keys = sorted(data.keys())
    values = [str(data[key]) for key in keys]
    signature_str = ';'.join(values)
    return hashlib.sha1((signature_str + secret).encode()).hexdigest()

# ====== ГЕНЕРАЦІЯ ПОСИЛАННЯ НА ОПЛАТУ ======
def create_payment_link(chat_id: int, issue_id: str) -> str:
    order_ref = f'pnzbz_{issue_id}_{chat_id}'
    data = {
        "merchantAccount": WFP_MERCHANT,
        "merchantDomainName": "pniabzyk.onrender.com",
        "orderReference": order_ref,
        "orderDate": int(time.time()),
        "amount": 50,
        "currency": "UAH",
        "productName": [f"Пнябзик №{issue_id[-1]} (PDF)"],
        "productCount": [1],
        "productPrice": [50],
        "clientEmail": f"user{chat_id}@fake.bot",
        "serviceUrl": "https://pniabzyk.onrender.com/webhook"
    }

    data["merchantSignature"] = generate_signature(data, WFP_SECRET)
    json_data = json.dumps(data)
    return f"https://secure.wayforpay.com/pay?data={json_data}"

# ====== ВІДПРАВКА КНОПКИ ======
def send_payment_button(chat_id: int, issue: str):
    url = create_payment_link(chat_id, issue)
    BOT.send_message(
        chat_id,
        f"Оплатіть Пнябзик №{issue[-1]}:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Оплатити 50 грн", url=url)]
        ])
    )

# ====== ОБРОБКА /start ======
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
            "Привіт! Оберіть випуск:",
            reply_markup=telegram.ReplyKeyboardMarkup([
                ["📘 Пнябзик №1", "📘 Пнябзик №2", "📘 Пнябзик №3"]
            ], one_time_keyboard=True)
        )
    elif text == "📘 Пнябзик №1":
        send_payment_button(chat_id, "issue1")
    elif text == "📘 Пнябзик №2":
        send_payment_button(chat_id, "issue2")
    elif text == "📘 Пнябзик №3":
        send_payment_button(chat_id, "issue3")

    return 'ok'

# ====== WEBHOOK WAYFORPAY ======
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json(force=True)
    if not data or data.get("transactionStatus") != "Approved":
        return 'Ignored'

    order_ref = data.get("orderReference")
    if not order_ref or not order_ref.startswith("pnzbz_"):
        return 'Invalid'

    parts = order_ref.split("_")
    if len(parts) != 3:
        return 'Invalid'

    issue_id, chat_id = parts[1], parts[2]
    dropbox_link = DROPBOX_LINKS.get(issue_id)
    if dropbox_link:
        try:
            BOT.send_message(chat_id=int(chat_id), text=f"✅ Дякуємо за оплату!\nОсь ваше посилання: {dropbox_link}")
        except Exception as e:
            print("Send error:", e)

    return 'OK'

# ====== СТАРТ СЕРВЕРА ======
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
