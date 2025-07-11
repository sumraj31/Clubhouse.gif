import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading, time, httpx, requests, asyncio

# === Configuration ===
BOT_TOKEN = "7974063244:AAFYXpWotmmykhWCRL7P4BG_hgwTX2Is5EE"
club_token = "6cc2cdb647407a3b754490ec78af1715ce1e1af1"
gif_id = "3oEjI6SIIHBdRxXI40"  # Change if needed

bot = telebot.TeleBot(BOT_TOKEN)
is_running = False
channel = None

headers = {
    "Authorization": f"Token {club_token}",
    "Content-Type": "application/json; charset=utf-8",
    "User-Agent": "clubhouse/android/1019808",
    "CH-AppBuild": "304",
    "CH-AppVersion": "0.1.28",
    "Accept": "application/json",
}

# === Telegram Commands ===
@bot.message_handler(commands=["start"])
def cmd_start(msg):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("▶️ Start GIF Loop", callback_data="start"),
        InlineKeyboardButton("🛑 Stop GIF Loop", callback_data="stop"),
    )
    bot.send_message(msg.chat.id, "Choose action:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data in ["start", "stop"])
def cb_handler(c):
    global is_running
    if c.data == "start":
        bot.send_message(c.message.chat.id, "🔗 Send Clubhouse room link:")
        bot.register_next_step_handler(c.message, receive_link)
    else:
        is_running = False
        bot.send_message(c.message.chat.id, "🛑 Stopped all actions.")

def receive_link(msg):
    global channel, is_running
    link = msg.text.strip()
    try:
        channel = link.split("/room/")[1].split("?")[0]
    except:
        bot.send_message(msg.chat.id, "❌ Invalid link.")
        return
    res = requests.post(
        "https://www.clubhouseapi.com/api/join_channel",
        headers=headers,
        json={"channel": channel}
    )
    if res.status_code == 200:
        bot.send_message(msg.chat.id, f"✅ Joined room `{channel}`", parse_mode="Markdown")
    else:
        bot.send_message(msg.chat.id, f"❌ Join failed: {res.status_code}")
    is_running = True
    threading.Thread(target=run_loops, args=(msg.chat.id,), daemon=True).start()

def run_loops(chat_id):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(asyncio.gather(
        gif_loop(chat_id),
        speaker_raise_loop(),
    ))

async def gif_loop(chat_id):
    global is_running
    while is_running:
        res = requests.post(
            "https://www.clubhouse.com/web_api/gif_reaction",
            headers=headers,
            json={"channel": channel, "giphy_id": gif_id}
        )
        if res.status_code == 200:
            bot.send_message(chat_id, "✅ GIF sent")
            await asyncio.sleep(15)
        elif res.status_code == 429:
            bot.send_message(chat_id, "⚠️ Retry faster due to rate limit")
            await asyncio.sleep(1)
        else:
            bot.send_message(chat_id, f"❌ GIF error {res.status_code}")
            await asyncio.sleep(5)

async def speaker_raise_loop():
    while is_running:
        async with httpx.AsyncClient() as client:
            await client.post(
                "https://www.clubhouseapi.com/api/audience_reply",
                headers=headers,
                json={"channel": channel, "raise_hands": True, "unraise_hands": False}
            )
            await client.post(
                "https://www.clubhouseapi.com/api/become_speaker",
                headers=headers,
                json={"channel": channel, "source": None}
            )
        await asyncio.sleep(10)

print("🤖 Bot running...")
bot.infinity_polling()
