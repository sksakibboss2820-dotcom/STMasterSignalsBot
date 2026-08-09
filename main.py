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
    return "ST Master Signal Bot is Live!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')
ADMIN_ID = int(os.environ.get('ADMIN_ID', '0'))

bot = telebot.TeleBot(BOT_TOKEN)

# গ্লোবাল কনফিগারেশন ও স্টেট
auto_mode = False
selected_timeframe = "1m" # 30s, 1m, 3m, 5m
target_wins = 10
current_wins = 0
current_step = 1
super_win_streak = 0
last_prediction = None
history_table = [] # টেবিল হিস্ট্রি রাখার জন্য

# ১. রিয়েল-টাইম পিরিয়ড ক্যালকুলেটর (পরবর্তী বেটিং পিরিয়ডের জন্য offset = +1)
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

# ২. স্ক্রিনশটের মতো প্রফেশনাল UI কার্ড জেনারেটর
def generate_hd_dashboard(period, signal, confidence, number_pair, tf):
    img = Image.new('RGB', (750, 480), color=(245, 247, 250))
    draw = ImageDraw.Draw(img)

    # হেডার কার্ড
    draw.rectangle([20, 20, 730, 100], fill=(255, 255, 255), outline=(220, 226, 235))
    draw.text((40, 35), f"WinGo {tf.upper()} AI PREDICTION", fill=(16, 185, 129))
    draw.text((40, 65), f"STATUS: ACTIVE  |  CONFIDENCE: {confidence}%", fill=(100, 116, 139))

    # মেইন সিগন্যাল বক্স
    sig_color = (37, 99, 235) if signal == "BIG" else (225, 29, 72)
    draw.rectangle([20, 120, 480, 260], fill=(255, 255, 255), outline=sig_color, width=2)
    draw.text((180, 135), f"CURRENT SIGNAL", fill=(100, 116, 139))
    draw.text((190, 165), signal, fill=sig_color)
    draw.text((180, 220), f"CONFIDENCE = {confidence}%", fill=(16, 185, 129))

    # নম্বর বক্স
    draw.rectangle([500, 120, 730, 260], fill=(255, 255, 255), outline=(220, 226, 235))
    draw.text((560, 135), "NUMBER", fill=(16, 185, 129))
    draw.text((570, 170), number_pair, fill=(16, 185, 129))

    # পিরিয়ড ও ইনফো
    draw.text((20, 280), f"MODE   : WinGo {tf}", fill=(30, 41, 59))
    draw.text((20, 310), f"PERIOD : {period[-6:]}", fill=(30, 41, 59))
    draw.text((20, 340), f"SIGNAL : {signal}", fill=sig_color)

    # ফুটার স্ট্যাটস
    draw.rectangle([20, 390, 230, 450], fill=(236, 253, 245))
    draw.text((90, 400), "WINS", fill=(5, 150, 105))
    draw.text((95, 420), f"{current_wins}", fill=(5, 150, 105))

    draw.rectangle([250, 390, 480, 450], fill=(254, 242, 242))
    draw.text((320, 400), "STEP", fill=(225, 29, 72))
    draw.text((330, 420), f"{current_step}", fill=(225, 29, 72))

    draw.rectangle([500, 390, 730, 450], fill=(239, 246, 255))
    draw.text((550, 400), "SUPER STREAK", fill=(37, 99, 235))
    draw.text((580, 420), f"{super_win_streak}", fill=(37, 99, 235))

    img.save("signal.png")

# ৩. সিগন্যাল সেন্ড করার প্রধান ফাংশন
def broadcast_signal(signal, number_pair, confidence=88):
    global last_prediction
    period = get_market_period(selected_timeframe)
    generate_hd_dashboard(period, signal, confidence, number_pair, selected_timeframe)
    
    caption = (
        f"👾 MODE : WINGO {selected_timeframe.upper()}\n"
        f"🎰 PERIOD : {period[-6:]}\n"
        f"📈 SIGNAL = {'🔵 BIG' if signal == 'BIG' else '🔴 SMALL'}\n"
        f"🎲 NUMBER = {number_pair}\n"
        f"🔥 CONFIDENCE = {confidence}%"
    )
    
    with open("signal.png", "rb") as photo:
        bot.send_photo(CHANNEL_ID, photo, caption=caption)
    
    last_prediction = {"period": period[-6:], "signal": signal}

