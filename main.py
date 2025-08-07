import telebot
import requests
import logging
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
import threading

BOT_TOKEN = '7953282622:AAGirPmwMcUmZ0VSH8iijGp8Bw-sWWDyass'
bot = telebot.TeleBot(BOT_TOKEN)

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

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
        bot.reply_to(message, "❌ Este bot só está disponível no grupo: https://t.me/vortexlikes", reply_markup=developer_button())

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
                bot.edit_message_text(chat_id=message.chat.id, message_id=progress_msg.message_id, text="❌ UID já recebeu likes hoje! 🚫", reply_markup=developer_button())
                return
            bot.edit_message_text(chat_id=message.chat.id, message_id=progress_msg.message_id, text=f"LIKES ENVIADOS COM SUCESSO! ✨\n\n• Nome: {data.get('nickname')}\n• UID: {uid}\n• Nível: {data.get('level')}\n• Região: {data.get('region')}\n\nLikes enviados:\n• Likes Antes: {data.get('likes_antes')}\n• Likes Agora: {data.get('likes_depois')}", reply_markup=developer_button())
            break
        if not found:
            bot.edit_message_text(chat_id=message.chat.id, message_id=progress_msg.message_id, text="❌ UID NÃO ENCONTRADO! 🚫", reply_markup=developer_button())
    except Exception as e:
        logging.error(f"Erro ao processar /like para {message.from_user.id}: {e}")
        bot.reply_to(message, "❌ Ocorreu um erro interno. Tente novamente mais tarde.", reply_markup=developer_button())

@bot.message_handler(commands=['info'])
def info_command(message):
    if message.chat.type == 'private':
        bot.reply_to(message, "❌ Este bot só está disponível no grupo: https://t.me/vortexlikes", reply_markup=developer_button())
        return
    try:
        uid = message.text.split()[1]
    except IndexError:
        bot.reply_to(message, "⚠️ Você precisa enviar o comando assim:\n/info [ID]", reply_markup=developer_button())
        return
    try:
        progress_msg = bot.reply_to(message, "🔄 Buscando informações...", reply_markup=developer_button())
        response = requests.get(INFO_API_URL.format(uid=uid))
        if response.status_code != 200:
            bot.delete_message(message.chat.id, progress_msg.message_id)
            bot.reply_to(message, "❌ UID NÃO ENCONTRADO! 🚫", reply_markup=developer_button())
            return
        data = response.json()
        basicInfo = data.get("basicInfo", {})
        clanInfo = data.get("clanBasicInfo", {})
        petInfo = data.get("petInfo", {})
        creditInfo = data.get("creditScoreInfo", {})
        nickname = basicInfo.get("nickname", "Desconhecido")
        level = basicInfo.get("level", "N/A")
        region = data.get("_resolved_region", "N/A")
        likes = basicInfo.get("liked", 0)
        br_rank = basicInfo.get("rank", "N/A")
        cs_rank = basicInfo.get("csRank", "N/A")
        exp = basicInfo.get("exp", "N/A")
        title_id = basicInfo.get("title", "N/A")
        clan_name = clanInfo.get("clanName", "Sem Clã")
        clan_level = clanInfo.get("clanLevel", "N/A")
        clan_members = f"{clanInfo.get('memberNum', 0)}/{clanInfo.get('capacity', 0)}"
        pet_name = petInfo.get("name", "N/A")
        pet_id = petInfo.get("id", "N/A")
        pet_level = petInfo.get("level", "N/A")
        credit_score = creditInfo.get("creditScore", "N/A")
        reward_state = creditInfo.get("rewardState", "N/A")
        final_text = f"""📊 INFORMAÇÕES DO JOGADOR:

• Nome: {nickname}
• UID: {uid}
• Nível: {level}
• Região: {region}
• Likes: {likes}
• BR Rank: {br_rank}
• CS Rank: {cs_rank}
• EXP: {exp}

🎖️ CLÃ:
• Nome: {clan_name}
• Nível: {clan_level}
• Membros: {clan_members}

🐶 PET:
• Nome: {pet_name}
• ID: {pet_id}
• Nível: {pet_level}

🛡️ CRÉDITO:
• Score: {credit_score}
• Recompensa: {reward_state}

🎯 TÍTULO:
• ID: {title_id}
"""
        profile_img_url = PROFILE_IMG_URL.format(uid=uid)
        bot.delete_message(message.chat.id, progress_msg.message_id)
        bot.send_photo(message.chat.id, photo=profile_img_url, caption=final_text, reply_markup=developer_button())
    except Exception as e:
        logging.error(f"Erro ao processar /info para {message.from_user.id}: {e}")
        bot.reply_to(message, "❌ Ocorreu um erro interno. Tente novamente mais tarde.", reply_markup=developer_button())

def run_bot():
    bot.infinity_polling()

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Online"

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=10000)
