import hashlib
import json
import requests
from flask import Flask, request
import telegram
import os

app = Flask(__name__)

# Конфігурація (вставлено напряму)
TELEGRAM_TOKEN = 7971113554:AAEHlyaoqnKDT7pLSCKjpKi4pYDfrwy7S7E
WFP_MERCHANT = 'forms_gle7'
WFP_SECRET = '7921e3bad21153d0e467066b5285511d390a16d4'
WFP_URL = 'https://secure.wayforpay.com/pay'
BOT = telegram.Bot(token=TELEGRAM_TOKEN)

# Випуски й посилання
DROPBOX_LINKS = {
    'issue1': 'https://www.dropbox.com/scl/fi/qm5hiudd87tpyljw89v83/1-27.01.pdf?rlkey=ij38rwju1owjrhm9ngnbe4em6&st=iw7rfoua&dl=0',
    'issue2': 'https://www.dropbox.com/scl/fi/nq957bo5ukp7axg1e9y5q/2-28.02.pdf?rlkey=1hfnpx1dqje36j3b66hjpfppc&st=vos3iv46&dl=0',
    'issue3': 'https://www.dropbox.com/scl/fi/hpg0gf9lh207hiw1uw50x/3-09.04.pdf?rlkey=d6s3iiup02aye3xul8898lg3c&st=ute9v9tz&dl=0'
}

# Генерація підпису для Wayforpay
def generate_signature(data, secret):
    keys = sorted(data)
    signature_str = ';'.join([str(data[k]) for k in keys])
    return hashlib.sha1((signature_str + secret).encode('utf-8')).hexdigest()

# Генерація посилання на оплату
def create_invoice(chat_id, issue_id):
    order_ref = f"pnzbz_{issue_id}_{chat_id}"
    invoice = {
        "orderReference": order_ref,
        "merchantAccount": WFP_MERCHANT,
        "orderDate": int(requests.get('https://showcase.api.linx.twenty57.net/UnixTime/tounixtimestamp?date=now').json()),
        "amount": "50",
        "currency": "UAH",
        "productName": [f"Пнябзик №{issue_id[-1]} (PDF)"],
        "productCount": [1],
        "productPrice": [50],
        "clientFirstName": "User",
        "clientLastName": "Telegram",
        "clientEmail": f"user{chat_id}@bot.fake",
        "returnUrl": "https://example.com/thankyou",
        "serviceUrl": "https://YOUR_RENDER_URL/webhook"
    }
    invoice["merchantSignature"] = generate_signature(invoice, WFP_SECRET)
    pay_url = WFP_URL + "?" + '&'.join([f"{k}={json.dumps(v) if isinstance(v, list) else v}" for k, v in invoice.items()])
    return pay_url

# Telegram webhook
@app.route('/telegram', methods=['POST'])
def telegram_webhook():
    update = telegram.Update.de_json(request.get_json(force=True), BOT)
    chat_id = update.message.chat_id
    message = update.message.text

    if message == '/start':
        BOT.send_message(chat_id, "Привіт! Оберіть випуск, який хочете купити:", reply_markup=telegram.ReplyKeyboardMarkup(
            [["📘 Пнябзик №1", "📘 Пнябзик №2", "📘 Пнябзик №3"]], one_time_keyboard=True))

    elif message == '📘 Пнябзик №1':
        link = create_invoice(chat_id, 'issue1')
        BOT.send_message(chat_id, f"Оплатіть випуск №1 за посиланням:\n{link}")
    elif message == '📘 Пнябзик №2':
        link = create_invoice(chat_id, 'issue2')
        BOT.send_message(chat_id, f"Оплатіть випуск №2 за посиланням:\n{link}")
    elif message == '📘 Пнябзик №3':
        link = create_invoice(chat_id, 'issue3')
        BOT.send_message(chat_id, f"Оплатіть випуск №3 за посиланням:\n{link}")

    return 'ok'

# Wayforpay webhook
@app.route('/webhook', methods=['POST'])
def wfp_webhook():
    data = request.get_json()
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

@app.route('/', methods=['GET'])
def index():
    return 'PniabzykBot is running.'

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
