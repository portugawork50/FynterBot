import telebot
from telebot import types
import sqlite3

# --- CONFIGURAÇÕES ---
TOKEN = '8338751670:AAEe17MTCw2uEBCGz2S68eXkdlpHLgf1Gho'
ADMIN_ID = 8647771753  # Seu ID corrigido
bot = telebot.TeleBot(TOKEN)

# --- BANCO DE DADOS (SQLite) ---
def init_db():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0)''')
    conn.commit()
    conn.close()

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
    btn1 = types.KeyboardButton("📱 GERAR NÚMERO")
    btn2 = types.KeyboardButton("💳 RECARREGAR")
    btn3 = types.KeyboardButton("👤 MINHA CONTA")
    btn4 = types.KeyboardButton("🆘 SUPORTE")
    markup.add(btn1, btn2, btn3, btn4)
    return markup

# --- COMANDOS ---
@bot.message_handler(commands=['start'])
def start(message):
    init_db()
    user_id = message.from_user.id
    update_balance(user_id, 0.0) # Apenas para registrar o usuário
    
    msg = (f"Olá {message.from_user.first_name}! 🤖\n\n"
           "Bem-vindo ao *FynterBot*.\n"
           "Aqui você gera números virtuais para SMS de +100 países instantaneamente.")
    bot.send_message(message.chat.id, msg, parse_mode="Markdown", reply_markup=main_menu())

@bot.message_handler(func=lambda message: message.text == "👤 MINHA CONTA")
def conta(message):
    saldo = get_balance(message.from_user.id)
    msg = (f"👤 *Suas Informações:*\n\n"
           f"🆔 ID: `{message.from_user.id}`\n"
           f"💰 Saldo: *{saldo:.2f} €*")
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "💳 RECARREGAR")
def recarregar(message):
    texto = (
        "🌍 *RECARGA GLOBAL* 🌍\n\n"
        "🟢 *OPÇÃO 1: USDT (Rede TRC20)*\n"
        "Envie para o endereço abaixo:\n"
        "🔹 `TWxHqzW9MBAymeBnqx3WX6VyNUPKMmhoXU` \n"
        "_(Toque no endereço para copiar)_\n\n"
        "🔵 *OPÇÃO 2: MB WAY / IBAN (Portugal 🇵🇹)*\n"
        "Envie o comprovativo para o suporte:\n"
        "👉 @pobrerico__\n\n"
        "⚠️ *IMPORTANTE:* Envie o comprovativo e seu ID para validar o saldo:\n"
        f"🆔 *Seu ID:* `{message.from_user.id}`"
    )
    bot.send_message(message.chat.id, texto, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "🆘 SUPORTE")
def suporte(message):
    bot.send_message(message.chat.id, "Dúvidas ou problemas? Fale com o admin: @pobrerico__")

@bot.message_handler(func=lambda message: message.text == "📱 GERAR NÚMERO")
def gerar_numero(message):
    saldo = get_balance(message.from_user.id)
    if saldo <= 0:
        bot.send_message(message.chat.id, "❌ Você não tem saldo suficiente. Recarregue para gerar números.")
    else:
        bot.send_message(message.chat.id, "🚀 Escolha o serviço: (Integração com API em breve!)")

# --- COMANDO DE ADMIN PARA ADICIONAR SALDO ---
# Uso: /add ID VALOR
@bot.message_handler(commands=['add'])
def add_balance_admin(message):
    if message.from_user.id == ADMIN_ID:
        try:
            parts = message.text.split()
            target_id = int(parts[1])
            amount = float(parts[2])
            update_balance(target_id, amount)
            bot.send_message(message.chat.id, f"✅ Adicionado {amount}€ ao usuário {target_id}")
            bot.send_message(target_id, f"🎉 *Recarga Confirmada!*\nForam adicionados *{amount}€* ao seu saldo.", parse_mode="Markdown")
        except:
            bot.reply_to(message, "❌ Erro! Use: `/add ID VALOR` (Ex: /add 8647771753 10.00)")
    else:
        bot.reply_to(message, "🚫 Acesso negado. Apenas o administrador pode usar este comando.")

# --- INICIALIZAÇÃO ---
if __name__ == "__main__":
    init_db()
    print("🤖 FynterBot Online!")
    bot.infinity_polling()
