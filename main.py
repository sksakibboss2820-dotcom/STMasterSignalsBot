import os
import time
import random
import threading
from datetime import datetime
from PIL import Image, ImageDraw
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask

app = Flask('')

@app.route('/')
def home():
    return "Bot is running perfectly!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')
ADMIN_ID = int(os.environ.get('ADMIN_ID', '0'))

bot = telebot.TeleBot(BOT_TOKEN)

# গ্লোবাল স্টেট
auto_mode = False
last_prediction = None # {"period": ..., "signal": ...}

def get_current_period():
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    minutes_passed = now.hour * 60 + now.minute
    period_seq = 10001 + minutes_passed
    return f"{date_str}1000{period_seq}"

def create_signal_image(period, signal, confidence, number_pair):
    img = Image.new('RGB', (700, 400), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)
    
    draw.text((40, 30), "WinGo 1 Min AI Prediction", fill=(255, 255, 255))
    draw.text((40, 90), f"PERIOD : {period}", fill=(148, 163, 184))
    
    color = (34, 197, 94) if signal == "BIG" else (239, 68, 68)
    draw.text((40, 150), f"SIGNAL : {signal}", fill=color)
    draw.text((40, 210), f"NUMBER : {number_pair}", fill=(56, 189, 248))
    draw.text((40, 270), f"CONFIDENCE : {confidence}%", fill=(234, 179, 8))
    
    img.save("signal.png")

def send_signal_to_channel(signal, number_pair, confidence=88):
    global last_prediction
    period = get_current_period()
    create_signal_image(period, signal, confidence, number_pair)
    
    caption = (
        f"👾 MODE : WINGO 1 MIN\n"
        f"🎰 PERIOD : {period[-6:]}\n"
        f"📈 SIGNAL = {'🔵 BIG' if signal == 'BIG' else '🔴 SMALL'}\n"
        f"🎲 NUMBER = {number_pair}\n"
        f"🔥 CONFIDENCE = {confidence}%"
    )
    
    with open("signal.png", "rb") as photo:
        bot.send_photo(CHANNEL_ID, photo, caption=caption)
    
    last_prediction = {"period": period[-6:], "signal": signal}

# অটো সিগন্যাল লুপ
def auto_signal_loop():
    global auto_mode
    while True:
        if auto_mode:
            # আগে যদি কোনো প্রেডিকশন থেকে থাকে, তার ফলাফল দেখানো (র‍্যান্ডম রেজাল্ট উদাহরণস্বরূপ)
            if last_prediction:
                is_win = random.choice([True, True, False]) # ৭০% উইন চান্স
                res_text = "✅ WIN!" if is_win else "❌ LOSS"
                bot.send_message(
                    CHANNEL_ID, 
                    f"{res_text}\n=====================\nPeriod => #{last_prediction['period']}\nResult => {'SUCCESS' if is_win else 'FAILED'}\n====================="
                )
                time.sleep(2)

            # নতুন সিগন্যাল পাঠানো
            sig = random.choice(["BIG", "SMALL"])
            num = "1/2" if sig == "BIG" else "6/7"
            send_signal_to_channel(sig, num, random.randint(80, 96))
            
            time.sleep(58) # ১ মিনিটের সাইকেল
        else:
            time.sleep(5)

# কন্ট্রোল প্যানেল কিবোর্ড
def get_control_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    
    status_btn = InlineKeyboardButton(f"Auto Mode: {'ON 🟢' if auto_mode else 'OFF 🔴'}", callback_data="toggle_auto")
    btn_big = InlineKeyboardButton("Send BIG 🔵", callback_data="send_big")
    btn_small = InlineKeyboardButton("Send SMALL 🔴", callback_data="send_small")
    btn_win = InlineKeyboardButton("Send WIN ✅", callback_data="res_win")
    btn_loss = InlineKeyboardButton("Send LOSS ❌", callback_data="res_loss")
    
    markup.add(status_btn)
    markup.add(btn_big, btn_small)
    markup.add(btn_win, btn_loss)
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if ADMIN_ID != 0 and message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "আপনার এই বটের অ্যাক্সেস নেই।")
        return
    bot.send_message(message.chat.id, "ST Master Signal Control Panel:", reply_markup=get_control_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    global auto_mode, last_prediction
    
    if ADMIN_ID != 0 and call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "অনুমতি নেই!")
        return

    if call.data == "toggle_auto":
        auto_mode = not auto_mode
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=get_control_keyboard())
        bot.answer_callback_query(call.id, f"Auto Mode {'ON' if auto_mode else 'OFF'}")

    elif call.data == "send_big":
        send_signal_to_channel("BIG", "1/2")
        bot.answer_callback_query(call.id, "BIG Signal Sent!")

    elif call.data == "send_small":
        send_signal_to_channel("SMALL", "6/7")
        bot.answer_callback_query(call.id, "SMALL Signal Sent!")

    elif call.data == "res_win":
        period_str = last_prediction['period'] if last_prediction else "NEXT"
        bot.send_message(CHANNEL_ID, f"✅ WIN!\n=====================\nPeriod => #{period_str}\nResult => SUCCESS\n=====================")
        bot.answer_callback_query(call.id, "WIN Message Sent!")

    elif call.data == "res_loss":
        period_str = last_prediction['period'] if last_prediction else "NEXT"
        bot.send_message(CHANNEL_ID, f"❌ LOSS\n=====================\nPeriod => #{period_str}\nResult => FAILED\n=====================")
        bot.answer_callback_query(call.id, "LOSS Message Sent!")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    threading.Thread(target=auto_signal_loop).start()
    
    # পোলিং এরর এড়াতে আগের সেশন ক্লিয়ার করা
    bot.remove_webhook()
    time.sleep(1)
    
    print("Bot started...")
    bot.infinity_polling(skip_pending=True)
