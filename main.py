@bot.message_handler(commands=['setar'])
def setar(message):
    user_id = message.from_user.id
    
    # Se não funcionar, o bot vai te dizer qual é o seu ID real
    if user_id != ADMIN_ID:
        bot.reply_to(message, f"❌ Acesso negado. Seu ID é {user_id}. Configure este ID no ADMIN_ID do código.")
        return

    try:
        # Divide a mensagem: /setar 123456 10.0
        partes = message.text.split()
        if len(partes) != 3:
            bot.reply_to(message, "⚠️ Use: `/setar ID VALOR` (Ex: /setar 11223344 5.0)", parse_mode="Markdown")
            return

        target_id = int(partes[1])
        valor = float(partes[2].replace(',', '.')) # Aceita 5,50 ou 5.50

        add_saldo(target_id, valor)
        bot.reply_to(message, f"✅ Adicionado €{valor} ao usuário {target_id}!")
        
        # Tenta avisar o cliente
        try:
            bot.send_message(target_id, f"💰 Seu saldo foi atualizado! Novo valor adicionado: €{valor}")
        except:
            pass

    except Exception as e:
        bot.reply_to(message, f"❌ Erro técnico: {e}")
