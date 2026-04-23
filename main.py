import telebot
from telebot import types

# --- CONFIGURAÇÕES ---
TOKEN = 'COLE_AQUI_O_TOKEN_DO_BOTFATHER'
ADMIN_ID = 123456789  # SUBSTITUA pelo seu ID do Telegram para poder usar comandos de admin
bot = telebot.TeleBot(TOKEN)

# Banco de dados temporário (em produção, use um arquivo .txt ou SQLite)
users_balance = {}

# --- FUNÇÕES AUXILIARES ---
def get_balance(user_id):
    return users_balance.get(user_id, 0.0)

# --- COMANDOS DE MENU ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("📱 GERAR NÚMERO")
    btn2 = types.KeyboardButton("💳 RECARREGAR")
    btn3 = types.KeyboardButton("👤 MINHA CONTA")
    btn4 = types.KeyboardButton("🆘 SUPORTE")
    markup.add(btn1, btn2, btn3, btn4)
    return markup

# --- HANDLERS ---

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
    saldo = get_balance(message.from_user.id)
    msg = (f"👤 *Suas Informações:*\n\n"
           f"🆔 ID: `{message.from_user.id}`\n"
           f"💰 Saldo: *{saldo:.2f} €*")
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "💳 RECARREGAR")
def recarregar(message):
    texto = (
        "🌍 *RECARGA GLOBAL / GLOBAL RECHARGE* 🌍\n\n"
        "🟢 *OPÇÃO 1: USDT (Rede TRC20)*\n"
        "Método instantâneo e sem fronteiras.\n"
        "🔹 *Endereço:* `TWxHqzW9MBAymeBnqx3WX6VyNUPKMmhoXU` \n"
        "_(Clique no endereço para copiar)_\n\n"
        "🔵 *OPÇÃO 2: MB WAY / IBAN (Portugal 🇵🇹)*\n"
        "Para pagamentos locais, contacte o suporte:\n"
        "👉 @seu_usuario_do_telegram\n\n"
        "⚠️ *IMPORTANTE:* Após o envio, mande o comprovativo e o seu ID abaixo para validarmos:\n"
        f"🆔 *Seu ID:* `{message.from_user.id}`"
    )
    bot.send_message(message.chat.id, texto, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "🆘 SUPORTE")
def suporte(message):
    bot.send_message(message.chat.id, "Precisa de ajuda? Fale com o administrador: @seu_usuario_do_telegram")

@bot.message_handler(func=lambda message: message.text == "📱 GERAR NÚMERO")
def gerar_numero(message):
    # Aqui você integraria com a API do provedor de SMS (ex: 5sim, SMS-Activate)
    bot.send_message(message.chat.id, "Escolha o serviço que deseja ativar: (Em breve integração