# ৪. ফলাফল প্রক্রিয়াকরণ (Step and Super Win Calculator)
def process_result(is_win):
    global current_wins, current_step, super_win_streak, auto_mode
    period_str = last_prediction['period'] if last_prediction else "NEXT"

    if is_win:
        current_wins += 1
        super_win_streak += 1
        current_step = 1 # উইন হলে স্টেপ রিকভার হয়ে ১ এ নামবে
        
        msg = f"✅ WIN!\n=====================\nPeriod => #{period_str}\nResult => {super_win_streak} SUPER WIN 🎉\n====================="
        
        # টার্গেট মিসন কমপ্লিট চেক
        if current_wins >= target_wins:
            auto_mode = False
            msg += f"\n\n🎯 MISSION COMPLETED! Target {target_wins} Wins Reached. Auto Bot Closed."
    else:
        current_step += 1
        super_win_streak = 0 # লস হলে সুপার উইন স্ট্রিক রিসেট
        msg = f"❌ LOSS\n=====================\nPeriod => #{period_str}\nResult => Use {current_step} STEP ⚠️\n====================="

    bot.send_message(CHANNEL_ID, msg)

# ৫. ব্যাকগ্রাউন্ড অটো লুপ
def auto_signal_loop():
    global auto_mode
    while True:
        if auto_mode:
            # অটোমেটিক সিগন্যাল জেনারেট
            sig = random.choice(["BIG", "SMALL"])
            num = "1/2" if sig == "BIG" else "6/7"
            broadcast_signal(sig, num, random.randint(80, 97))

            # টাইমফ্রেমে নির্দেশিত সেকেন্ডের জন্য বিরতি
            sleep_time = 30 if selected_timeframe == "30s" else 60 if selected_timeframe == "1m" else 180 if selected_timeframe == "3m" else 300
            time.sleep(sleep_time)
        else:
            time.sleep(3)

# ৬. এডমিন কন্ট্রোল প্যানেল কিবোর্ড
def get_control_keyboard():
    markup = InlineKeyboardMarkup()
    
    btn_status = InlineKeyboardButton(f"Auto Mode: {'ON 🟢' if auto_mode else 'OFF 🔴'}", callback_data="toggle_auto")
    
    # টাইমার নির্বাচন বাটন
    btn_30s = InlineKeyboardButton(f"{'✅' if selected_timeframe=='30s' else ''} 30s", callback_data="tf_30s")
    btn_1m = InlineKeyboardButton(f"{'✅' if selected_timeframe=='1m' else ''} 1 Min", callback_data="tf_1m")
    btn_3m = InlineKeyboardButton(f"{'✅' if selected_timeframe=='3m' else ''} 3 Min", callback_data="tf_3m")
    btn_5m = InlineKeyboardButton(f"{'✅' if selected_timeframe=='5m' else ''} 5 Min", callback_data="tf_5m")

    # ম্যানুয়াল সিগন্যাল বাটন
    btn_big = InlineKeyboardButton("Send BIG 🔵", callback_data="send_big")
    btn_small = InlineKeyboardButton("Send SMALL 🔴", callback_data="send_small")
    
    # রেজাল্ট বাটন
    btn_win = InlineKeyboardButton("Send WIN ✅", callback_data="res_win")
    btn_loss = InlineKeyboardButton("Send LOSS ❌", callback_data="res_loss")

    markup.add(btn_status)
    markup.row(btn_30s, btn_1m, btn_3m, btn_5m)
    markup.row(btn_big, btn_small)
    markup.row(btn_win, btn_loss)
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if ADMIN_ID != 0 and message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "আপনার এক্সেস নেই।")
        return
    bot.send_message(message.chat.id, "⚙️ **ST Signal Master Control Panel**", reply_markup=get_control_keyboard(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    global auto_mode, selected_timeframe, current_wins
    
    if ADMIN_ID != 0 and call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "অনুমতি নেই!")
        return

    if call.data == "toggle_auto":
        auto_mode = not auto_mode
        if auto_mode:
            current_wins = 0 # অটো চালুর সময় টার্গেট রিসেট
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=get_control_keyboard())
        bot.answer_callback_query(call.id, f"Auto Mode {'ON' if auto_mode else 'OFF'}")

    elif call.data.startswith("tf_"):
        selected_timeframe = call.data.split("_")[1]
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=get_control_keyboard())
        bot.answer_callback_query(call.id, f"Timeframe set to {selected_timeframe}")

    elif call.data == "send_big":
        broadcast_signal("BIG", "1/2")
        bot.answer_callback_query(call.id, "BIG Signal Sent!")

    elif call.data == "send_small":
        broadcast_signal("SMALL", "6/7")
        bot.answer_callback_query(call.id, "SMALL Signal Sent!")

    elif call.data == "res_win":
        process_result(True)
        bot.answer_callback_query(call.id, "WIN Result Sent!")

    elif call.data == "res_loss":
        process_result(False)
        bot.answer_callback_query(call.id, "LOSS Result Sent!")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    threading.Thread(target=auto_signal_loop).start()
    
    bot.remove_webhook()
    time.sleep(1)
    
    print("Bot started successfully...")
    bot.infinity_polling(skip_pending=True)
