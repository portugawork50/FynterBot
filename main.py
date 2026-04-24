import telebot
from telebot import types
import sqlite3
import requests
import time
import os

# --- CONFIGURAÇÕES ---
TOKEN = '8338751670:AAEe17MTCw2uEBCGz2S68eXkdlpHLgf1Gho'
ADMIN_ID = 8647771753
API_5SIM = 'EyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE4MDg1NjM2MDIsImlhdCI6MTc3NzAyNzYwMiwicmF5IjoiN2EyZTM1ZTA2NjJjNTUzM2QzYmI3M2ZhMzgzNWRiNTgiLCJzdWIiOjQwMDA4MjJ9.AFEiVz5FmQ9RU_x_GvO-hFGu9ThDWm-Co5yT1DjKruXLRrgxtpGsBOUJA-FvEUUDD08pkZ9DU0YBNMZQ1r89FYZDufXA7U5OoDbddzg-CbYVbh3sJaMAeKSaWTvlAIkf1b8Fx3eQMmmNC2GDrVHYT8Dr8LQU2m7kJAcoppnvkx-ZZ4sT1t8mJiUc6TD1Mb2rFGNzcRIGDI5-icO3kzKAMqfDmXBmS4N3_pZ5wCTNYZmvKkISwbI_hWJptPpi8WwEY0nL4wIJclSXMSpsgZDpei9D5jD_czf9Hf_DHqXAPJo5s7_dcD6UCBrJ-P74F7IspnPTh4nGhTlJgg89o8LNRQ'.strip()

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

# --- MENUS ---
def menu_principal():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("📱 GERAR NÚMERO", "💳 RECARREGAR", "👤 MINHA CONTA", "🆘 SUPORTE")
    return markup

@bot.message_handler(commands=['start'])
def welcome(message):
    init_db()
    texto = (
        f"🌟 *BEM-VINDO AO FYNTERBOT!* 🌟\n\n"
        f"🛡️ _Ativações SMS para Brasil, Portugal e mais._\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"✅ Números Reais e Virtuais\n"
        f"👤 Suporte: @portugam50\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👇 *Escolha uma opção:* "
    )
    bot.send_message(message.chat.id, texto, reply_markup=menu_principal(), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📱 GERAR NÚMERO")
def escolher_pais(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🇧🇷 Brasil", callback_data="p_brazil"),
        types.InlineKeyboardButton("🇵🇹 Portugal", callback_data="p_portugal"),
        types.InlineKeyboardButton("🇬🇧 Inglaterra", callback_data="p_england"),
        types.InlineKeyboardButton("🇺🇸 EUA", callback_data="p_usa"),
        types.InlineKeyboardButton("🇫🇷 França", callback_data="p_france"),
        types.InlineKeyboardButton("🇪🇸 Espanha", callback_data="p_spain")
    )
    bot.send_message(message.chat.id, "🌍 *SELECIONE O PAÍS DO NÚMERO:*", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("p_"))
def escolher_servico(call):
    pais = call.data.split("_")[1]
    markup = types.InlineKeyboardMarkup(row_width=1)
    # Preços fixos para facilitar a gestão
    markup.add(
        types.InlineKeyboardButton("💬 WhatsApp - 1.50€", callback_data=f"buy_{pais}_whatsapp"),
        types.InlineKeyboardButton("✈️ Telegram - 1.20€", callback_data=f"buy_{pais}_telegram")
    )
    bot.edit_message_text(f"📍 País Selecionado: *{pais.upper()}*\n🚀 *Escolha o serviço desejado:*", 
                          call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def processar_compra(call):
    _, pais, serv = call.data.split("_")
    user_id = call.from_user.id
    precos = {"whatsapp": 1.50, "telegram": 1.20}
    custo = precos.get(serv, 1.50)

    if get_balance(user_id) < custo:
        bot.answer_callback_query(call.id, "❌ Saldo insuficiente!", show_alert=True)
        return

    bot.edit_message_text(f"⏳ *Buscando número do {pais.upper()}...*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    headers = {'Authorization': f'Bearer {API_5SIM}', 'Accept': 'application/json'}
    
    # Tentativa de compra
    url = f"https://5sim.net/v1/user/buy/activation/{pais}/any/{serv}"
    
    try:
        r = requests.get(url, headers=headers, timeout=60)
        res = r.json()
        
        if r.status_code == 200:
            update_balance(user_id, -custo)
            bot.send_message(call.message.chat.id, f"✅ *NÚMERO DO {pais.upper()} GERADO!*\n\n📱 Número: `{res['phone']}`\n🆔 ID: `{res['id']}`\n\n_Copie o número e peça o código. Aguardando o SMS aqui..._", parse_mode="Markdown")
            
            # Loop de verificação de SMS (aguarda até 4 minutos)
            for _ in range(24):
                time.sleep(10)
                c = requests.get(f"https://5sim.net/v1/user/check/{res['id']}", headers=headers).json()
                if c.get('sms'):
                    bot.send_message(call.message.chat.id, f"📩 *CÓDIGO RECEBIDO PARA {pais.upper()}:*\n\n🔑 Código: `{c['sms'][0]['code']}`",
