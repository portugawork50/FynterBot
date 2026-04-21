import os
import telebot
import requests
import sqlite3

# 1. PRIMEIRO define o Token e cria o bot
TOKEN = "8338751670:AAEe17MTCw2uEBCGz2S68eXkdlpHLgf1Gho"
bot = telebot.TeleBot(TOKEN)

# 2. Define o ID de Administrador (O SEU ID)
ADMIN_ID = 123456789  # <--- MUDE PARA O SEU ID REAL

# 3. Define a Key do Grizzly
GRIZZLY_KEY = os.getenv("GRIZZLY_API_KEY")

# 4. Funções de Banco de Dados
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                    (id INTEGER PRIMARY KEY, saldo REAL DEFAULT 0)''')
    conn.commit()
    conn.close()

def add_saldo(user_id, valor):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (id, saldo) VALUES (?, 0)", (user_id,))
    cursor.execute("UPDATE users SET saldo = saldo + ? WHERE id = ?", (valor, user_id))
    conn.commit()
    conn.close()

# 5. AGORA sim vêm os comandos (handlers)
@bot.message_handler(commands=['start'])
def start(message):
    init_db()
    bot.reply_to(message, "🚀 Bot Online! Use o menu ou fale com o suporte.")

@bot.message_handler(commands=['setar'])
def setar(message):
    if message.from_user.id == ADMIN_ID:
        try:
            _, target_id, valor = message.text.split()
            add_saldo(int(target_id), float(valor))
            bot.reply_to(message, "✅ Saldo atualizado!")
        except:
            bot.reply_to(message, "❌ Erro. Use: /setar ID VALOR")

# 6. FINAL: O comando para o bot ficar ligado
print("Bot ligando...")
init_db()
bot.infinity_polling()
