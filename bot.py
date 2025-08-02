import telebot
import requests
import time
import json
import datetime
import os

BOT_TOKEN = "8191885274:AAETiQF_e_Xs198q5Ug5TDB52E_CYuUHY58"  # Seu token do bot
bot = telebot.TeleBot(BOT_TOKEN)

# IDs autorizados e grupos permitidos
AUTHORIZED_OWNERS = [8183673253]  # ID do dono (sem o -)
ALLOWED_GROUP_IDS = [-4781844651]  # ID do grupo (com o -)

# --- Persistência de dados ---
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
        return True, None

    current_timestamp = time.time()
    was_vip_and_expired = False

    if user_id in vip_users:
        vip_data = vip_users[user_id]
        if current_timestamp < vip_data['expiry_timestamp']:
            if vip_data['remaining_requests'] > 0:
                vip_data['remaining_requests'] -= 1
                save_user_data()
                return True, None
            else:
                expiry_dt_str = datetime.datetime.fromtimestamp(vip_data['expiry_timestamp']).strftime('%Y-%m-%d %H:%M UTC')
                return False, f"❌ Você usou todas as requests VIP ({vip_data['total_requests_granted']}). VIP ativo até {expiry_dt_str}, mas sem requests restantes."
        else:
            was_vip_and_expired = True
            del vip_users[user_id]
            save_user_data()

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
        sent_likes = data.get("sent", "0")
        sent_count = 0
        try:
            sent_count = int(''.join(filter(str.isdigit, str(sent_likes))))
        except Exception:
            pass

        if sent_count == 0:
            bot.edit_message_text(
                "⚠️ Você atingiu o limite diário de likes. Tente novamente amanhã!",
                chat_id=status_msg.chat.id,
                message_id=status_msg.message_id,
                parse_mode="Markdown"
            )
            return

        reply_text = (
            "✨ **VorteX Like!** ✨\n\n"
            f"👤 Nome: `{data.get('nickname', 'N/A')}`\n"
            f"🆔 UID: `{uid_to_like}`\n"
            f"🌎 Região: `{data.get('region', 'N/A')}`\n\n"
            f"👎 Likes antes: `{data.get('likes_antes', 'N/A')}`\n"
            f"👍 Likes depois: `{data.get('likes_depois', 'N/A')}`\n"
            f"✅ Likes adicionados pelo Bot: `{sent_likes}`"
        )

        bot.edit_message_text(
            reply_text,
            chat_id=status_msg.chat.id,
            message_id=status_msg.message_id,
            parse_mode="Markdown"
        )

        image_url = "https://cdn.discordapp.com/attachments/1359752132579950685/1401313741345259591/f3fcf1b8bc493f13d38e0451ae6d2f78.gif"
        bot.send_animation(msg.chat.id, animation=image_url)

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
