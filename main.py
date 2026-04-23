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

# --- MENUS ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("📱 GERAR NÚMERO", "💳 RECARREGAR", "👤 MINHA CONTA", "🆘 SUPORTE")
    return markup

# --- LÓGICA DE GERAR NÚMERO ---
@bot.message_handler(func=lambda message: message.text == "📱 GERAR NÚMERO")
def menu_paises(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    # Aqui você define os países (nome para o usuário, código para a API)
    btn1 = types.InlineKeyboardButton("🇧🇷 Brasil", callback_data="country_brazil")
    btn2 = types.InlineKeyboardButton("🇺🇸 EUA", callback_data="country_usa")
    btn3 = types.InlineKeyboardButton("🇵🇹 Portugal", callback_data="country_portugal")
    markup.add(btn1, btn2, btn3)
    bot.send_message(message.chat.id, "🌍 Escolha o país do número:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('country_'))
def menu_servicos(call):
    pais = call.data.split('_')[1]
    markup = types.InlineKeyboardMarkup(row_width=2)
    # Serviços comuns (nome, código_da_api_pais)
    btn1 = types.InlineKeyboardButton("WhatsApp (1.50€)", callback_data=f"buy_{pais}_whatsapp")
    btn2 = types.InlineKeyboardButton("Telegram (1.20€)", callback_data=f"buy_{pais}_telegram")
    btn3 = types.InlineKeyboardButton("Instagram (0.80€)", callback_data=f"buy_{pais}_instagram")
    markup.add(btn1, btn2, btn3)
    bot.edit_message_text(f"✅ País selecionado: {pais.capitalize()}\nAgora escolha o serviço:", 
                          call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def finalizar_compra(call):
    _, pais, servico = call.data.split('_')
    user_id = call.from_user.id
    
    # Tabela de Preços (Exemplo - Ajuste como quiser)
    precos = {"whatsapp": 1.50, "telegram": 1.20, "instagram": 0.80}
    custo = precos.get(servico, 2.00)

    if get_balance(user_id) < custo:
        bot.answer_callback_query(call.id, "❌ Saldo insuficiente!", show_alert=True)
        return

    bot.edit_message_text("⏳ Processando pedido no servidor...", call.message.chat.id, call.message.message_id)

    # Chamada API 5Sim
    url = f"https://5sim.net/v1/user/buy/activation/{pais}/any/{servico}"
    headers = {'Authorization': f'Bearer {API_5SIM}', 'Accept': 'application/json'}

    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            data = res.json()
            numero = data['phone']
            order_id = data['id']
            
            update_balance(user_id, -custo)
            bot.send_message(call.message.chat.id, f"✅ *NÚMERO PRONTO!*\n\n📱 Número: `{numero}`\n🆔 Pedido: `{order_id}`\n\n*Aguardando SMS...*")

            # Loop de Verificação de SMS (simplificado)
            for _ in range(30):
                time.sleep(10)
                check = requests.get(f"https://5sim.net/v1/user/check/{order_id}", headers=headers).json()
                if check.get('sms'):
                    codigo = check['sms'][0]['code']
                    bot.send_message(call.message.chat.id, f"📩 *CÓDIGO RECEBIDO:* `{codigo}`", parse_mode="Markdown")
                    return
            bot.send_message(call.message.chat.id, "⚠️ Tempo esgotado. Se o SMS não chegou, o valor será reembolsado (implementar lógica).")
        else:
            bot.send_message(call.message.chat.id, "❌ Provedor sem estoque para este serviço no momento.")
    except:
        bot.send_message(call.message.chat.id, "❌ Erro na conexão com o servidor de números.")

# --- COMANDOS BÁSICOS (RECARGA, CONTA, ADMIN) ---
# (Mantenha as funções de start, conta, suporte e /add que já tínhamos)

@bot.message_handler(commands=['start'])
def start(message):
    update_balance(message.from_user.id, 0)
    bot.send_message(message.chat.id, "🤖 FynterBot Ativo!", reply_markup=main_menu())

@bot.message_handler(func=lambda message: message.text == "👤 MINHA CONTA")
def conta(message):
    saldo = get_balance(message.from_user.id)
    bot.send_message(message.chat.id, f"👤 ID: `{message.from_user.id}`\n💰 Saldo: {saldo:.2f} €", parse_mode="Markdown")

@bot.message_handler(commands=['add'])
def add_balance_admin(message):
    if message.from_user.id == ADMIN_ID:
        parts = message.text.split()
        update_balance(int(parts[1]), float(parts[2]))
        bot.send_message(message.chat.id, "✅ Saldo adicionado!")

bot.infinity_polling()
