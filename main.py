import telebot
from telebot import types
import sqlite3
import requests
import time
import os

# --- CONFIGURAÇÕES ---
TOKEN = os.getenv('BOT_TOKEN', '8338751670:AAEe17MTCw2uEBCGz2S68eXkdlpHLgf1Gho')
ADMIN_ID = int(os.getenv('ADMIN_ID', 8647771753))
API_5SIM = os.getenv('API_5SIM')

bot = telebot.TeleBot(TOKEN)

# --- SISTEMA DE BANCO DE DADOS INTELIGENTE ---
# Se houver volume montado em /app/data, ele usa. Se não, usa a pasta local.
if os.path.exists('/app/data'):
    DB_PATH = '/app/data/bot_database.db'
else:
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

# --- COMANDOS ---
@bot.message_handler(commands=['start'])
def start(message):
    init_db()
    update_balance(message.from_user.id, 0)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📱 GERAR NÚMERO", "💳 RECARREGAR", "👤 MINHA CONTA")
    bot.send_message(message.chat.id, "🤖 *FynterBot Online!*", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "👤 MINHA CONTA")
def conta(message):
    saldo = get_balance(message.from_user.id)
    bot.send_message(message.chat.id, f"🆔 ID: `{message.from_user.id}`\n💰 Saldo: {saldo:.2f} €", parse_mode="Markdown")

@bot.message_handler(commands=['add'])
def add_admin(message):
    if message.from_user.id == ADMIN_ID:
        try:
            p = message.text.split()
            update_balance(int(p[1]), float(p[2]))
            bot.reply_to(message, "✅ Saldo adicionado!")
        except:
            bot.reply_to(message, "Use: /add ID VALOR")

# --- LÓGICA DE COMPRA ---
@bot.message_handler(func=lambda message: message.text == "📱 GERAR NÚMERO")
def menu_paises(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🇧🇷 Brasil", callback_data="p_brazil"),
               types.InlineKeyboardButton("🇵🇹 Portugal", callback_data="p_portugal"),
               types.InlineKeyboardButton("🇺🇸 EUA", callback_data="p_usa"))
    bot.send_message(message.chat.id, "🌍 Escolha o país:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('p_'))
def escolher_servico(call):
    pais = call.data.split('_')[1]
    markup = types.InlineKeyboardMarkup()
    # Adicionei os nomes corretos para a API do 5sim
    markup.add(types.InlineKeyboardButton("WhatsApp (1.50€)", callback_data=f"buy_{pais}_whatsapp"),
               types.InlineKeyboardButton("Telegram (1.20€)", callback_data=f"buy_{pais}_telegram"))
    bot.edit_message_text(f"📍 País: {pais.upper()}\nEscolha o serviço:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def comprar_final(call):
    _, pais, serv = call.data.split('_')
    user_id = call.from_user.id
    custo = 1.0 # Preço de teste

    if get_balance(user_id) < custo:
        bot.answer_callback_query(call.id, "❌ Sem saldo suficiente!", show_alert=True)
        return

    headers = {'Authorization': f'Bearer {API_5SIM}', 'Accept': 'application/json'}
    url = f"https://5sim.net/v1/user/buy/activation/{pais}/any/{serv}"
    
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            data = res.json()
            update_balance(user_id, -custo)
            bot.send_message(call.message.chat.id, f"✅ *Número:* `{data['phone']}`\n🆔 ID: {data['id']}\nAguarde o SMS...")
        else:
            bot.send_message(call.message.chat.id, "❌ Sem números no momento ou erro no 5sim.")
    except:
        bot.send_message(call.message.chat.id, "❌ Erro ao conectar à API.")

if __name__ == "__main__":
    init_db()
    bot.infinity_polling()
