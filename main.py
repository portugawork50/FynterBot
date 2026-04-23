import telebot
from telebot import types
import sqlite3
import requests
import time

# --- CONFIGURAÇÕES ---
TOKEN = '8338751670:AAEe17MTCw2uEBCGz2S68eXkdlpHLgf1Gho'
ADMIN_ID = 8647771753
API_5SIM = 'COLE_AQUI_SUA_API_KEY_DO_5SIM'
bot = telebot.TeleBot(TOKEN)

# --- TABELA DE PREÇOS E PAÍSES (Ajuste aqui quando quiser!) ---
PAISES = {
    "brazil": "🇧🇷 Brasil",
    "usa": "🇺🇸 EUA",
    "portugal": "🇵🇹 Portugal",
    "angola": "🇦🇴 Angola"
}

SERVICOS = {
    "whatsapp": {"nome": "WhatsApp", "preco": 1.50},
    "telegram": {"nome": "Telegram", "preco": 1.20},
    "instagram": {"nome": "Instagram", "preco": 0.80},
    "facebook": {"nome": "Facebook", "preco": 0.70}
}

# --- BANCO DE DADOS ---
def update_balance(user_id, amount):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (id, balance) VALUES (?, 0.0)", (user_id,))
    cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def get_balance(user_id):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0.0

# --- MENU PRINCIPAL ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("📱 GERAR NÚMERO", "💳 RECARREGAR", "👤 MINHA CONTA", "🆘 SUPORTE")
    return markup

# --- FLUXO DE COMPRA ---

@bot.message_handler(func=lambda message: message.text == "📱 GERAR NÚMERO")
def menu_paises(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    botoes = [types.InlineKeyboardButton(nome, callback_data=f"country_{cod}") for cod, nome in PAISES.items()]
    markup.add(*botoes)
    bot.send_message(message.chat.id, "🌍 *Escolha o país do número:*", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('country_'))
def menu_servicos(call):
    pais_cod = call.data.split('_')[1]
    pais_nome = PAISES.get(pais_cod)
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for serv_cod, info in SERVICOS.items():
        btn_texto = f"{info['nome']} - {info['preco']:.2f}€"
        markup.add(types.InlineKeyboardButton(btn_texto, callback_data=f"buy_{pais_cod}_{serv_cod}"))
    
    markup.add(types.InlineKeyboardButton("⬅️ Voltar", callback_data="voltar_paises"))
    
    bot.edit_message_text(f"📍 *País:* {pais_nome}\n🚀 *Selecione o serviço:*", 
                          call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "voltar_paises")
def voltar_paises(call):
    menu_paises(call.message) # Simplesmente chama o menu de países de novo

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def finalizar_compra(call):
    _, pais, servico = call.data.split('_')
    user_id = call.from_user.id
    custo = SERVICOS[servico]['preco']

    if get_balance(user_id) < custo:
        bot.answer_callback_query(call.id, "⚠️ Saldo insuficiente!", show_alert=True)
        return

    bot.edit_message_text("⏳ *Aguarde... Solicitando número ao sistema.*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    # API 5Sim
    url = f"https://5sim.net/v1/user/buy/activation/{pais}/any/{servico}"
    headers = {'Authorization': f'Bearer {API_5SIM}', 'Accept': 'application/json'}

    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            data = res.json()
            numero = data['phone']
            order_id = data['id']
            
            update_balance(user_id, -custo)
            bot.send_message(call.message.chat.id, f"✅ *NÚMERO GERADO!*\n\n📱 Número: `{numero}`\n🆔 Pedido: `{order_id}`\n\n*Aguardando código SMS...*", parse_mode="Markdown")

            # Verificação automática (Máximo 3 minutos)
            for _ in range(18): 
                time.sleep(10)
                check = requests.get(f"https://5sim.net/v1/user/check/{order_id}", headers=headers).json()
                if check.get('sms'):
                    codigo = check['sms'][0]['code']
                    bot.send_message(call.message.chat.id, f"📩 *CÓDIGO RECEBIDO:* `{codigo}`", parse_mode="Markdown")
                    return
            
            bot.send_message(call.message.chat.id, "⚠️ O tempo acabou. Se não recebeu o código, o número expirou.")
        else:
            bot.send_message(call.message.chat.id, "❌ Não há números disponíveis para este país/serviço.")
    except:
        bot.send_message(call.message.chat.id, "❌ Erro ao conectar com o provedor.")

# --- OUTROS COMANDOS ---

@bot.message_handler(commands=['start'])
def start(message):
    update_balance(message.from_user.id, 0)
    bot.send_message(message.chat.id, "🤖 *FynterBot Ativo!*", reply_markup=main_menu(), parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "👤 MINHA CONTA")
def conta(message):
    saldo = get_balance(message.from_user.id)
    bot.send_message(message.chat.id, f"👤 *Informações:*\n🆔 ID: `{message.from_user.id}`\n💰 Saldo: {saldo:.2f} €", parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "💳 RECARREGAR")
def recarregar(message):
    bot.send_message(message.chat.id, f"💰 *Para recarregar:*\n\n1️⃣ Envie USDT (TRC20): `TWxHqzW9MBAymeBnqx3WX6VyNUPKMmhoXU`\n2️⃣ Ou peça MB WAY ao suporte.\n\n🆔 Seu ID: `{message.from_user.id}`", parse_mode="Markdown")

@bot.message_handler(commands=['add'])
def add_balance_admin(message):
    if message.from_user.id == ADMIN_ID:
        try:
            parts = message.text.split()
            update_balance(int(parts[1]), float(parts[2]))
            bot.send_message(message.chat.id, "✅ Saldo adicionado com sucesso!")
        except:
            bot.reply_to(message, "Use: /add ID VALOR")

bot.infinity_polling()
