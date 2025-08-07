import telebot
import requests
import logging
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
import threading

# Substitua aqui pelo seu token novo
BOT_TOKEN = '7953282622:AAGpnNH78dfht2G8KCjJKVirbWwMN7cnTIY'

bot = telebot.TeleBot(BOT_TOKEN)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

API_LIKES = [
    "https://likes.ffgarena.cloud/api/v2/likes?uid={uid}&amount_of_likes=100&auth=vortex&region=ind",
    "https://likes.ffgarena.cloud/api/v2/likes?uid={uid}&amount_of_likes=100&auth=vortex&region=br"
]

INFO_API_URL = "https://rawthug.onrender.com/info?uid={uid}"
PROFILE_IMG_URL = "https://generatethug.onrender.com/profile?uid={uid}"

def developer_button():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("👑 DESENVOLVEDOR", url="https://t.me/VorteXModi"))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.type == 'private':
        bot.reply_to(
            message,
            "❌ Este bot só está disponível no grupo: https://t.me/vortexlikes",
            reply_markup=developer_button()
        )

@bot.message_handler(commands=['like'])
def like_command(message):
    if message.chat.type == 'private':
        bot.reply_to(
            message,
            "❌ Este bot só está disponível no grupo: https://t.me/vortexlikes",
            reply_markup=developer_button()
        )
        return
    try:
        uid = message.text.split()[1]
    except IndexError:
        bot.reply_to(
            message,
            "⚠️ Você precisa enviar o comando assim:\n/like [ID]",
            reply_markup=developer_button()
        )
        return
    try:
        progress_msg = bot.reply_to(message, "🔄 Buscando dados no servidor... 10%", reply_markup=developer_button())
        found = False
        for url in API_LIKES:
            res = requests.get(url.format(uid=uid))
            if res.status_code != 200:
                continue
            data = res.json()
            if data.get("status") == 404:
                continue
            found = True
            if data.get("sent") == "0 likes":
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=progress_msg.message_id,
                    text="❌ UID já recebeu likes hoje! 🚫",
                    reply_markup=developer_button()
                )
                return
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=progress_msg.message_id,
                text=(
                    f"LIKES ENVIADOS COM SUCESSO! ✨\n\n"
                    f"• Nome: {data.get('nickname')}\n"
                    f"• UID: {uid}\n"
                    f"• Nível: {data.get('level')}\n"
                    f"• Região: {data.get('region')}\n\n"
                    f"Likes enviados:\n"
                    f"• Likes Antes: {data.get('likes_antes')}\n"
                    f"• Likes Agora: {data.get('likes_depois')}"
                ),
                reply_markup=developer_button()
            )
            break
        if not found:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=progress_msg.message_id,
                text="❌ UID NÃO ENCONTRADO! 🚫",
                reply_markup=developer_button()
            )
    except Exception as e:
        logging.error(f"Erro ao processar /like para {message.from_user.id}: {e}")
        bot.reply_to(
            message,
            "❌ Ocorreu um erro interno. Tente novamente mais tarde.",
            reply_markup=developer_button()
        )

@bot.message_handler(commands=['info'])
def info_command(message):
    if message.chat.type == 'private':
        bot.reply_to(
            message,
            "❌ Este bot só está disponível no grupo.",
            reply_markup=developer_button()
        )
        return
    try:
        uid = message.text.split()[1]
    except IndexError:
        bot.reply_to(
            message,
            "⚠️ Use: /info [UID]",
            reply_markup=developer_button()
        )
        return
    try:
        response = requests.get(f"https://rawthug.onrender.com/info?uid={uid}")
        response.raise_for_status()
        data = response.json()
        logging.info(f"Resposta API /info: {data}")
        nickname = data.get("basicInfo", {}).get("nickname", "N/A")
        level = data.get("basicInfo", {}).get("level", "N/A")
        region = data.get("_resolved_region", "N/A")
        likes = data.get("basicInfo", {}).get("liked", 0)
        final_text = (
            f"📊 INFORMAÇÕES DO JOGADOR:\n\n"
            f"• Nome: {nickname}\n"
            f"• UID: {uid}\n"
            f"• Nível: {level}\n"
            f"• Região: {region}\n"
            f"• Likes: {likes}"
        )
        bot.reply_to(message, final_text, reply_markup=developer_button())
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error no /info: {http_err}")
        bot.reply_to(
            message,
            "❌ Erro HTTP ao buscar informações.",
            reply_markup=developer_button()
        )
    except Exception as e:
        logging.error(f"Erro no /info: {e}")
        bot.reply_to(
            message,
            "❌ Ocorreu um erro interno. Tente novamente mais tarde.",
            reply_markup=developer_button()
        )

def run_bot():
    bot.infinity_polling()

from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Online"

if __name__ == "__main__":
    import threading
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=10000)
