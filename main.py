    elif call.data == "recarregar":
        # --- SEUS LINKS CONFIGURADOS ---
        meu_link_revolut = "https://revolut.me/goncalom35" 
        meu_suporte_telegram = "https://t.me/portugam50"
        
        texto = (
            "💳 *RECARGA INTERNACIONAL (REVOLUT)*\n\n"
            "Pague com o seu cartão bancário ou saldo Revolut. O valor é convertido para Euros automaticamente!\n\n"
            "--- *PASSO A PASSO* ---\n"
            "1️⃣ Clique no botão **'Pagar Agora'** abaixo.\n"
            "2️⃣ Insira o valor em **Euros** (€) que deseja carregar.\n"
            f"3️⃣ Na nota (Add note), escreva obrigatoriamente o seu ID: `{user_id}`\n\n"
            "--- *INFORMAÇÕES* ---\n"
            "• O saldo é creditado manualmente após verificação.\n"
            "• Envie o comprovante para o suporte para acelerar o processo.\n\n"
            "⚠️ *Taxas de conversão e IOF dependem do seu banco emissor.*"
        )
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🔗 Pagar Agora (Revolut)", url=meu_link_revolut))
        markup.add(telebot.types.InlineKeyboardButton("👨‍💻 Enviar Comprovante", url=meu_suporte_telegram))
        
        bot.edit_message_text(texto, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
