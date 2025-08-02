import telebot
import requests
import time
import json
import datetime
import os

BOT_TOKEN = "8191885274:AAFAVYu0gYQxPZQ-sWERjn7TvEm12U1caeI"  # Substitua pelo token do seu bot
bot = telebot.TeleBot(BOT_TOKEN)

# Defina seu ID de usuário do Telegram e ID(s) dos grupos permitidos aqui
AUTHORIZED_OWNERS = [8183673253]  # Exemplo: seu user ID
ALLOWED_GROUP_IDS = [-4781844651]  # Exemplo: ID do grupo (supergrupo)

# --- Persistência de dados ---
USER_DATA_FILE = "user_data.json"
vip_users = {}  # {user_id: {...}}
regular_user_usage = set()  # Usuários regulares que já usaram /like

def load_user_data():
    global vip_users, regular_user_usage
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, 'r') as f:
                data = json.load(f)
                vip_users_loaded = data.get("vip_users", {})
                vip_users.update({int(k): v for k, v in vip_users_loaded.items()})
                regular_user_usage.update(set(int(uid) for uid in data.get("regular_user_usage", [])))
                print("User data loaded successfully.")
        except Exception as e:
            print(f"Error loading user data: {e}. Starting empty.")
            vip_users.clear()
            regular_user_usage.clear()
    else:
        print(f"{USER_DATA_FILE} not found. Starting empty.")
        vip_users.clear()
        regular_user_usage.clear()

def save_user_data():
    data_to_save = {
        "vip_users": vip_users,
        "regular_user_usage": list(regular_user_usage)
    }
    try:
        with open(USER_DATA_FILE, 'w') as f:
            json.dump(data_to_save, f, indent=4)
    except Exception as e:
        print(f"Error saving user data: {e}")

load_user_data()
# --- Fim persistência ---

def safe_reply(message, text, **kwargs):
    try:
        return bot.reply_to(message, text, **kwargs)
    except telebot.apihelper.ApiTelegramException as e:
        print(f"Failed to reply, sending as new message. Error: {e}")
        try:
            return bot.send_message(message.chat.id, text, **kwargs)
        except Exception as e2:
            print(f"Fallback send_message also failed: {e2}")
            return None

def is_owner(user_id):
    return user_id in AUTHORIZED_OWNERS

def is_group_allowed(chat_id, user_id):
    # Permite se for grupo liberado OU se for dono/admin
    return chat_id in ALLOWED_GROUP_IDS or is_owner(user_id)

def restricted_group(func):
    def wrapper(msg):
        if not is_group_allowed(msg.chat.id, msg.from_user.id):
            return safe_reply(msg, "❌ This bot is restricted to specific groups only @Dholujangir0008.")
        return func(msg)
    return wrapper

@bot.message_handler(commands=['allowgroup'])
def allow_group(msg):
    if not is_owner(msg.from_user.id):
        return safe_reply(msg, "❌ You do not have permission to use this command.")
    parts = msg.text.strip().split()
    if len(parts) != 2:
        return safe_reply(msg, "❗ Usage: /allowgroup group_id\nExample: /allowgroup -1001234567890")
    try:
        group_id = int(parts[1])
    except ValueError:
        return safe_reply(msg, "⚠️ Invalid group ID. It must be a number.")

    if group_id not in ALLOWED_GROUP_IDS:
        ALLOWED_GROUP_IDS.append(group_id)
        return safe_reply(msg, f"✅ Group `{group_id}` is now allowed to use the bot.", parse_mode="Markdown")
    else:
        return safe_reply(msg, f"ℹ️ Group `{group_id}` is already allowed.", parse_mode="Markdown")

