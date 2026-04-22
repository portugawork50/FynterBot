import os
import telebot
import requests
import sqlite3

# --- 1. CONFIGURAÇÕES ---
TOKEN = "8338751670:AAEe17MTCw2uEBCGz2S68eXkdlpHLgf1Gho"
ADMIN_ID = 8647771753
GRIZZLY_KEY = os.getenv("GRIZZLY_API_KEY")

bot = telebot.TeleBot(TOKEN)

# --- 2. BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                    (id INTEGER PRIMARY KEY, saldo REAL DEFAULT 0)''')
    conn.commit()
    conn.close()

def get_saldo(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT saldo FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

def add_saldo(user_id, valor):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (id, saldo) VALUES (?, 0)", (user_id,))
    cursor.execute("UPDATE users SET saldo = saldo + ? WHERE id = ?", (valor, user_id))
    conn.commit()
    conn.close()

# --- 3. COMANDOS PRINCIPAIS ---

@bot.message_handler(commands=['start'])
def start(message):
    init_db()
    user_id = message.from_user.id
    add_saldo(user_id, 0)
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("📲 Comprar Número", callback_data="comprar_num"))
    markup.add(telebot.types.InlineKeyboardButton("💰 Ver Saldo", callback_data="ver_saldo"))
    markup.add(telebot.types.InlineKeyboardButton("💳 Recarregar", callback_data="recarregar"))
    
    bot.send_message(message.chat.id, "👋 Bem-vindo ao FynterBot!\nO que deseja fazer?", reply_markup=markup)

@bot.message_handler(commands=['setar'])
def setar(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        _, target_id, valor = message.text.split()
        add_saldo(int(target_id), float(valor))
        bot.reply_to(message, f"✅ €{valor} adicionados ao ID {target_id}")
    except:
        bot.reply_to(message, "⚠️ Use: /setar ID VALOR")

# --- 4. CALLBACKS (BOTÕES) ---

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    
    if call.data == "ver_saldo":
        saldo = get_saldo(user_id)
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, f"💎 Seu saldo atual: €{saldo:.2f}")

    elif call.data == "recarregar":
        texto = (
            "💳 *RECARGA INTERNACIONAL (REVOLUT)*\n\n"
            "Pague com cartão brasileiro. O banco converte para Euros!\n\n"
            "1️⃣ Clique em 'Pagar Agora'.\n"
            "2️⃣ Insira o valor em Euros (€).\n"
            f"3️⃣ Na nota (Add note), escreva seu ID: `{user_id}`\n\n"
            "⚠️ Envie o comprovante ao suporte após pagar."
        )
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🔗 Pagar Agora", url="https://revolut.me/goncalom35"))
        markup.add(telebot.types.InlineKeyboardButton("👨‍💻 Suporte", url="https://t.me/portugam50"))
        bot.edit_message_text(texto, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "comprar_num":
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🇧🇷 Brasil - €1.50", callback_data="buy_73"))
        markup.add(telebot.types.InlineKeyboardButton("🇵🇹 Portugal - €2.00", callback_data="buy_19"))
        bot.edit_message_text("Selecione o país:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("buy_"):
        pais_id = call.data.split("_")[1]
        saldo = get_saldo(user_id)
        preco = 1.50
        
        if saldo >= preco:
            url = f"https://api.grizzlysms.com/stubs/handler_api.php?api_key={GRIZZLY_KEY}&action=getNumber&service=tg&country={pais_id}"
            try:
                res = requests.get(url).text
                if "ACCESS_NUMBER" in res:
                    _, order_id, numero = res.split(":")
                    add_saldo(user_id, -preco)
                    markup = telebot.types.InlineKeyboardMarkup()
                    markup.add(telebot.types.InlineKeyboardButton("🔄 Checar SMS", callback_data=f"chk_{order_id}"))
                    bot.edit_message_text(f"✅ Número: `{numero}`\nAguardando SMS...", 
                                          call.message.chat.id, call.message.message_id, reply_markup=markup)
                else:
                    bot.answer_callback_query(call.id, f"Erro: {res}", show_alert=True)
            except:
                bot.answer_callback_query(call.id, "Erro de conexão API.")
        else:
            bot.answer_callback_query(call.id, "❌ Sem saldo!", show_alert=True)

    elif call.data.startswith("chk_"):
        order_id = call.data.split("_")[1]
        url = f"https://api.grizzlysms.com/stubs/handler_api.php?api_key={GRIZZLY_KEY}&action=getStatus&id={order_id}"
        res = requests.get(url).text
        if "STATUS_OK" in res:
            codigo = res.split(":")[1]
            bot.edit_message_text(f"✅ Seu código: `{codigo}`", call.message.chat.id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "⏳ Aguardando...")

# --- 5. LIGAR ---
if __name__ == "__main__":
    init_db()
    bot.infinity_polling()
