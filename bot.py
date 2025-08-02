import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests

BOT_TOKEN = "8191885274:AAGBH9oKmlryZA0NE59SATncnpc3fd5or8c"
bot = telebot.TeleBot(BOT_TOKEN)

AUTHORIZED_OWNERS = [8183673253]
ALLOWED_GROUP_IDS = [-4781844651]

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

def is_group_allowed(chat_id):
    return chat_id in ALLOWED_GROUP_IDS

def restricted_group(func):
    def wrapper(msg):
        if msg.chat.type in ["group", "supergroup"]:
            if not is_group_allowed(msg.chat.id):
                return safe_reply(msg, "❌ Este bot só funciona em grupos autorizados.")
        elif msg.chat.type == "private":
            if not is_owner(msg.from_user.id):
                return safe_reply(msg, "❌ Você não tem permissão para usar este bot.")
        return func(msg)
    return wrapper

@bot.message_handler(commands=['like'])
@restricted_group
def like_cmd(msg):
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
            "⚠️ Erro ao comunicar com o servidor de likes.",
            chat_id=status_msg.chat.id,
            message_id=status_msg.message_id,
            parse_mode="Markdown"
        )

    if data.get("status") == 200:
        sent_likes = str(data.get("sent", "0"))
        sent_count = int(''.join(filter(str.isdigit, sent_likes)) or "0")

        if sent_count == 0:
            return bot.edit_message_text(
                "⚠️ Você atingiu o limite diário de likes.",
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
def get_id(msg):
    safe_reply(msg, f"🆔 Chat ID: `{msg.chat.id}`\n👤 User ID: `{msg.from_user.id}`", parse_mode="Markdown")

if __name__ == '__main__':
    print("Bot starting...")
    bot.infinity_polling()
