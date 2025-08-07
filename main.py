import telebot
import requests
import time
import logging
import threading
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot.apihelper import ApiException

BOT_TOKEN = '7953282622:AAGirPmwMcUmZ0VSH8iijGp8Bw-sWWDyass'

# Configuração do LOG
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

bot = telebot.TeleBot(BOT_TOKEN)

API_URLS = [
    "https://likes.ffgarena.cloud/api/v2/likes?uid={uid}&amount_of_likes=100&auth=vortex&region=ind",
    "https://likes.ffgarena.cloud/api/v2/likes?uid={uid}&amount_of_likes=100&auth=vortex&region=br"
]

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Online ✅"

def developer_button():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("👑 DESENVOLVEDOR", url="https://t.me/VorteXModi"))
    return markup

def safe_edit_message_text(new_text, chat_id, message_id, reply_markup=None):
    try:
        bot.edit_message_text(new_text, chat_id=chat_id, message_id=message_id, reply_markup=reply_markup)
    except ApiException as e:
        if "message is not modified" in str(e):
            pass
        else:
            logging.error(f"Erro ao editar mensagem: {e}")

@bot.message_handler(commands=['start'])
def start(message):
    logging.info(f"Comando /start recebido de {message.from_user.id} ({message.from_user.username})")
    if message.chat.type == 'private':
        bot.reply_to(message, "❌ Este bot só está disponível no grupo: https://t.me/vortexlikes", reply_markup=developer_button())
    else:
        bot.reply_to(message, "Use o comando /like seguido do ID do jogador.\nExemplo: /like 123456789", reply_markup=developer_button())

@bot.message_handler(commands=['like'])
def like_command(message):
    logging.info(f"Comando /like recebido de {message.from_user.id} ({message.from_user.username}): {message.text}")
    if message.chat.type == 'private':
        bot.reply_to(message, "❌ Este bot só está disponível no grupo: https://t.me/vortexlikes", reply_markup=developer_button())
        return

    try:
        uid = message.text.split()[1]
    except IndexError:
        bot.reply_to(message, "⚠️ Você precisa enviar o comando assim:\n/like [ID]", reply_markup=developer_button())
        return

    progress_msg = bot.send_message(message.chat.id, "🔄 Buscando dados no servidor... 10%", reply_markup=developer_button())

    try:
        time.sleep(1)
        safe_edit_message_text("🔄 Validando UID... 30%", chat_id=message.chat.id, message_id=progress_msg.message_id, reply_markup=developer_button())

        found = False
        player_data = None

        for api_url in API_URLS:
            time.sleep(1)
            safe_edit_message_text("🔄 Enviando solicitação de likes... 60%", chat_id=message.chat.id, message_id=progress_msg.message_id, reply_markup=developer_button())
            response = requests.get(api_url.format(uid=uid))
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 200:
                    player_data = data
                    found = True
                    break
            elif response.status_code == 404:
                continue

        bot.delete_message(message.chat.id, progress_msg.message_id)

        if found:
            nickname = player_data.get('nickname', 'Desconhecido')
            level = player_data.get('level', 'Desconhecido')
            region = player_data.get('region', 'Desconhecido')
            likes_antes = player_data.get('likes_antes', 0)
            likes_depois = player_data.get('likes_depois', 0)
            likes_sent = int(player_data.get('sent', '0 likes').split()[0])

            if likes_sent == 0:
                final_text = f"""❌ UID já recebeu likes hoje! 🚫

• Nome: {nickname}
• UID: {uid}
• Nível: {level}
• Região: {region}
"""
            else:
                final_text = f"""LIKES ENVIADOS COM SUCESSO! ✨

• Nome: {nickname}
• UID: {uid}
• Nível: {level}
• Região: {region}

Likes enviados:
• Likes Antes: {likes_antes}
• Likes Agora: {likes_depois}
"""
            logging.info(f"Likes enviados para UID {uid} ({nickname}) pelo usuário {message.from_user.id}")
        else:
            final_text = "❌ UID NÃO ENCONTRADO! 🚫"
            logging.info(f"UID {uid} não encontrado pelo usuário {message.from_user.id}")

        bot.send_message(message.chat.id, final_text, reply_markup=developer_button())

    except Exception as e:
        logging.error(f"Erro ao processar /like para {message.from_user.id}: {e}")
        bot.reply_to(message, "❌ Ocorreu um erro interno. Tente novamente mais tarde.", reply_markup=developer_button())

def run_bot():
    logging.info("Iniciando bot...")
    bot.infinity_polling()

if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    app.run(host="0.0.0.0", port=10000)
