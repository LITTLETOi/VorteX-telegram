import telebot
import aiohttp
import asyncio
import time
import threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "7953282622:AAF4cPFrxAwG-xH-zVsxF11XLP2o5lbKYIs"
like_request_tracker = {}

VIP_USERS = {4930014286}

bot = telebot.TeleBot(BOT_TOKEN)

def developer_button():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("👑 DESENVOLVEDOR", url="https://t.me/VorteXModi"))
    return markup

async def send_like_request(uid):
    urls = [
        f"https://likes.ffgarena.cloud/api/v2/likes?uid={uid}&amount_of_likes=100&auth=vortex&region=br",
        f"https://likes.ffgarena.cloud/api/v2/likes?uid={uid}&amount_of_likes=100&auth=vortex&region=ind"
    ]

    async with aiohttp.ClientSession() as session:
        for url in urls:
            try:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") != 404:
                            return data  # Sucesso
                    elif response.status == 404:
                        data = await response.json()
                        if data.get("error") == "PLAYER_NOT_FOUND":
                            continue  # Tenta próxima região
            except (aiohttp.ClientError, asyncio.TimeoutError):
                return {"status": 500, "error": "API_ERROR"}

    return {"status": 404, "error": "PLAYER_NOT_FOUND"}  # Se ambas falharem

def process_like(message, uid):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if user_id not in VIP_USERS and like_request_tracker.get(user_id, False):
        bot.reply_to(
            message,
            "⚠️ Você já atingiu o limite diário de likes! ⏳ Tente novamente amanhã.",
            reply_markup=developer_button()
        )
        return

    processing_msg = bot.reply_to(message, "⏳ Processando sua solicitação... 🔄", reply_markup=developer_button())

    time.sleep(1)
    bot.edit_message_text("🔄 Buscando dados no servidor... 10%", chat_id, processing_msg.message_id, reply_markup=developer_button())
    time.sleep(1)
    bot.edit_message_text("🔄 Validando UID... 30%", chat_id, processing_msg.message_id, reply_markup=developer_button())
    time.sleep(1)
    bot.edit_message_text("🔄 Enviando solicitação de likes... 60%", chat_id, processing_msg.message_id, reply_markup=developer_button())
    time.sleep(1)
    bot.edit_message_text("🔄 Quase lá... 90%", chat_id, processing_msg.message_id, reply_markup=developer_button())

    # Executar a função assíncrona
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    response = loop.run_until_complete(send_like_request(uid))

    # Tratamento de erros da API
    if response.get("status") == 404 and response.get("error") == "PLAYER_NOT_FOUND":
        bot.edit_message_text(
            f"❌ Não foi possível encontrar o usuário com UID `{uid}`.",
            chat_id,
            processing_msg.message_id,
            parse_mode="Markdown",
            reply_markup=developer_button()
        )
        return

    elif response.get("status") != 200:
        bot.edit_message_text(
            "🚨 ERRO NA API! ⚒️ Estamos corrigindo, por favor aguarde algumas horas. ⏳",
            chat_id,
            processing_msg.message_id,
            reply_markup=developer_button()
        )
        return

    # Dados da resposta
    sent_raw = response.get('sent', 0)
    try:
        sent = int(sent_raw)
    except (ValueError, TypeError):
        sent = 0  # Se não for um número válido, trata como 0

    nickname = response.get('nickname', 'N/A')
    region = response.get('region', 'N/A').upper()

    # CHECAGEM DEFINITIVA: SE SENT == 0 PARA AQUI
    if sent == 0:
        bot.edit_message_text(
            f"• ❌ UID JÁ RECEBEU LIKES HOJE! 🚫\n\n"
            f"• Nome: {nickname}\n"
            f"• UID: {uid}\n"
            f"• Região: {region}",
            chat_id,
            processing_msg.message_id,
            reply_markup=developer_button()
        )
        return

    # Se likes foram enviados (sent > 0)
    if user_id not in VIP_USERS:
        like_request_tracker[user_id] = True  # Marcar uso diário

    level = response.get('level', 'N/A')
    exp = response.get('exp', 'N/A')
    likes_antes = response.get('likes_antes', 'N/A')
    likes_depois = response.get('likes_depois', 'N/A')

    try:
        photos = bot.get_user_profile_photos(user_id)
        if photos.total_count > 0:
            file_id = photos.photos[0][-1].file_id
            bot.edit_message_media(
                chat_id=chat_id,
                message_id=processing_msg.message_id,
                media=telebot.types.InputMediaPhoto(
                    file_id,
                    caption=f"✅ **Likes enviados com sucesso!**\n"
                            f"🔹 **UID:** `{uid}`\n"
                            f"🔸 **Apelido:** `{nickname}`\n"
                            f"🌍 **Região:** `{region}`\n"
                            f"🎮 **Nível:** `{level}` | 🆙 **EXP:** `{exp}`\n"
                            f"❤️ **Likes Antes:** `{likes_antes}`\n"
                            f"💖 **Likes Depois:** `{likes_depois}`\n"
                            f"🚀 **{sent} likes**",
                    parse_mode="Markdown"
                ),
                reply_markup=developer_button()
            )
            return
    except:
        pass

    bot.edit_message_text(
        chat_id=chat_id,
        message_id=processing_msg.message_id,
        text=f"✅ **Likes enviados com sucesso!**\n"
             f"🔹 **UID:** `{uid}`\n"
             f"🔸 **Apelido:** `{nickname}`\n"
             f"🌍 **Região:** `{region}`\n"
             f"🎮 **Nível:** `{level}` | 🆙 **EXP:** `{exp}`\n"
             f"❤️ **Likes Antes:** `{likes_antes}`\n"
             f"💖 **Likes Depois:** `{likes_depois}`\n"
             f"🚀 **{sent} likes**",
        parse_mode="Markdown",
        reply_markup=developer_button()
    )

@bot.message_handler(commands=['like'])
def handle_like(message):
    if message.chat.type == "private":
        return

    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(
            message,
            "❌ Formato incorreto! Use: `/like {uid}`\n📌 Exemplo: `/like 1640556162`",
            parse_mode="Markdown",
            reply_markup=developer_button()
        )
        return

    uid = args[1]

    if not uid.isdigit():
        bot.reply_to(
            message,
            "⚠️ UID inválido! Deve conter apenas números.\n📌 Exemplo: `/like 1640556162`",
            reply_markup=developer_button()
        )
        return

    threading.Thread(target=process_like, args=(message, uid)).start()

bot.polling(none_stop=True)
