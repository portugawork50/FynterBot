import os
import telebot
import requests
import sqlite3

# --- 1. CONFIGURAÇÕES INICIAIS ---
TOKEN = "8338751670:AAEe17MTCw2uEBCGz2S68eXkdlpHLgf1Gho"
ADMIN_ID = 8647771753
GRIZZLY_KEY = os.getenv("GRIZZLY_API_KEY")

bot = telebot.TeleBot(TOKEN)

# --- 2. BANCO DE DADOS (Saldo dos Clientes) ---
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

# --- 3. COMANDOS DE ADMINISTRADOR ---

@bot.message_handler(commands=['setar'])
def setar(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        partes = message.text.split()
        target_id = int(partes[1])
        valor = float(partes[2])
        add_saldo(target_id, valor)
        bot.reply_to(message, f"✅ Adicionado €{valor:.2f} ao usuário {target_id}!")
    except:
        bot.reply_to(message, "⚠️ Erro! Use: `/setar ID VALOR`", parse_mode="Markdown")

# --- 4. COMANDOS DE USUÁRIO ---

@bot.message_handler(commands=['start'])
def start(message):
    init_db()
    user_id = message.from_user.id
    add_saldo(user_id, 0)
    
    boas_vindas = (
        f"🚀 *BEM-VINDO AO FYNTERBOT!*\n\n"
        f"Seu ID: `{user_id}`\n"
        "Aqui você compra números virtuais para Telegram de forma rápida.\n\n"
        "💳 *Como funciona?*\n"
        "1. Recarregue seu saldo via Revolut.\n"
        "2. Escolha o país do número.\n"
        "3. Receba o SMS direto aqui no bot!\n\n"
        "👇 Escolha uma opção abaixo:"
    )
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("📲 COMPRAR NÚMERO", callback_data="comprar_num"))
    markup.row(
        telebot.types.InlineKeyboardButton("💰 MEU SALDO", callback_data="ver_saldo"),
        telebot.types.InlineKeyboardButton("💳 RECARREGAR", callback_data="recarregar")
    )
    
    bot.send_message(message.chat.id, boas_vindas, reply_markup=markup, parse_mode="Markdown")

# --- 5. LÓGICA DOS BOTÕES (CALLBACKS) ---

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id

    if call.data == "ver_saldo":
        saldo = get_saldo(user_id)
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, f"💎 Seu saldo atual: *€{saldo:.2f}*", parse_mode="Markdown")

    elif call.data == "recarregar":
        texto = (
            "💳 *RECARGA INTERNACIONAL (REVOLUT)*\n\n"
            "Pague com cartão brasileiro. O banco converte para Euros!\n\n"
            "--- *PASSO A PASSO* ---\n"
            "1️⃣ Clique em 'Pagar Agora' abaixo.\n"
            "2️⃣ Insira o valor em Euros (€).\n"
            f"3️⃣ Na nota (Add note), escreva seu ID: `{user_id}`\n\n"
            "⚠️ *Importante:* Após pagar, envie o comprovante ao suporte."
        )
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🔗 Pagar Agora (Revolut)", url="https://revolut.me/goncalom35"))
        markup.add(telebot.types.InlineKeyboardButton("👨‍💻 Enviar Comprovante", url="https://t.me/portugam50"))
        bot.edit_message_text(texto, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "comprar_num":
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🇧🇷 Brasil - €1.50", callback_data="buy_73"))
        markup.add(telebot.types.InlineKeyboardButton("🇵🇹 Portugal - €2.00", callback_data="buy_19"))
        markup.add(telebot.types.InlineKeyboardButton("🇺🇸 EUA - €1.50", callback_data="buy_187"))
        markup.add(telebot.types.InlineKeyboardButton("🇦🇴 Angola - €2.00", callback_data="buy_57"))
        markup.add(telebot.types.InlineKeyboardButton("🇮🇩 Indonésia - €1.00", callback_data="buy_6"))
        bot.edit_message_text("🌍 *ESCOLHA O PAÍS DO NÚMERO:*", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data.startswith("buy_"):
        pais_id = call.data.split("_")[1]
        saldo = get_saldo(user_id)
        
        # Preços definidos (podes ajustar aqui)
        precos = {"73": 1.50, "19": 2.00, "187": 1.50, "57": 2.00, "6": 1.00}
        preco_venda = precos.get(pais_id, 2.00)
        
        if saldo >= preco_venda:
            # Pedir número ao Grizzly
            url = f"https://api.grizzlysms.com/stubs/handler_api.php?api_key={GRIZZLY_KEY}&action=getNumber&service=tg&country={pais_id}"
            try:
                res = requests.get(url).text
                if "ACCESS_NUMBER" in res:
                    _, order_id, numero = res.split(":")
                    add_saldo(user_id, -preco_venda) # Deduz saldo
                    
                    markup = telebot.types.InlineKeyboardMarkup()
                    markup.add(telebot.types.InlineKeyboardButton("🔄 Checar SMS", callback_data=f"chk_{order_id}"))
                    bot.edit_message_text(f"✅ *NÚMERO GERADO!*\n\n📱 Número: `{numero}`\n🆔 Pedido: `{order_id}`\n\n_Copie o número e peça o SMS no Telegram. Depois clique no botão abaixo._", 
                                          call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
                else:
                    bot.answer_callback_query(call.id, f"❌ Erro Grizzly: {res}", show_alert=True)
            except:
                bot.answer_callback_query(call.id, "❌ Erro de conexão com o servidor.")
        else:
            bot.answer_callback_query(call.id, "❌ Saldo insuficiente! Recarregue via Revolut.", show_alert=True)

    elif call.data.startswith("chk_"):
        order_id = call.data.split("_")[1]
        url = f"https://api.grizzlysms.com/stubs/handler_api.php?api_key={GRIZZLY_KEY}&action=getStatus&id={order_id}"
        try:
            res = requests.get(url).text
            if "STATUS_OK" in res:
                codigo = res.split(":")[1]
                bot.edit_message_text(f"✅ *CÓDIGO RECEBIDO!*\n\n🔑 Seu código é: `{codigo}`", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
            elif "STATUS_WAIT_CODE" in res:
                bot.answer_callback_query(call.id, "⏳ SMS ainda não chegou. Aguarde um pouco e tente de novo.", show_alert=True)
            else:
                bot.answer_callback_query(call.id, f"Status: {res}")
        except:
            bot.answer_callback_query(call.id, "Erro ao verificar SMS.")

# --- 6. INICIALIZAÇÃO ---
if __name__ == "__main__":
    init_db()
    print("FynterBot Online!")
    bot.infinity_polling()
