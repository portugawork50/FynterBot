@bot.message_handler(commands=['setar'])
def set_saldo_manual(message):
    # Verifica se quem enviou o comando é você
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Você não tem permissão para usar este comando.")
        return

    try:
        # O comando deve ser: /setar ID VALOR
        # Exemplo: /setar 987654321 10.50
        dados = message.text.split()
        if len(dados) != 3:
            bot.reply_to(message, "⚠️ Use o formato: `/setar ID VALOR`", parse_mode="Markdown")
            return

        target_id = int(dados[1])
        valor = float(dados[2])

        add_saldo(target_id, valor)
        
        bot.send_message(message.chat.id, f"✅ Sucesso! Adicionado € {valor:.2f} ao usuário {target_id}.")
        # Avisa o cliente automaticamente
        try:
            bot.send_message(target_id, f"💰 Seu pagamento foi confirmado! Adicionamos € {valor:.2f} ao seu saldo.")
        except:
            pass # Se o cliente bloqueou o bot, ignora o erro

    except Exception as e:
        bot.reply_to(message, f"❌ Erro ao processar: {e}")
