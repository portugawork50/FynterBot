import telebot
from telebot import types
import sqlite3
import requests
import time
import os

# --- CONFIGURAÇÕES ---
# O bot tenta ler das variáveis do Railway, se não houver, usa os valores padrão
TOKEN = os.getenv('BOT_TOKEN', '8338751670:AAEe17MTCw2uEBCGz2S68eXkdlpHLgf1Gho')
ADMIN_ID = int(os.getenv('ADMIN_ID', 8647771753))
API_5SIM = os.getenv('API_5SIM', 'EyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE4MDg1MjQ5ODQsImlhdCI6MTc3Njk4ODk4NCwicmF5IjoiN2EyZTM1ZTA2NjJjNTUzM2QzYmI3M2ZhMzgzNWRiNTgiLCJzdWIiOjQwMDA4MjJ9.uLu1Ggft6JUWcQJOlHehmY9CyZFxf4Ip8yRIoI7ExRlNa8h1ccN1M8JYp2z4D5MCJEFiqZL_e0X34PfQ82VBjSv5mIZS8pV_JfCoIpbBXb6ecoHYwaStmwGT633lqeFFHtEX1kBmVcOQvwb_38V2RwQdENwc4LidIbocIsqibIyk4eMHlfRFakJbxKEYQxXK7UlANL2sErMSNwj_Gs3j9CMHiWBeNAk2oFYnMsJHcx73102jwl7GcYa6Rl4IU2K2Qwc72g350Ws2tOQ48wltEt2K7Z3-S4v8l_RIiekLsUlRT692i0ffc8XBftAxz66PeDuPIVMCtQoljb5l5gEVwA')

bot = telebot.TeleBot(TOKEN)

# Caminho do banco de dados (ajustado para funcionar com ou sem volume)
DB_PATH = 'bot_database.db'
if os.path.exists('/app/data'):
    DB_PATH = '/app/data/bot_database.db'

# --- FUNÇÕES DE BANCO DE DADOS ---
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

# --- COMANDOS ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    init_db()
    update_balance(message.from_user.id, 0)
    bot.send_message(message.chat.id, "👋 Bem-vindo ao **FynterBot**! \nUse o menu abaixo para navegar.", 
                     reply_markup=menu_principal(), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "👤 MINHA CONTA")
def conta(message):
    saldo = get_balance(message.from_user.id)
    bot.send_message(message.chat.id, f"👤 **CONTA**\n\n🆔 ID: `{message.from_user.id}`\n💰 Saldo: **{saldo:.2f} €**", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "💳 RECARREGAR")
def recarga(message):
    msg = (f"💳 **RECARGA DE SALDO**\n\n"
           f"🟢 **USDT (TRC20):**\n`TWxHqzW9MBAymeBnqx3WX6VyNUPKMmhoXU`\n\n"
           f"🔵 **MB WAY / IBAN:**\nFale com @pobrerico__\n\n"
           f"⚠️ Envie o comprovativo e o seu ID:\n🆔 ID: `{message.from_user.id}`")
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🆘 SUPORTE")
def suporte(message):
    bot.send_message(message.chat.id, "🆘 Precisa de ajuda? Contacte: @pobrerico__")

# --- ADMIN: ADICIONAR SALDO ---
@bot.message_handler(commands=['add'])
def add_saldo(message):
    if message.from_user.id == ADMIN_ID:
        try:
            # Formato: /add ID VALOR
            args = message.text.split()
            target_id = int(args[1])
            valor = float(args[2])
            update_balance(target_id, valor)
            bot.reply_to(message, f"✅ Sucesso! Adicionado **{valor}€** ao ID `{target_id}`", parse_mode="Markdown")
            bot.send_message(target_id, f"🎉 **Saldo creditado!**\nForam adicionados **{valor}€** à sua conta.")
        except Exception as e:
            bot.reply_to(message, "❌ Erro. Use: `/add ID VALOR` \nExemplo: `/add 8647771753 10`", parse_mode="Markdown")
    else:
        bot.reply_to(message, "🚫 Acesso Negado.")

# --- GERAR NÚMEROS (INLINE) ---
@bot.message_handler(func=lambda m: m.text == "📱 GERAR NÚMERO")
def escolher_pais(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🇧🇷 Brasil", callback_data="pais_brazil"),
               types.InlineKeyboardButton("🇵🇹 Portugal", callback_data="pais_portugal"))
    bot.send_message(message.chat.id, "🌍 Escolha o país:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pais_"))
def escolher_servico(call):
    pais = call.data.split("_")[1]
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("WhatsApp (1.50€)", callback_data=f"buy_{pais}_whatsapp"),
               types.InlineKeyboardButton("Telegram (1.20€)", callback_data=f"buy_{pais}_telegram"))
    bot.edit_message_text(f"📍 País: {pais.upper()}\nSelecione o serviço:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def processar_compra(call):
    _, pais, serv = call.data.split("_")
    user_id = call.from_user.id
    # Preços fixos para teste
    precos = {"whatsapp": 1.50, "telegram": 1.20}
    custo = precos.get(serv, 2.0)

    if get_balance(user_id) < custo:
        bot.answer_callback_query(call.id, "❌ Saldo Insuficiente!", show_alert=True)
        return

    bot.edit_message_text("⏳ Conectando ao 5sim...", call.message.chat.id, call.message.message_id)
    
    headers = {'Authorization': f'Bearer {API_5SIM}', 'Accept': 'application/json'}
    url = f"https://5sim.net/v1/user/buy/activation/{pais}/any/{serv}"
    
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            res = r.json()
            update_balance(user_id, -custo)
            bot.send_message(call.message.chat.id, f"✅ **NÚMERO:** `{res['phone']}`\n🆔 Pedido: `{res['id']}`\nAguarde o SMS chegar...", parse_mode="Markdown")
        else:
            bot.send_message(call.message.chat.id, "❌ Sem números disponíveis ou saldo insuficiente no 5sim.")
    except:
        bot.send_message(call.message.chat.id, "❌ Erro ao processar pedido.")

# --- INICIALIZAÇÃO ---
if __name__ == "__main__":
    init_db()
    print("Bot rodando...")
    bot.infinity_polling()
