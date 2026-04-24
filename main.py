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
    texto = (
        f"🌟 *BEM-VINDO AO FYNTERBOT!* 🌟\n\n"
        f"🛡️ _A tua solução segura para ativações SMS._\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"✅ +10 Países de alta disponibilidade\n"
        f"✅ Ativação instantânea\n"
        f"✅ Suporte: @portugam50\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👇 *Escolha uma opção no menu abaixo:* "
    )
    bot.send_message(message.chat.id, texto, reply_markup=menu_principal(), parse_mode="Markdown")

# --- LISTA DE PAÍSES (10 OPÇÕES) ---
PAISES_LISTA = {
    "portugal": "🇵🇹 Portugal",
    "brazil": "🇧🇷 Brasil",
    "usa": "🇺🇸 EUA",
    "england": "🇬🇧 Inglaterra",
    "france": "🇫🇷 França",
    "spain": "🇪🇸 Espanha",
    "netherlands": "🇳🇱 Holanda",
    "germany": "🇩🇪 Alemanha",
    "canada": "🇨🇦 Canadá",
    "angola": "🇦🇴 Angola"
}

@bot.message_handler(func=lambda m: m.text == "📱 GERAR NÚMERO")
def escolher_pais(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    botoes = []
    for cod, nome in PAISES_LISTA.items():
        botoes.append(types.InlineKeyboardButton(nome, callback_data=f"p_{cod}"))
    markup.add(*botoes)
    bot.send_message(message.chat.id, "🌍 *SELECIONE O PAÍS:*", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("p_"))
def escolher_servico(call):
    pais = call.data.split("_")[1]
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("💬 WhatsApp - 1.50€", callback_data=f"buy_{pais}_whatsapp"),
        types.InlineKeyboardButton("✈️ Telegram - 1.20€", callback_data=f"buy_{pais}_telegram")
    )
    bot.edit_message_text(f"📍 País: *{pais.upper()}*\n🚀 *Selecione o serviço:*", 
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

    bot.edit_message_text("⏳ *A solicitar número ao servidor...*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    headers = {'Authorization': f'Bearer {API_5SIM}', 'Accept': 'application/json'}
    url = f"https://5sim.net/v1/user/buy/activation/{pais}/any/{serv}"
    
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            res = r.json()
            update_balance(user_id, -custo)
            bot.send_message(call.message.chat.id, f"✅ *NÚMERO:* `{res['phone']}`\n🆔 Pedido: `{res['id']}`\n\nAguardando o código SMS...")
            
            # Loop de verificação (3 minutos)
            for _ in range(18):
                time.sleep(10)
                c = requests.get(f"https://5sim.net/v1/user/check/{res['id']}", headers=headers).json()
                if c.get('sms'):
                    bot.send_message(call.message.chat.id, f"📩 *CÓDIGO:* `{c['sms'][0]['code']}`")
                    return
            bot.send_message(call.message.chat.id, "⚠️ SMS demorou muito. Tente novamente.")
        else:
            bot.send_message(call.message.chat.id, f"❌ Sem stock em {pais.upper()} agora. Tente outro país!")
    except:
        bot.send_message(call.message.chat.id, "❌ Erro na API.")

# --- OUTROS COMANDOS ---
@bot.message_handler(func=lambda m: m.text == "👤 MINHA CONTA")
def conta(message):
    saldo = get_balance(message.from_user.id)
    bot.send_message(message.chat.id, f"👤 *DADOS DA CONTA*\n\n🆔 ID: `{message.from_user.id}`\n💰 Saldo: `{saldo:.2f} €`", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "💳 RECARREGAR")
def recarga(message):
    bot.send_message(message.chat.id, f"💳 *RECARGA*\n\n🟢 USDT (TRC20): `TWxHqzW9MBAymeBnqx3WX6VyNUPKMmhoXU`\n\n🔵 MB WAY / IBAN: @portugam50\n\n🆔 Teu ID: `{message.from_user.id}`", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🆘 SUPORTE")
def suporte(message):
    bot.send_message(message.chat.id, "🆘 *SUPORTE:* @portugam50")

@bot.message_handler(commands=['add'])
def add_admin(message):
    if message.from_user.id == ADMIN_ID:
        try:
            p = message.text.split()
            update_balance(int(p[1]), float(p[2]))
            bot.reply_to(message, "✅ Saldo adicionado!")
        except:
            bot.reply_to(message, "Use: /add ID VALOR")

if __name__ == "__main__":
    init_db()
    bot.infinity_polling()
