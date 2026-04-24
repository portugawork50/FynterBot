import telebot
from telebot import types
import sqlite3
import requests
import time
import os

# --- CONFIGURAÇÕES ---
TOKEN = '8338751670:AAEe17MTCw2uEBCGz2S68eXkdlpHLgf1Gho'
ADMIN_ID = 8647771753
API_5SIM = 'eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE4MDg1NjM2MDIsImlhdCI6MTc3NzAyNzYwMiwicmF5IjoiN2EyZTM1ZTA2NjJjNTUzM2QzYmI3M2ZhMzgzNWRiNTgiLCJzdWIiOjQwMDA4MjJ9.AFEiVz5FmQ9RU_x_GvO-hFGu9ThDWm-Co5yT1DjKruXLRrgxtpGsBOUJA-FvEUUDD08pkZ9DU0YBNMZQ1r89FYZDufXA7U5OoDbddzg-CbYVbh3sJaMAeKSaWTvlAIkf1b8Fx3eQMmmNC2GDrVHYT8Dr8LQU2m7kJAcoppnvkx-ZZ4sT1t8mJiUc6TD1Mb2rFGNzcRIGDI5-icO3kzKAMqfDmXBmS4N3_pZ5wCTNYZmvKkISwbI_hWJptPpi8WwEY0nL4wIJclSXMSpsgZDpei9D5jD_czf9Hf_DHqXAPJo5s7_dcD6UCBrJ-P74F7IspnPTh4nGhTlJgg89o8LNRQ'.strip()

bot = telebot.TeleBot(TOKEN)
DB_PATH = 'bot_database.db'

def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0)')
    conn.commit()
    conn.close()

def update_balance(user_id, amount):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (id, balance) VALUES (?, 0.0)", (user_id,))
    cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def get_balance(user_id):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0.0

@bot.message_handler(commands=['start'])
def welcome(message):
    init_db()
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("📱 GERAR NÚMERO", "💳 RECARREGAR", "👤 MINHA CONTA", "🆘 SUPORTE")
    bot.send_message(message.chat.id, "🌟 *BEM-VINDO AO FYNTERBOT!* 🌟\n\nEscolha uma opção no menu:", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📱 GERAR NÚMERO")
def escolher_pais(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🇧🇷 Brasil", callback_data="p_brazil"),
        types.InlineKeyboardButton("🇵🇹 Portugal", callback_data="p_portugal"),
        types.InlineKeyboardButton("🇬🇧 Inglaterra", callback_data="p_england"),
        types.InlineKeyboardButton("🇺🇸 EUA", callback_data="p_usa")
    )
    bot.send_message(message.chat.id, "🌍 *SELECIONE O PAÍS:*", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("p_"))
def escolher_servico(call):
    pais = call.data.split("_")[1]
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("💬 WhatsApp - 1.50€", callback_data=f"buy_{pais}_whatsapp"),
        types.InlineKeyboardButton("✈️ Telegram - 1.20€", callback_data=f"buy_{pais}_telegram")
    )
    bot.edit_message_text(f"📍 País: *{pais.upper()}*\n🚀 Escolha o serviço:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def processar_compra(call):
    _, pais, serv = call.data.split("_")
    user_id = call.from_user.id
    custo = 1.50 if serv == "whatsapp" else 1.20

    if get_balance(user_id) < custo:
        bot.answer_callback_query(call.id, "❌ Saldo insuficiente!", show_alert=True)
        return

    bot.edit_message_text(f"⏳ *Buscando número {pais.upper()}...*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    
    headers = {'Authorization': f'Bearer {API_5SIM}', 'Accept': 'application/json'}
    url = f"https://5sim.net/v1/user/buy/activation/{pais}/any/{serv}"
    
    try:
        r = requests.get(url, headers=headers, timeout=60)
        if r.status_code == 200:
            res = r.json()
            update_balance(user_id, -custo)
            bot.send_message(call.message.chat.id, f"✅ *NÚMERO:* `{res['phone']}`\n🆔 ID: `{res['id']}`\nAguardando SMS...")
            
            for _ in range(30):
                time.sleep(10)
                c = requests.get(f"https://5sim.net/v1/user/check/{res['id']}", headers=headers).json()
                if c.get('sms'):
                    bot.send_message(call.message.chat.id, f"📩 *CÓDIGO {pais.upper()}:* `{c['sms'][0]['code']}`")
                    return
            bot.send_message(call.message.chat.id, "⚠️ SMS demorou. Tente novamente.")
        else:
            erro = r.json().get('errors', ['Sem stock'])[0]
            bot.send_message(call.message.chat.id, f"❌ *FORNECEDOR:* {erro}")
    except Exception as e:
        bot.send_message(call.message.chat.id, "⚠️ Erro de conexão. Tente de novo.")

@bot.message_handler(func=lambda m: m.text == "👤 MINHA CONTA")
def conta(message):
    saldo = get_balance(message.from_user.id)
    bot.send_message(message.chat.id, f"👤 ID: `{message.from_user.id}`\n💰 Saldo: `{saldo:.2f} €`", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "💳 RECARREGAR")
def recarga(message):
    texto = f"💳 *RECARGA*\n\n🔵 MB WAY: @portugam50\n🟢 USDT: `TWxHqzW9MBAymeBnqx3WX6VyNUPKMmhoXU`\n\n🆔 Seu ID: `{message.from_user.id}`"
    bot.send_message(message.chat.id, texto, parse_mode="Markdown")

@bot.message_handler(commands=['add'])
def add_saldo(message):
    if message.from_user.id == ADMIN_ID:
        try:
            p = message.text.split()
            update_balance(int(p[1]), float(p[2]))
            bot.reply_to(message, "✅ Saldo creditado!")
        except:
            bot.reply_to(message, "Use: /add ID VALOR")

if __name__ == "__main__":
    init_db()
    bot.infinity_polling()