@bot.message_handler(commands=['vipadd'])
def vip_add_command(msg):
    if not is_owner(msg.from_user.id):
        return safe_reply(msg, "❌ You do not have permission to use this command.")

    parts = msg.text.strip().split()
    if len(parts) != 4:
        return safe_reply(
            msg,
            "❗ *Usage:* `/vipadd user_id times days`\n*Example:* `/vipadd 123456789 10 30`",
            parse_mode="Markdown"
        )

    try:
        target_user_id = int(parts[1])
        times = int(parts[2])
        days = int(parts[3])
    except ValueError:
        return safe_reply(msg, "⚠️ Invalid input. `user_id`, `times`, and `days` must be numbers.")

    if times <= 0 or days <= 0:
        return safe_reply(msg, "⚠️ `times` and `days` must be positive numbers.")

    current_datetime = datetime.datetime.utcnow()
    expiry_datetime_obj = current_datetime + datetime.timedelta(days=days)
    expiry_timestamp = expiry_datetime_obj.timestamp()

    vip_users[target_user_id] = {
        'expiry_timestamp': expiry_timestamp,
        'remaining_requests': times,
        'total_requests_granted': times,
        'duration_days': days,
        'start_timestamp': current_datetime.timestamp()
    }
    save_user_data()

    expiry_date_str = expiry_datetime_obj.strftime("%Y-%m-%d %H:%M:%S UTC")
    response_text = (
        f"✅ *VIP added for user* `{target_user_id}`\n"
        f"📅 *Expires:* `{expiry_date_str}`\n"
        f"🔢 *Total Requests:* `{times}`\n"
        f"⏳ *Duration:* `{days}` days"
    )
    return safe_reply(msg, response_text, parse_mode="Markdown")

def check_user_like_permission(user_id):
    if is_owner(user_id):
        return True, None  # Admin sempre pode

    current_timestamp = time.time()
    was_vip_and_expired = False

    if user_id in vip_users:
        vip_data = vip_users[user_id]
        if current_timestamp < vip_data['expiry_timestamp']:  # VIP ativo
            if vip_data['remaining_requests'] > 0:
                vip_data['remaining_requests'] -= 1
                save_user_data()
                return True, None
            else:
                expiry_dt_str = datetime.datetime.fromtimestamp(vip_data['expiry_timestamp']).strftime('%Y-%m-%d %H:%M UTC')
                return False, f"❌ Você usou todas as suas requests VIP ({vip_data['total_requests_granted']}). VIP ativo até {expiry_dt_str}, mas sem requests restantes."
        else:
            was_vip_and_expired = True
            del vip_users[user_id]
            save_user_data()

    # Usuário regular pode usar 1 vez só
    if user_id in regular_user_usage:
        msg = "❌ Você já usou seu like único gratuito. "
        if was_vip_and_expired:
            msg = "⏳ Seu VIP expirou, e você já usou seu like gratuito. "
        msg += "Contate um administrador para acesso VIP."
        return False, msg
    else:
        regular_user_usage.add(user_id)
        save_user_data()
        return True, None

