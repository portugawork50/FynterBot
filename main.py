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

@bot.callback_query_handler(func=lambda call: call.data == "recarregar")
def menu_revolut(call):
    # Substitua pelo seu link real do Revolut
    seu_link_revolut = "https://revolut.me/seuusuario" 
    
    texto = (
        "💳 *RECARGA VIA REVOLUT*\n\n"
        "Siga os passos abaixo para adicionar saldo:\n\n"
        "1️⃣ Clique no botão abaixo para abrir o link.\n"
        "2️⃣ Envie o valor desejado (Mínimo €1.00).\n"
        "3️⃣ No campo de *Nota/Mensagem* do Revolut, coloque seu ID:\n"
        f"👉 `{call.from_user.id}`\n\n"
        "⚠️ *Importante:* Após o pagamento, envie o comprovante (print) para o suporte."
    )

    markup = telebot.types.InlineKeyboardMarkup()
    btn_pagar = telebot.types.InlineKeyboardButton("🔗 Abrir Revolut", url=revolut.me/goncalom35)
    btn_suporte = telebot.types.InlineKeyboardButton("👨‍💻 Enviar Comprovante", url="https://t.me/portugam50")
    
    markup.add(btn_pagar)
    markup.add(btn_suporte)

    bot.edit_message_text(texto, 
                          call.message.chat.id, 
                          call.message.message_id, 
                          reply_markup=markup, 
                          parse_mode="Markdown") 


# --- 4. LIGAR O BOT ---
if __name__ == "__main__":
    print("Iniciando o bot...")
    init_db()
    bot.infinity_polling()
