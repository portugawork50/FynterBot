import telebot
from telebot import types
import sqlite3
import requests
import time
import os

# --- CONFIGURAÇÕES ---
TOKEN = '8338751670:AAEe17MTCw2uEBCGz2S68eXkdlpHLgf1Gho'
ADMIN_ID = 8647771753
# Tua chave API JWT atualizada
API_5SIM = 'eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE4MDg1NjM2MDIsImlhdCI6MTc3Njk4ODk4NCwicmF5IjoiN2EyZTM1ZTA2NjJjNTUzM2QzYmI3M2ZhMzgzNWRiNTgiLCJzdWIiOjQwMDA4MjJ9.AFEiVz5FmQ9RU_x_GvO-hFGu9ThDWm-Co5yT1DjKruXLRrgxtpGsBOUJA-FvEUUDD08pkZ9DU0YBNMZQ1r89FYZDufXA7U5OoDbddzg-CbYVbh3sJaMAeKSaWTvlAIkf1b8Fx3eQMmmNC2GDrVHYT8Dr8LQU2m7kJAcoppnvkx-ZZ4sT1t8mJiUc6TD1Mb2rFGNzcRIGDI5-icO3kzKAMqfDmXBmS4N3_pZ5wCTNYZmvKkISwbI_hWJptPpi8WwEY0nL4wIJclSXMSpsgZDpei9D5jD_czf9Hf_DHqXAPJo5s7_dcD6UCBrJ-P74F7IspnPTh4nGhTlJgg89o8LNRQ'.strip()

bot = telebot.TeleBot(TOKEN)
DB_PATH = 'bot_database.db'

# --- BANCO DE DADOS ---
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
        f"🛡️ _Ativações SMS automáticas e instantâneas._\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📍 +10 Países Disponíveis\n"
        f"👤 Suporte: @portugam50\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👇 *Escolha uma opção no menu abaixo:* "
    )
    bot.send_message(message.chat.id, texto, reply_markup=menu_principal(), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📱 GERAR NÚMERO")
def escolher_pais(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🇬🇧 Inglaterra", callback_data="p_england"),
        types.InlineKeyboardButton("🇺🇸 EUA", callback_data="p_usa"),
        types.InlineKeyboardButton("🇵🇹 Portugal", callback_data="p_portugal"),
        types.InlineKeyboardButton("🇧🇷 Brasil", callback_data="p_brazil"),
        types.InlineKeyboardButton("🇫🇷 França", callback_data="p_france"),
        types.InlineKeyboardButton("🇪🇸 Espanha", callback_data="p_spain")
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
    bot.edit_message_text(f"📍 País: *{pais.upper()}*\n🚀 *Escolha o serviço:*", 
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

    bot.edit_message_text("⏳ *A procurar número disponível...*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    headers = {'Authorization': f'Bearer {API_5SIM}', 'Accept': 'application/json'}
    url = f"https://5sim.net/v1/user/buy/activation/{pais}/any/{serv}"
    
    try:
        r = requests.get(url, headers=headers, timeout=30)
        res = r.json()
        
        if r.status_code == 200:
            update_balance(user_id, -custo)
            bot.send_message(call.message.chat.id, f"✅ *NÚMERO ENCONTRADO!*\n\n📱 Número: `{res['phone']}`\n🆔 Pedido: `{res['id']}`\n\n_Aguardando o SMS (pode demorar até 2 min)..._", parse_mode="Markdown")
            
            # Loop de verificação de SMS
            for _ in range(20):
                time.sleep(12)
                c = requests.get(f"https://5sim.net/v1/user/check/{res['id']}", headers=headers).json()
                if c.get('sms'):
                    bot.send_message(call.message.chat.id, f"📩 *CÓDIGO RECEBIDO:* `{c['sms'][0]['code']}`", parse_mode="Markdown")
                    return
            bot.send_message(call.message.chat.id, "⚠️ O SMS está a demorar. O saldo foi descontado, mas o número continua ativo no fornecedor.")
        else:
            # Tratamento de falta de stock
            erro_msg = res.get('errors', ['Sem stock'])[0]
            if "no free numbers" in erro_msg.lower():
                bot.send_message(call.message.chat.id, f"❌ *SEM STOCK EM {pais.upper()}*\n\nInfelizmente não há números de {serv} agora.\n\n💡 *DICA:* Tente **Inglaterra** ou **EUA**, costumam ter sempre!", parse_mode="Markdown")
            else:
                bot.send_message(call.message.chat.id, f"❌ *ERRO:* {erro_msg}")
    except:
        bot.send_message(call.message.chat.id, "⚠️ O servidor demorou a responder. Tente de novo.")

# --- MINHA CONTA ---
@bot.message_handler(func=lambda m: m.text == "👤 MINHA CONTA")
def conta(message):
    saldo = get_balance(message.from_user.id)
    bot.send_message(message.chat.id, f"👤 *DADOS DA CONTA*\n\n🆔 ID: `{message.from_user.id}`\n💰 Saldo: `{saldo:.2f} €`", parse_mode="Markdown")

# --- RECARREGAR ---
@bot.message_handler(func=lambda m: m.text == "💳 RECARREGAR")
def recarga(message):
    texto_recarga = (
        "💳 *RECARGA DE SALDO*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "🔵 *MB WAY / IBAN / PAYPAL:*\n"
        "Entre em contacto com o suporte para pagar:\n"
        "👉 @portugam50\n\n"
        "🟢 *CRIPTO (USDT - TRC20):*\n"
        "Endereço para depósito:\n"
        "`TWxHqzW9MBAymeBnqx3WX6VyNUPKMmhoXU`\n\n"
        "⚠️ *AVISO:* Após o pagamento, envie o comprovativo e o seu ID abaixo.\n\n"
        f"🆔 *Seu ID:* `{message.from_user.id}`"
    )
    bot.send_message(message.chat.id, texto_recarga, parse_mode="Markdown")

# --- SUPORTE ---
@bot.message_handler(func=lambda m: m.text == "🆘 SUPORTE")
def suporte(message):
    bot.send_message(message.chat.id, "🆘 *SUPORTE:* @portugam50\n\nFale connosco para recargas ou dúvidas.")

# --- ADMIN: ADICIONAR SALDO ---
@bot.message_handler(commands=['add'])
def add_admin(message):
    if message.from_user.id == ADMIN_ID:
        try:
            p = message.text.split()
            update_balance(int(p[1]), float(p[2]))
            bot.reply_to(message, f"✅ Saldo de {p[2]}€ adicionado ao ID {p[1]}!")
        except:
            bot.reply_to(message, "❌ Use: /add ID VALOR")

if __name__ == "__main__":
    init_db()
    bot.infinity_polling()