@bot.message_handler(commands=['like'])
@restricted_group
def like_cmd(msg):
    if msg.chat.type == "private":
        return safe_reply(msg, "❌ O comando /like só pode ser usado em grupos.")

    user_id = msg.from_user.id
    can_proceed, denial_message = check_user_like_permission(user_id)
    if not can_proceed:
        return safe_reply(msg, denial_message)

    parts = msg.text.strip().split()
    if len(parts) != 2:
        return safe_reply(
            msg,
            "❗ *Uso:* `/like uid`\n*Exemplo:* `/like 123456789`",
            parse_mode="Markdown"
        )

    uid_to_like = parts[1]
    status_msg = safe_reply(msg, "🔄 Enviando like... Aguarde, por favor...")
    if status_msg is None:
        print("Falha ao enviar mensagem inicial do /like.")
        return

    url = f"https://likes.ffgarena.cloud/api/v2/likes?uid={uid_to_like}&amount_of_likes=100&auth=vortex"

    try:
        res = requests.get(url, timeout=20)
        res.raise_for_status()
        data = res.json()
    except requests.exceptions.Timeout:
        return bot.edit_message_text(
            "⚠️ *Tempo esgotado. O servidor de likes pode estar lento ou fora do ar. Tente novamente mais tarde.*",
            chat_id=status_msg.chat.id,
            message_id=status_msg.message_id,
            parse_mode="Markdown"
        )
    except requests.exceptions.HTTPError as http_err:
        print(f"Erro HTTP na API: {http_err} - Resposta: {res.text if res else 'Sem resposta'}")
        return bot.edit_message_text(
            f"⚠️ *Erro na comunicação com o servidor de likes (HTTP {res.status_code if res else 'N/A'}). Tente novamente mais tarde.*",
            chat_id=status_msg.chat.id,
            message_id=status_msg.message_id,
            parse_mode="Markdown"
        )
    except requests.exceptions.RequestException as req_err:
        print(f"Erro de requisição API: {req_err}")
        return bot.edit_message_text(
            "⚠️ *Não foi possível conectar ao servidor de likes. Verifique a rede ou tente mais tarde.*",
            chat_id=status_msg.chat.id,
            message_id=status_msg.message_id,
            parse_mode="Markdown"
        )
    except json.JSONDecodeError:
        print(f"Erro ao decodificar JSON da API. Status: {res.status_code if res else 'N/A'}, Resposta: {res.text if res else 'Sem resposta'}")
        return bot.edit_message_text(
            "⚠️ *Resposta inválida do servidor de likes. Tente novamente mais tarde.*",
            chat_id=status_msg.chat.id,
            message_id=status_msg.message_id,
            parse_mode="Markdown"
        )

    if data.get("status") == 200:
        reply = (
            f"🔹 *Nickname:* `{data.get('nickname', 'N/A')}`\n"
            f"🔸 *Região:* `{data.get('region', 'N/A')}`\n"
            f"🔹 *Level:* `{data.get('level', 'N/A')}`\n"
            f"🔸 *Exp:* `{data.get('exp', 'N/A')}`\n"
            f"🔹 *Likes antes:* `{data.get('likes_antes', 'N/A')}`\n"
            f"🔸 *Likes depois:* `{data.get('likes_depois', 'N/A')}`\n"
            f"🔹 *Likes enviados:* `{data.get('sent', 'N/A')}`"
        )
        bot.edit_message_text(reply, chat_id=status_msg.chat.id, message_id=status_msg.message_id, parse_mode="Markdown")
    else:
        api_message = data.get("message", f"Falha ao dar like no UID {uid_to_like}. A API reportou um problema.")
        bot.edit_message_text(
            f"⚠️ *{api_message}*",
            chat_id=status_msg.chat.id,
            message_id=status_msg.message_id,
            parse_mode="Markdown"
        )

@bot.message_handler(commands=['help'])
@restricted_group
def help_command(msg):
    help_text = (
        "🤖 *Bot Help Menu*\n\n"
        "🔹 `/like uid`\n"
        "   Envia likes para o player com UID especificado.\n"
        "   *Exemplo:* `/like 123456789`\n"
        "   *(Admins: ilimitado, VIPs: limitado, Usuários regulares: 1 vez)*\n\n"
        "🔹 `/id`\n"
        "   Mostra o ID do chat e seu user ID.\n\n"
        "✨ *Comandos do Admin (somente dono):*\n"
        "🔹 `/allowgroup group_id`\n"
        "   Permite que um grupo use o bot.\n\n"
        "🔹 `/vipadd user_id times days`\n"
        "   Dá VIP para um usuário.\n"
        "   *Exemplo:* `/vipadd 123456789 10 30`"
    )
    safe_reply(msg, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['id'])
@restricted_group
def get_id(msg):
    safe_reply(msg, f"🆔 Chat ID: `{msg.chat.id}`\n👤 User ID: `{msg.from_user.id}`", parse_mode="Markdown")

if __name__ == '__main__':
    print("Bot starting...")
    while True:
        try:
            bot.polling(timeout=60, long_polling_timeout=45, non_stop=True)
        except Exception as e:
            print(f"{datetime.datetime.now()} Polling error: {e}. Retrying in 15 seconds...")
            time.sleep(15)
