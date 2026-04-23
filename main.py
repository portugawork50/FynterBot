import telebot
from telebot import types
import sqlite3
import requests
import time
import os

# --- CONFIGURAÇÕES ---
# O ideal é colocar nas 'Variables' do Railway, mas vou deixar aqui para facilitar seu deploy inicial
TOKEN = '8338751670:AAEe17MTCw2uEBCGz2S68eXkdlpHLgf1Gho'
ADMIN_ID = 8647771753 
API_5SIM = 'COLE_AQUI_SUA_API_KEY_DO_5SIM' # Pegue no site 5sim.net

bot = telebot.TeleBot(TOKEN)

# --- TABELA DE PREÇOS E PAÍSES ---
PAISES = {
    "brazil": "🇧🇷 Brasil",
    "usa": "🇺🇸 EUA",
    "portugal": "🇵🇹 Portugal"
}

SERVICOS = {
    "whatsapp": {"nome": "WhatsApp", "preco": 1.50},
    "telegram": {"nome": "Telegram", "preco": 1.20},
    "instagram": {"nome": "Instagram", "preco": 0.80}
}

# --- BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('bot_database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0)''')
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

# --- MENUS ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("📱 GERAR NÚMERO", "💳 RECARREGAR", "👤 MINHA CONTA", "🆘 SUPORTE")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    init_db()
    update_balance(message.from_user.id, 0)
    bot.send_message(message.chat.id, "🤖 *FynterBot Ativo!* \n\nEscolha uma opção no menu abaixo:", 
                     reply_markup=main_menu(), parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "👤 MINHA CONTA")
def conta(message):
    saldo = get_balance(message.from_user.id)
    bot.send_message(message.chat.id, f"👤 *Informações:*\n🆔 ID: `{message.from_user.id}`\n💰 Saldo: {saldo:.2f} €", parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "🆘 SUPORTE")
def suporte(message):
    bot.send_message(message.chat.id, "🆘 Dúvidas? Fale com o admin: @pobrerico__")

@bot.message_handler(func=lambda message: message.text == "💳 RECARREGAR")
def recarregar(message):
    bot.send_message(message.chat.id, 
        f"💰 *PARA RECARREGAR:*\n\n"
        f"1️⃣ Envie USDT (TRC20): `TWxHqzW9MBAymeBnqx3WX6VyNUPKMmhoXU` \n"
        f"2️⃣ Ou peça MB WAY/IBAN ao suporte: @pobrerico__\n\n"
        f"🆔 Seu ID para validar: `{message.from_user.id}`", parse_mode="Markdown")

# --- LÓGICA DE COMPRA ---
@bot.message_handler(func=lambda message: message.text == "📱 GERAR NÚMERO")
def menu_paises(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    botoes = [types.InlineKeyboardButton(nome, callback_data=f"country_{cod}") for cod, nome in PAISES.items()]
    markup.add(*botoes)
    bot.send_message(message.chat.id, "🌍 *Escolha o país do número:*", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('country_'))
def menu_servicos(call):
    pais_cod = call.data.split('_')[1]
    markup = types.InlineKeyboardMarkup(row_width=1)
    for serv_cod, info in SERVICOS.items():
        markup.add(types.InlineKeyboardButton(f"{info['nome']} - {info['preco']:.2f}€", callback_data=f"buy_{pais_cod}_{serv_cod}"))
    bot.edit_message_text(f"📍 País: {pais_cod.upper()}\n🚀 Selecione o serviço:", 
                          call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def finalizar_compra(call):
    _, pais, servico = call.data.split('_')
    custo = SERVICOS[servico]['preco']
    user_id = call.from_user.id

    if get_balance(user_id) < custo:
        bot.answer_callback_query(call.id, "⚠️ Saldo insuficiente!", show_alert=True)
        return

    bot.edit_message_text("⏳ Solicitando número...", call.message.chat.id, call.message.message_id)

    url = f"https://5sim.net/v1/user/buy/activation/{pais}/any/{servico}"
    headers = {'Authorization': f'Bearer {API_5SIM}', 'Accept': 'application/json'}

    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            data = res.json()
            update_balance(user_id, -custo)
            order_id = data['id']
            bot.send_message(call.message.chat.id, f"✅ *NÚMERO:* `{data['phone']}`\n🆔 Pedido: `{order_id}`\n\nAguardando SMS...")
            
            # Loop check SMS (Simplificado)
            for _ in range(15):
                time.sleep(15)
                c = requests.get(f"https://5sim.net/v1/user/check/{order_id}", headers=headers).json()
                if c.get('sms'):
                    bot.send_message(call.message.chat.id, f"📩 *CÓDIGO:* `{c['sms'][0]['code']}`")
                    return
            bot.send_message(call.message.chat.id, "⚠️ Tempo esgotado para o SMS.")
        else:
            bot.send_message(call.message.chat.id, "❌ Sem estoque no momento.")
    except:
        bot.send_message(call.message.chat.id, "❌ Erro na API.")

# --- ADMIN ---
@bot.message_handler(commands=['add'])
def add_balance_admin(message):
    if message.from_user.id == ADMIN_ID:
        try:
            parts = message.text.split()
            update_balance(int(parts[1]), float(parts[2]))
            bot.reply_to(message, "✅ Saldo Adicionado!")
        except:
            bot.reply_to(message, "Use: /add ID VALOR")

# --- BOOT ---
if __name__ == "__main__":
    init_db()
    print("Bot Ligado!")
    bot.infinity_polling()
