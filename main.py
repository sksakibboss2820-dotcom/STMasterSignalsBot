import os
import time
import random
import threading
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask

app = Flask('')

@app.route('/')
def home():
    return "ST Signal Dashboard Server Live!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')
ADMIN_ID = int(os.environ.get('ADMIN_ID', '0'))

bot = telebot.TeleBot(BOT_TOKEN)

# গ্লোবাল স্টেট
auto_mode = False
selected_timeframe = "1m" # 30s, 1m, 3m, 5m
target_wins = 10
current_wins = 2595
jackpot_count = 726
current_streak = 2
max_streak = 21
total_predictions = 3640

last_prediction = None
history_rows = []

def get_market_period(tf):
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    total_seconds = now.hour * 3600 + now.minute * 60 + now.second
    
    if tf == "30s":
        seq = (total_seconds // 30) + 1 + 10000
    elif tf == "1m":
        seq = (total_seconds // 60) + 1 + 10000
    elif tf == "3m":
        seq = (total_seconds // 180) + 1 + 10000
    elif tf == "5m":
        seq = (total_seconds // 300) + 1 + 10000
    else:
        seq = (total_seconds // 60) + 1 + 10000

    return f"{date_str}1000{seq}"

# রেফারেন্স স্ক্রিনশটের মতো ড্যাশবোর্ড জেনারেটর
def generate_exact_dashboard(period, signal, confidence, number_pair, tf):
    img = Image.new('RGB', (800, 920), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # লোগো ও হেডার
    draw.ellipse([20, 20, 100, 100], outline=(0, 0, 0), width=3)
    draw.text((38, 45), "WG", fill=(16, 185, 129))
    draw.text((120, 20), f"WinGo {tf.upper()}", fill=(16, 185, 129))
    draw.text((120, 50), "AI PREDICTION BOT", fill=(0, 0, 0))
    draw.text((120, 70), "ENGINE : PART1-WG1M v3", fill=(100, 116, 139))

    # টপ ব্যাজ
    draw.rectangle([120, 95, 280, 125], outline=(16, 185, 129), width=2)
    draw.text((130, 100), "WIN", fill=(16, 185, 129))
    draw.text((220, 100), f"{current_wins}", fill=(16, 185, 129))

    draw.rectangle([290, 95, 450, 125], outline=(234, 179, 8), width=2)
    draw.text((300, 100), "JACK", fill=(234, 179, 8))
    draw.text((390, 100), f"{jackpot_count}", fill=(234, 179, 8))

    draw.rectangle([460, 95, 620, 125], outline=(239, 68, 68), width=2)
    draw.text((470, 100), "STREAK", fill=(239, 68, 68))
    draw.text((580, 100), f"{current_streak}", fill=(239, 68, 68))

    # ইনফো বার (ব্ল্যাক ব্যাকগ্রাউন্ড)
    draw.rectangle([0, 140, 800, 180], fill=(15, 23, 42))
    now_str = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
    draw.text((10, 150), f"TIME: {now_str}", fill=(255, 255, 255))
    draw.text((260, 150), "STATUS: ACTIVE", fill=(34, 197, 94))
    draw.text((500, 150), "ACCURACY: 71.3%", fill=(34, 197, 94))
    draw.text((650, 150), f"PRED: {total_predictions}", fill=(255, 255, 255))

    # কারেন্ট সিগন্যাল প্যানেল
    draw.text((20, 195), f"MODE   : WinGo {tf}", fill=(71, 85, 105))
    draw.text((20, 220), f"PERIOD : {period[-6:]}", fill=(0, 0, 0))
    sig_color = (225, 29, 72) if signal == "SMALL" else (37, 99, 235)
    draw.text((20, 245), f"SIGNAL : {signal}", fill=sig_color)
    draw.text((20, 270), f"NUMBER : {number_pair}", fill=(16, 185, 129))

    # মেইন প্রেডিকশন বক্স
    draw.rectangle([280, 190, 540, 310], outline=sig_color, width=2)
    draw.text((330, 195), "CURRENT SIGNAL", fill=(16, 185, 129))
    draw.text((310, 215), signal, fill=sig_color)
    draw.text((370, 260), f"{confidence}%", fill=(16, 185, 129))
    draw.text((330, 285), f"CONFIDENCE = {confidence}%", fill=(16, 185, 129))

    # নম্বর ফিল্ড
    draw.rectangle([640, 190, 780, 310], outline=(16, 185, 129), width=2)
    draw.text((670, 195), "NUMBER", fill=(16, 185, 129))
    draw.text((685, 225), number_pair, fill=(16, 185, 129))

    # টেবিল হেডার
    draw.rectangle([0, 330, 800, 360], fill=(15, 23, 42))
    draw.text((10, 338), "#", fill=(255, 255, 255))
    draw.text((100, 338), "PERIOD", fill=(255, 255, 255))
    draw.text((300, 338), "SIGNAL", fill=(255, 255, 255))
    draw.text((420, 338), "NUMBER", fill=(255, 255, 255))
    draw.text((510, 338), "RESULT", fill=(255, 255, 255))
    draw.text((680, 338), "TIME", fill=(255, 255, 255))

    # হিস্ট্রি টেবিল রেন্ডারিং
    y = 370
    for idx, row in enumerate(history_rows[-9:]):
        draw.text((10, y), str(idx+1), fill=(100, 116, 139))
        draw.text((100, y), row['period'], fill=(30, 41, 59))
        draw.text((300, y), row['signal'], fill=(37, 99, 235) if row['signal']=="BIG" else (225, 29, 72))
        draw.text((420, y), str(row['num']), fill=(30, 41, 59))

        # রেজাল্ট ব্যাজ
        res_bg = (220, 252, 231) if row['res'] == "WIN" else (254, 242, 242) if row['res'] == "LOSE" else (254, 249, 195)
        res_fg = (22, 101, 52) if row['res'] == "WIN" else (153, 27, 27) if row['res'] == "LOSE" else (161, 98, 7)
        draw.rectangle([500, y-2, 560, y+18], fill=res_bg)
        draw.text((510, y), row['res'], fill=res_fg)
        draw.text((680, y), row['time'], fill=(100, 116, 139))
        y += 35

    # কারেন্ট রানিং রো
    draw.text((10, y), "10", fill=(16, 185, 129))
    draw.text((100, y), period[-6:], fill=(16, 185, 129))
    draw.text((300, y), signal, fill=sig_color)
    draw.text((420, y), number_pair, fill=(16, 185, 129))
    draw.rectangle([500, y-2, 560, y+18], fill=(219, 234, 254))
    draw.text((510, y), "NEXT", fill=(29, 78, 216))
    draw.text((680, y), datetime.now().strftime("%I:%M:%S %p"), fill=(16, 185, 129))

    # ফুটার কার্ড
    draw.rectangle([20, 750, 180, 810], outline=(16, 185, 129), width=2)
    draw.text((70, 760), "WINS", fill=(16, 185, 129))
    draw.text((70, 780), f"{current_wins}", fill=(16, 185, 129))

    draw.rectangle([200, 750, 360, 810], outline=(234, 179, 8), width=2)
    draw.text((240, 760), "JACKPOT", fill=(234, 179, 8))
    draw.text((255, 780), f"{jackpot_count}", fill=(234, 179, 8))

    draw.rectangle([380, 750, 540, 810], outline=(239, 68, 68), width=2)
    draw.text((410, 760), "MAX STREAK", fill=(239, 68, 68))
    draw.text((450, 780), f"{max_streak}", fill=(239, 68, 68))

    draw.rectangle([560, 750, 780, 810], fill=(239, 246, 255))
    draw.text((620, 760), "WIN RATE", fill=(37, 99, 235))
    draw.text((630, 780), "71.3%", fill=(37, 99, 235))

    img.save("exact_dashboard.png")

# সিগন্যাল পাঠানোর ফাংশন
def broadcast_signal(signal, number_pair, confidence=68):
    global last_prediction
    period = get_market_period(selected_timeframe)
    generate_exact_dashboard(period, signal, confidence, number_pair, selected_timeframe)

    caption = (
        f"👾 MODE : WINGO {selected_timeframe.upper()}\n"
        f"╭────────────────╮\n"
        f"🎰 PERIOD : {period[-6:]}\n"
        f"⚙️ LOGIC  : PART 1 | ENTRY 1\n\n"
        f"┣ 📈 SIGNAL = {'🔴 SMALL' if signal == 'SMALL' else '🔵 BIG'}\n"
        f"┣ \n"
        f"┣ 🛡 NUMBER = {number_pair}\n"
        f"┣ \n"
        f"╰────────────────╯"
    )

    with open("exact_dashboard.png", "rb") as photo:
        bot.send_photo(CHANNEL_ID, photo, caption=caption)

    last_prediction = {"period": period[-6:], "signal": signal, "full_period": period}

# ফলাফল প্রসেসর (WIN / LOSS / JACKPOT)
def send_result_message(res_type, num_hit):
    global current_wins, jackpot_count, current_streak, history_rows
    if not last_prediction:
        period_str = "0299"
        sig = "BIG"
    else:
        period_str = last_prediction['period']
        sig = last_prediction['signal']

    is_big = int(num_hit) >= 5
    side_emoji = "🔵  BIG" if is_big else "🔴  SMALL"

    if res_type == "WIN":
        current_wins += 1
        current_streak += 1
        history_rows.append({"period": last_prediction['full_period'] if last_prediction else "20260809100010290", "signal": sig, "num": num_hit, "res": "WIN", "time": datetime.now().strftime("%I:%M:%S %p")})
        msg = f"✅ WIN!\n================================\nPeriod  =>  #{period_str}\nResult  =>  NUM:{num_hit}  {side_emoji}\n================================"

    elif res_type == "JACKPOT":
        jackpot_count += 1
        current_wins += 1
        current_streak += 1
        history_rows.append({"period": last_prediction['full_period'] if last_prediction else "20260809100010290", "signal": sig, "num": num_hit, "res": "JACK", "time": datetime.now().strftime("%I:%M:%S %p")})
        msg = f"🎰 JACK! NUMBER HIT\n================================\nPeriod  =>  #{period_str}\nResult  =>  NUM:{num_hit}  {side_emoji}\n================================"

    else:
        current_streak = 0
        history_rows.append({"period": last_prediction['full_period'] if last_prediction else "20260809100010290", "signal": sig, "num": num_hit, "res": "LOSE", "time": datetime.now().strftime("%I:%M:%S %p")})
        msg = f"❌ LOSS\n================================\nPeriod  =>  #{period_str}\nResult  =>  NUM:{num_hit}  {side_emoji}\n================================"

    bot.send_message(CHANNEL_ID, msg)

def auto_loop():
    while True:
        if auto_mode:
            sig = random.choice(["BIG", "SMALL"])
            num = "1/2" if sig == "BIG" else "5/7"
            broadcast_signal(sig, num)
            sleep_time = 30 if selected_timeframe == "30s" else 60 if selected_timeframe == "1m" else 180 if selected_timeframe == "3m" else 300
            time.sleep(sleep_time)
        else:
            time.sleep(3)

def get_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton(f"Auto Mode: {'ON 🟢' if auto_mode else 'OFF 🔴'}", callback_data="toggle_auto"))
    markup.row(
        InlineKeyboardButton("30s", callback_data="tf_30s"),
        InlineKeyboardButton("1m", callback_data="tf_1m"),
        InlineKeyboardButton("3m", callback_data="tf_3m"),
        InlineKeyboardButton("5m", callback_data="tf_5m")
    )
    markup.row(
        InlineKeyboardButton("Send SMALL 🔴", callback_data="sig_small"),
        InlineKeyboardButton("Send BIG 🔵", callback_data="sig_big")
    )
    markup.row(
        InlineKeyboardButton("Send WIN ✅", callback_data="res_win"),
        InlineKeyboardButton("Send JACKPOT 🎰", callback_data="res_jack"),
        InlineKeyboardButton("Send LOSS ❌", callback_data="res_loss")
    )
    return markup

@bot.message_handler(commands=['start'])
def start_cmd(message):
    if ADMIN_ID != 0 and message.from_user.id != ADMIN_ID:
        return
    bot.send_message(message.chat.id, "⚙️ **ST Control Panel**", reply_markup=get_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    global auto_mode, selected_timeframe
    if call.data == "toggle_auto":
        auto_mode = not auto_mode
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=get_keyboard())
    elif call.data.startswith("tf_"):
        selected_timeframe = call.data.split("_")[1]
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=get_keyboard())
    elif call.data == "sig_small":
        broadcast_signal("SMALL", "5/7")
    elif call.data == "sig_big":
        broadcast_signal("BIG", "1/2")
    elif call.data == "res_win":
        send_result_message("WIN", random.choice([6, 7, 8, 9]))
    elif call.data == "res_jack":
        send_result_message("JACKPOT", 6)
    elif call.data == "res_loss":
        send_result_message("LOSS", random.choice([0, 1, 2, 3]))

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    threading.Thread(target=auto_loop).start()
    bot.remove_webhook()
    time.sleep(1)
    bot.infinity_polling(skip_pending=True)
