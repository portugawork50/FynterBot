import telebot
from telebot import types
import sqlite3
import requests
import time
import os

# --- CONFIGURAÇÕES VIA AMBIENTE (Railway) ---
TOKEN = os.getenv('BOT_TOKEN', '8338751670:AAEe17MTCw2uEBCGz2S68eXkdlpHLgf1Gho')
ADMIN_ID = int(os.getenv('ADMIN_ID', 8647771753))
API_5SIM = os.getenv('API_5SIM') # Ele vai pegar das 'Variables' do Railway

bot = telebot.TeleBot(TOKEN)

# --- TABELA DE PREÇOS (Você paga centavos e vende por estes valores) ---
SERVICOS = {
    "whatsapp": {"nome": "WhatsApp", "preco": 1.50},
    "telegram": {"nome": "Telegram", "preco": 1.20},
    "instagram": {"nome": "Instagram", "preco": 0.80},
    "google": {"nome": "Google/Gmail", "preco": 1.00}
}

PAISES = {
    "brazil": "🇧🇷 Brasil",
    "portugal": "🇵🇹 Portugal",
    "usa": "🇺🇸 EUA"
}

# --- BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('bot_database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0)')
    conn.commit()
    conn.close()

def update_balance(user_id, amount):
    conn = sqlite3.connect('bot_database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (id, balance) VALUES (?, 0.0)", (user_id,))
    cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def get_balance(user_id):
    conn = sqlite3.connect('bot_database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0.0

# --- LÓGICA DE COMPRA ---
@bot.message_handler(func=lambda message: message.text == "📱 GERAR NÚMERO")
def menu_paises(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for cod, nome in PAISES.items():
        markup.add(types.InlineKeyboardButton(nome, callback_data=f"p_{cod}"))
    bot.send_message(message.chat.id, "🌍 *Escolha o país:*", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('p_'))
def menu_serv(call):
    pais = call.data.split('_')[1]
    markup = types.InlineKeyboardMarkup(row_width=1)
    for s_cod, info in SERVICOS.items():
        markup.add(types.InlineKeyboardButton(f"{info['nome']} - {info['preco']:.2f}€", callback_data=f"buy_{pais}_{s_cod}"))
    bot.edit_message_text(f"📍 País: {pais.upper()}\n🚀 Escolha o serviço:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def comprar(call):
    _, pais, serv = call.data.split('_')
    user_id = call.from_user.id
    custo = SERVICOS[serv]['preco']

    if get_balance(user_id) < custo:
        bot.answer_callback_query(call.id, "❌ Saldo insuficiente!", show_alert=True)
        return

    bot.edit_message_text("⏳ *Solicitando número...*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    headers = {'Authorization': f'Bearer {API_5SIM}', 'Accept': 'application/json'}
    url = f"https://5sim.net/v1/user/buy/activation/{pais}/any/{serv}"

    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            data = res.json()
            update_balance(user_id, -custo)
            bot.send_message(call.message.chat.id, f"✅ *NÚMERO:* `{data['phone']}`\n🆔 ID: `{data['id']}`\n\nAguarde o SMS chegar...")
            
            # Checagem de SMS
            for _ in range(20):
                time.sleep(10)
                chk = requests.get(f"https://5sim.net/v1/user/check/{data['id']}", headers=headers).json()
                if chk.get('sms'):
                    bot.send_message(call.message.chat.id, f"📩 *CÓDIGO:* `{chk['sms'][0]['code']}`")
                    return
            bot.send_message(call.message.chat.id, "⚠️ Tempo esgotado. SMS não recebido.")
        else:
            bot.send_message(call.message.chat.id, "❌ Sem estoque agora.")
    except:
        bot.send_message(call.message.chat.id, "❌ Erro de conexão.")

# --- COMANDOS FIXOS ---
@bot.message_handler(commands=['start'])
def start(message):
    init_db()
    update_balance(message.from_user.id, 0)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📱 GERAR NÚMERO", "💳 RECARREGAR", "👤 MINHA CONTA")
    bot.send_message(message.chat.id, "🤖 *FynterBot Ativo!*", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "👤 MINHA CONTA")
def conta(message):
    saldo = get_balance(message.from_user.id)
    bot.send_message(message.chat.id, f"🆔 ID: `{message.from_user.id}`\n💰 Saldo: {saldo:.2f} €", parse_mode="Markdown")

@bot.message_handler(commands=['add'])
def add_admin(message):
    if message.from_user.id == ADMIN_ID:
        p = message.text.split()
        update_balance(int(p[1]), float(p[2]))
        bot.reply_to(message, "✅ Saldo adicionado!")

if __name__ == "__main__":
    init_db()
    bot.infinity_polling()
