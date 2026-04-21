import os
import telebot
import requests
import sqlite3

# --- 1. CONFIGURAÇÕES INICIAIS (Sempre no topo) ---
TOKEN = "8338751670:AAEe17MTCw2uEBCGz2S68eXkdlpHLgf1Gho"
bot = telebot.TeleBot(TOKEN)
ADMIN_ID = 8647771753  # Seu ID correto
GRIZZLY_KEY = os.getenv("GRIZZLY_API_KEY")

# --- 2. BANCO DE DADOS ---
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

# --- 3. COMANDOS DO BOT ---

@bot.message_handler(commands=['start'])
def start(message):
    init_db()
    bot.reply_to(message, "🚀 Bot Online! Use o menu ou fale com o suporte.")

@bot.message_handler(commands=['setar'])
def setar(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, f"❌ Acesso negado. Seu ID: {message.from_user.id}")
        return
    try:
        partes = message.text.split()
        if len(partes) == 3:
            target_id = int(partes[1])
            valor = float(partes[2])
            add_saldo(target_id, valor)
            bot.reply_to(message, f"✅ Adicionado €{valor} ao ID {target_id}")
        else:
            bot.reply_to(message, "⚠️ Use: /setar ID VALOR")
    except Exception as e:
        bot.reply_to(message, f"❌ Erro: {e}")

# --- 4. LIGAR O BOT ---
if __name__ == "__main__":
    print("Iniciando o bot...")
    init_db()
    bot.infinity_polling()
