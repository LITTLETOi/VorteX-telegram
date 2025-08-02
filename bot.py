import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import time
import json
import datetime
import os

BOT_TOKEN = "8191885274:AAFU3M-X5FFFSW5c2OjtWRZn6dvWAxvTgCA"
bot = telebot.TeleBot(BOT_TOKEN)

AUTHORIZED_OWNERS = [8183673253]
ALLOWED_GROUP_IDS = [-4781844651]

USER_DATA_FILE = "user_data.json"
vip_users = {}
regular_user_usage = set()

def load_user_data():
    global vip_users, regular_user_usage
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, 'r') as f:
                data = json.load(f)
                vip_users.update({int(k): v for k, v in data.get("vip_users", {}).items()})
                regular_user_usage.update(set(int(uid) for uid in data.get("regular_user_usage", [])))
        except:
            vip_users.clear()
            regular_user_usage.clear()
    else:
        vip_users.clear()
        regular_user_usage.clear()

def save_user_data():
    data_to_save = {
        "vip_users": vip_users,
        "regular_user_usage": list(regular_user_usage)
    }
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data_to_save, f, indent=4)

load_user_data()

def safe_reply(message, text, **kwargs):
    try:
        return bot.reply_to(message, text, **kwargs)
    except:
        try:
            return bot.send_message(message.chat.id, text, **kwargs)
        except:
            return None

def is_owner(user_id):
    return user_id in AUTHORIZED_OWNERS

def is_group_allowed(chat_id, user_id):
    return chat_id in ALLOWED_GROUP_IDS or is_owner(user_id)

def restricted_group(func):
    def wrapper(msg):
        if not is_group_allowed(msg.chat.id, msg.from_user.id):
            return safe_reply(msg, "❌ Este bot é restrito a grupos específicos.")
        return func(msg)
    return wrapper

@bot.message_handler(commands=['like'])
@restricted_group
def like_cmd(msg):
    if msg.chat.type == "private":
        return safe_reply(msg, "❌ O comando /like só pode ser usado em grupos.")

    user_id = msg.from_user.id
    parts = msg.text.strip().split()
    if len(parts) != 2:
        return safe_reply(msg, "❗ Uso correto: `/like uid`", parse_mode="Markdown")

    uid_to_like = parts[1]
    status_msg = safe_reply(msg, "🔄 Enviando like... Aguarde, por favor...")
    if status_msg is None:
        return

    url = f"https://likes.ffgarena.cloud/api/v2/likes?uid={uid_to_like}&amount_of_likes=100&auth=vortex"

    try:
        res = requests.get(url, timeout=20)
        res.raise_for_status()
        data = res.json()
    except:
        return bot.edit_message_text(
            "⚠️ Erro ao comunicar com o servidor de likes. Tente novamente mais tarde.",
            chat_id=status_msg.chat.id,
            message_id=status_msg.message_id,
            parse_mode="Markdown"
        )

    if data.get("status") == 200:
        sent_likes = str(data.get("sent", "0"))
        try:
            sent_count = int(''.join(filter(str.isdigit, sent_likes)))
        except:
            sent_count = 0

        if sent_count == 0:
            return bot.edit_message_text(
                "⚠️ Você atingiu o limite diário de likes. Tente novamente amanhã!",
                chat_id=status_msg.chat.id,
                message_id=status_msg.message_id,
                parse_mode="Markdown"
            )

        reply_text = (
            "✨ **VorteX Like!** ✨\n\n"
            f"👤 Nome: `{data.get('nickname', 'N/A')}`\n"
            f"🆔 UID: `{uid_to_like}`\n"
            f"🌎 Região: `{data.get('region', 'N/A')}`\n\n"
            f"👎 Likes antes: `{data.get('likes_antes', 'N/A')}`\n"
            f"👍 Likes depois: `{data.get('likes_depois', 'N/A')}`\n"
            f"✅ Likes adicionados pelo Bot: `{sent_likes}`"
        )

        keyboard = InlineKeyboardMarkup()
        button = InlineKeyboardButton(text="🛒 ADQUIRA O SEU", url="https://t.me/VorteXModi")
        keyboard.add(button)

        bot.edit_message_text(
            reply_text,
            chat_id=status_msg.chat.id,
            message_id=status_msg.message_id,
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    else:
        api_message = data.get("message", "A API reportou um problema.")
        bot.edit_message_text(
            f"⚠️ *{api_message}*",
            chat_id=status_msg.chat.id,
            message_id=status_msg.message_id,
            parse_mode="Markdown"
        )

@bot.message_handler(commands=['id'])
@restricted_group
def get_id(msg):
    safe_reply(msg, f"🆔 Chat ID: `{msg.chat.id}`\n👤 User ID: `{msg.from_user.id}`", parse_mode="Markdown")

if __name__ == '__main__':
    print("Bot starting...")
    bot.polling(timeout=60, long_polling_timeout=45, non_stop=True)
