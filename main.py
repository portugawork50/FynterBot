import telebot
from telebot import types

# --- CONFIGURAÇÕES ---
# Substitua pelo Token que o @BotFather te deu
TOKEN = 'SEU_TOKEN_AQUI' 

# IMPORTANTE: Coloque SEU ID numérico aqui (use o @userinfobot no Telegram para descobrir o seu)
ADMIN_ID = 000000000  

bot = telebot.TeleBot(TOKEN)

# Banco de dados simples em dicionário (Reinicia se o script parar)
# Dica: No futuro, use SQLite para não perder os saldos se o PC desligar.
users_balance = {}

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
    user_id = message.from_user.id
    if user_id not in users_balance:
        users_balance[user_id] = 0.0
    
    msg = (f"Olá {message.from_user.first_name}! 🤖\n\n"
           "Bem-vindo ao *FynterBot*.\n"
           "Aqui você gera números virtuais para SMS de +100 países instantaneamente.")
    bot.send_message(message.chat.id, msg, parse_mode="Markdown", reply_markup=main_menu())

@bot.message_handler(func=lambda message: message.text == "👤 MINHA CONTA")
def conta(message):
    saldo = users_balance.get(message.from_user.id, 0.0)
    msg = (f"👤 *Suas Informações:*\n\n"
           f"🆔 ID: `{message.from_user.id}`\n"
           f"💰 Saldo: *{saldo:.2f} €*")
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "💳 RECARREGAR")
def recarregar(message):
    texto = (
        "🌍 *RECARGA GLOBAL / GLOBAL RECHARGE* 🌍\n\n"
        "🟢 *OPÇÃO 1: USDT (Rede TRC20)*\n"
        "Ideal para pagamentos de qualquer país.\n"
        "🔹 *Endereço:* `TWxHqzW9MBAymeBnqx3WX6VyNUPKMmhoXU` \n"
        "_(Clique no endereço acima para copiar)_\n\n"
        "🔵 *OPÇÃO 2: MB WAY / IBAN (Portugal 🇵🇹)*\n"
        "Para pagamentos via MB WAY ou bancos, contacte o suporte:\n"
        "👉 @seu_usuario_pessoal\n\n"
        "⚠️ *IMPORTANTE:* Após realizar o pagamento, envie o comprovativo e o seu ID abaixo aqui no suporte:\n"
        f"🆔 *Seu ID:* `{message.from_user.id}`"
    )
    bot.send_message(message.chat.id, texto, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "🆘 SUPORTE")
def suporte(message):
    bot.send_message(message.chat.id, "Precisa de ajuda? Fale com o nosso administrador: @seu_usuario_pessoal")

# --- COMANDO DE ADMINISTRADOR PARA ADD SALDO ---
# Exemplo de uso: /add 12345678 5.00
@bot.message_handler(commands=['add'])
def add_balance(message):
    if message.from_user.id == ADMIN_ID:
        try:
            parts = message.text.split()
            target_id = int(parts[1])
            amount = float(parts[2])
            
            users_balance[target_id] = users_balance.get(target_id, 0.0) + amount
            
            bot.send_message(message.chat.id, f"✅ Sucesso! Adicionado {amount}€ ao ID {target_id}.")
            bot.send_message(target_id, f"🎉 *Saldo Adicionado!*\n\nSua recarga de *{amount}€* foi confirmada e já está disponível.", parse_mode="Markdown")
        except:
            bot.reply_to(message, "❌ Erro! Use o formato: `/add ID VALOR` (Ex: /add 12345 10.00)")
    else:
        bot.reply_to(message, "🚫 Apenas o dono do bot pode usar este comando.")

# --- INICIALIZAÇÃO ---
print("🤖 FynterBot está online e aguardando comandos...")
bot.infinity_polling()
