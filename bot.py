import telebot
import requests
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = '7953282622:AAGirPmwMcUmZ0VSH8iijGp8Bw-sWWDyass'

bot = telebot.TeleBot(BOT_TOKEN)

API_URLS = [
    "https://likes.ffgarena.cloud/api/v2/likes?uid={uid}&amount_of_likes=100&auth=vortex&region=ind",
    "https://likes.ffgarena.cloud/api/v2/likes?uid={uid}&amount_of_likes=100&auth=vortex&region=br"
]

def developer_button():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("👑 DESENVOLVEDOR", url="https://t.me/VorteXModi"))
    return markup

def get_user_photo_file_id(user_id):
    photos = bot.get_user_profile_photos(user_id)
    if photos.total_count > 0:
        photo = photos.photos[0][-1]
        return photo.file_id
    return None

@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.type == 'private':
        bot.reply_to(message, "❌ Este bot só está disponível no grupo: https://t.me/vortexlikes", reply_markup=developer_button())
    else:
        bot.reply_to(message, "Use o comando /like seguido do ID do jogador.\nExemplo: /like 123456789", reply_markup=developer_button())

@bot.message_handler(commands=['like'])
def like_command(message):
    if message.chat.type == 'private':
        bot.reply_to(message, "❌ Este bot só está disponível no grupo: https://t.me/vortexlikes", reply_markup=developer_button())
        return

    try:
        uid = message.text.split()[1]
    except IndexError:
        bot.reply_to(message, "⚠️ Você precisa enviar o comando assim:\n/like [ID]", reply_markup=developer_button())
        return

    progress_msg = bot.send_message(message.chat.id, "🔄 Buscando dados no servidor... 10%", reply_markup=developer_button())

    time.sleep(1)
    bot.edit_message_text("🔄 Validando UID... 30%", chat_id=message.chat.id, message_id=progress_msg.message_id, reply_markup=developer_button())

    found = False
    player_data = None

    for api_url in API_URLS:
        time.sleep(1)
        bot.edit_message_text("🔄 Enviando solicitação de likes... 60%", chat_id=message.chat.id, message_id=progress_msg.message_id, reply_markup=developer_button())
        response = requests.get(api_url.format(uid=uid))
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 200:
                player_data = data
                found = True
                break
        elif response.status_code == 404:
            continue

    time.sleep(1)
    bot.edit_message_text("🔄 Quase lá... 90%", chat_id=message.chat.id, message_id=progress_msg.message_id, reply_markup=developer_button())

    photo_file_id = get_user_photo_file_id(message.from_user.id)

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
    else:
        final_text = "❌ UID NÃO ENCONTRADO! 🚫"

    bot.delete_message(message.chat.id, progress_msg.message_id)

    if photo_file_id:
        bot.send_photo(chat_id=message.chat.id, photo=photo_file_id, caption=final_text, reply_markup=developer_button())
    else:
        bot.send_message(message.chat.id, final_text, reply_markup=developer_button())

print("Bot rodando...")
bot.polling()
