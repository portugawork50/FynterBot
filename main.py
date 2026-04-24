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
    markup.add("📱 GERAR NÚMERO", "💳 RECARREGAR", "👤 MINHA CONTA", "🆘 SUPORTE")
    return markup

@bot.message_handler(commands=['start'])
def welcome(message):
    init_db()
    update_balance(message.from_user.id, 0)
    bot.send_message(message.chat.id, f"👋 Olá {message.from_user.first_name}!\n\nBem-vindo ao *FynterBot*.\nEscolha uma opção:", reply_markup=menu_principal(), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📱 GERAR NÚMERO")
def escolher_pais(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🇵🇹 Portugal", callback_data="p_portugal"),
        types.InlineKeyboardButton("🇧🇷 Brasil", callback_data="p_brazil"),
        types.InlineKeyboardButton("🇺🇸 EUA", callback_data="p_usa"),
        types.InlineKeyboardButton("🇬🇧 Inglaterra", callback_data="p_england"),
        types.InlineKeyboardButton("🇫🇷 França", callback_data="p_france"),
        types.InlineKeyboardButton("🇦🇴 Angola", callback_data="p_angola")
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
    precos = {"whatsapp": 1.50, "telegram": 1.20}
    custo = precos.get(serv, 1.50)

    if get_balance(user_id) < custo:
        bot.answer_callback_query(call.id, "❌ Saldo insuficiente no Bot!", show_alert=True)
        return

    bot.edit_message_text("⏳ *A solicitar número...*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    
    headers = {'Authorization': f'Bearer {API_5SIM}', 'Accept': 'application/json'}
    
    # TENTATIVA 1: Usando "any" operadora
    url = f"https://5sim.net/v1/user/buy/activation/{pais}/any/{serv}"
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        
        if r.status_code == 200:
            res = r.json()
            update_balance(user_id, -custo)
            bot.send_message(call.message.chat.id, f"✅ *NÚMERO:* `{res['phone']}`\n🆔 ID: `{res['id']}`\nAguarde o SMS...")
        else:
            # MOSTRAR O ERRO REAL PARA DIAGNÓSTICO
            erro_msg = r.text
            if "no free numbers" in erro_msg.lower():
                bot.send_message(call.message.chat.id, f"❌ O fornecedor está sem números de {serv} para {pais.upper()} agora. Tente outro país.")
            elif "not enough user balance" in erro_msg.lower():
                bot.send_message(call.message.chat.id, "❌ Erro: O saldo no site 5sim.net acabou!")
            elif "api key" in erro_msg.lower():
                bot.send_message(call.message.chat.id, "❌ Erro: Chave API inválida.")
            else:
                bot.send_message(call.message.chat.id, f"❌ Erro do Sistema: {erro_msg}")
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Erro de Conexão: {str(e)}")

# --- COMANDOS BÁSICOS ---
@bot.message_handler(func=lambda m: m.text == "👤 MINHA CONTA")
def conta(message):
    saldo = get_balance(message.from_user.id)
    bot.send_message(message.chat.id, f"👤 ID: `{message.from_user.id}`\n💰 Saldo: `{saldo:.2f} €`", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "💳 RECARREGAR")
def recarga(message):
    bot.send_message(message.chat.id, f"💳 Envie USDT ou peça MB WAY a @portugam50\nID: `{message.from_user.id}`")

@bot.message_handler(commands=['add'])
def add_admin(message):
    if message.from_user.id == ADMIN_ID:
        try:
            parts = message.text.split()
            update_balance(int(parts[1]), float(parts[2]))
            bot.reply_to(message, "✅ Saldo Adicionado!")
        except: pass

if __name__ == "__main__":
    init_db()
    bot.infinity_polling()
