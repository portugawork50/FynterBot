import telebot
from telebot import types
import sqlite3
import requests
import time
import os

# --- CONFIGURAÇÕES ---
TOKEN = '8338751670:AAEe17MTCw2uEBCGz2S68eXkdlpHLgf1Gho'
ADMIN_ID = 8647771753
API_5SIM = 'EyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE4MDg1MjQ5ODQsImlhdCI6MTc3Njk4ODk4NCwicmF5IjoiN2EyZTM1ZTA2NjJjNTUzM2QzYmI3M2ZhMzgzNWRiNTgiLCJzdWIiOjQwMDA4MjJ9.uLu1Ggft6JUWcQJOlHehmY9CyZFxf4Ip8yRIoI7ExRlNa8h1ccN1M8JYp2z4D5MCJEFiqZL_e0X34PfQ82VBjSv5mIZS8pV_JfCoIpbBXb6ecoHYwaStmwGT633lqeFFHtEX1kBmVcOQvwb_38V2RwQdENwc4LidIbocIsqibIyk4eMHlfRFakJbxKEYQxXK7UlANL2sErMSNwj_Gs3j9CMHiWBeNAk2oFYnMsJHcx73102jwl7GcYa6Rl4IU2K2Qwc72g350Ws2tOQ48wltEt2K7Z3-S4v8l_RIiekLsUlRT692i0ffc8XBftAxz66PeDuPIVMCtQoljb5l5gEVwA'

bot = telebot.TeleBot(TOKEN)

# Banco de Dados
DB_PATH = 'bot_database.db'
if os.path.exists('/app/data'):
    DB_PATH = '/app/data/bot_database.db'

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
    btn1 = types.KeyboardButton("📱 GERAR NÚMERO")
    btn2 = types.KeyboardButton("💳 RECARREGAR")
    btn3 = types.KeyboardButton("👤 MINHA CONTA")
    btn4 = types.KeyboardButton("🆘 SUPORTE")
    markup.add(btn1, btn2, btn3, btn4)
    return markup

# --- COMANDO START (O "BONITO") ---
@bot.message_handler(commands=['start'])
def welcome(message):
    init_db()
    update_balance(message.from_user.id, 0)
    
    # Texto de Boas-vindas com Estilo
    texto_boas_vindas = (
        f"👋 *Olá, {message.from_user.first_name}!*\n\n"
        f"Bem-vindo ao *FynterBot* 🤖\n"
        f"A sua plataforma nº1 para ativações de SMS!\n\n"
        f"⚡️ *Rápido | Automático | Seguro*\n\n"
        f"Escolha uma opção no menu abaixo para começar: 👇"
    )
    
    bot.send_message(
        message.chat.id, 
        texto_boas_vindas, 
        reply_markup=menu_principal(), 
        parse_mode="Markdown"
    )

# --- OUTROS COMANDOS ---
@bot.message_handler(func=lambda m: m.text == "👤 MINHA CONTA")
def conta(message):
    saldo = get_balance(message.from_user.id)
    msg = (
        f"👤 *DADOS DA CONTA*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🆔 *ID:* `{message.from_user.id}`\n"
        f"💰 *SALDO:* `{saldo:.2f} €`"
    )
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "💳 RECARREGAR")
def recarga(message):
    msg = (
        f"💳 *RECARGA DE SALDO*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🏦 *MÉTODOS ACEITES:*\n\n"
        f"🟢 *USDT (TRC20):*\n`TWxHqzW9MBAymeBnqx3WX6VyNUPKMmhoXU`\n\n"
        f"🔵 *MB WAY / IBAN:*\nContacte @portugam50\n\n"
        f"⚠️ *Nota:* Envie o comprovativo e o seu ID: `{message.from_user.id}`"
    )
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🆘 SUPORTE")
def suporte(message):
    bot.send_message(message.chat.id, "🆘 *SUPORTE TÉCNICO*\n\nPrecisa de ajuda? Clique aqui: @portugam50", parse_mode="Markdown")

# --- COMPRA DE NÚMEROS ---
@bot.message_handler(func=lambda m: m.text == "📱 GERAR NÚMERO")
def escolher_pais(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🇧🇷 Brasil", callback_data="pais_brazil"),
        types.InlineKeyboardButton("🇵🇹 Portugal", callback_data="pais_portugal"),
        types.InlineKeyboardButton("🇺🇸 EUA", callback_data="pais_usa")
    )
    bot.send_message(message.chat.id, "🌍 *SELECIONE O PAÍS:*", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("pais_"))
def escolher_servico(call):
    pais = call.data.split("_")[1]
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("💬 WhatsApp - 1.50€", callback_data=f"buy_{pais}_whatsapp"),
        types.InlineKeyboardButton("✈️ Telegram - 1.20€", callback_data=f"buy_{pais}_telegram")
    )
    bot.edit_message_text(f"📍 *País:* {pais.upper()}\n🚀 *Selecione o Serviço:*", 
                          call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def processar_compra(call):
    _, pais, serv = call.data.split("_")
    user_id = call.from_user.id
    precos = {"whatsapp": 1.50, "telegram": 1.20}
    custo = precos.get(serv, 1.50)

    if get_balance(user_id) < custo:
        bot.answer_callback_query(call.id, "❌ Saldo Insuficiente!", show_alert=True)
        return

    bot.edit_message_text("⏳ *A gerar número...*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    headers = {'Authorization': f'Bearer {API_5SIM}', 'Accept': 'application/json'}
    url = f"https://5sim.net/v1/user/buy/activation/{pais}/any/{serv}"
    
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            res = r.json()
            update_balance(user_id, -custo)
            bot.send_message(call.message.chat.id, f"✅ *NÚMERO GERADO!*\n\n📱 *Número:* `{res['phone']}`\n🆔 *Pedido:* `{res['id']}`\n\nAguarde o código aqui...", parse_mode="Markdown")
            
            for _ in range(15):
                time.sleep(15)
                c = requests.get(f"https://5sim.net/v1/user/check/{res['id']}", headers=headers).json()
                if c.get('sms'):
                    bot.send_message(call.message.chat.id, f"📩 *CÓDIGO:* `{c['sms'][0]['code']}`", parse_mode="Markdown")
                    return
            bot.send_message(call.message.chat.id, "⚠️ SMS atrasado. Verifique o site ou tente novamente.")
        else:
            bot.send_message(call.message.chat.id, "❌ Sem stock no momento.")
    except:
        bot.send_message(call.message.chat.id, "❌ Erro de conexão.")

# --- ADMIN ---
@bot.message_handler(commands=['add'])
def add_saldo(message):
    if message.from_user.id == ADMIN_ID:
        try:
            args = message.text.split()
            update_balance(int(args[1]), float(args[2]))
            bot.reply_to(message, "✅ Saldo adicionado com sucesso!")
        except:
            bot.reply_to(message, "Use: /add ID VALOR")

if __name__ == "__main__":
    init_db()
    bot.infinity_polling()
