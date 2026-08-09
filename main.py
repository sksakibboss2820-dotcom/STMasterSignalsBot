import os
import time
import random
import threading
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import telebot
from flask import Flask

# Flask Server setup
app = Flask('')

@app.route('/')
def home():
    return "Bot is running perfectly!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')
# অ্যাডমিনের টেলিগ্রাম ইউজার আইডি (নিরাপত্তার জন্য যাতে অন্য কেউ কমান্ড না দিতে পারে)
ADMIN_ID = int(os.environ.get('ADMIN_ID', '0')) 

bot = telebot.TeleBot(BOT_TOKEN)

# ১. লাইভ পিরিয়ড ক্যালকুলেটর
def get_current_period():
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    
    # রাত ১২টা থেকে বর্তমান সময় পর্যন্ত যত মিনিট পার হয়েছে
    minutes_passed = now.hour * 60 + now.minute
    period_seq = 10001 + minutes_passed
    
    # উদাহরণ ফরম্যাট: 20260810100011186
    return f"{date_str}1000{period_seq}"

# ২. এইচডি সিগন্যাল কার্ড জেনারেটর
def create_signal_image(period, signal, confidence, number_pair):
    img = Image.new('RGB', (700, 400), color=(15, 23, 42)) # গাঢ় ব্যাকগ্রাউন্ড
    draw = ImageDraw.Draw(img)
    
    # হেডার
    draw.text((40, 30), "WinGo 1 Min AI Prediction", fill=(255, 255, 255))
    
    # পিরিয়ড ও সিগন্যাল বক্স
    draw.text((40, 90), f"PERIOD : {period}", fill=(148, 163, 184))
    
    color = (34, 197, 94) if signal == "BIG" else (239, 68, 68)
    draw.text((40, 150), f"SIGNAL : {signal}", fill=color)
    draw.text((40, 210), f"NUMBER : {number_pair}", fill=(56, 189, 248))
    draw.text((40, 270), f"CONFIDENCE : {confidence}%", fill=(234, 179, 8))
    
    img.save("signal.png")

# ৩. চ্যানেলে মেসেজ সেন্ড করার ফাংশন
def broadcast_signal(signal, number_pair, confidence=85):
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

# ৪. ম্যানুয়াল সিগন্যাল দেওয়ার অ্যাডমিন কমান্ড
# উদাহরণ: /send BIG 1/2  অথবা  /send SMALL 6/7
@bot.message_handler(commands=['send'])
def handle_manual_signal(message):
    # যদি অ্যাডমিন ইউজার আইডি চেক করতে চান
    if ADMIN_ID != 0 and message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "আপনি এই কমান্ডটি ব্যবহার করতে পারবেন না।")
        return

    try:
        args = message.text.split()
        if len(args) < 3:
            bot.reply_to(message, "সঠিক ফরম্যাট: `/send BIG 1/2` বা `/send SMALL 6/7`", parse_mode="Markdown")
            return
            
        signal = args[1].upper()
        number_pair = args[2]
        confidence = random.randint(80, 98)
        
        broadcast_signal(signal, number_pair, confidence)
        bot.reply_to(message, f"✅ সিগন্যাল সফলভাবে পিরিয়ড `{get_current_period()}` এর জন্য সেন্ড করা হয়েছে!")
    except Exception as e:
        bot.reply_to(message, f"ত্রুটি: {e}")

# বটের অটো-লিসেনার রান করা
def run_bot_polling():
    bot.infinity_polling()

if __name__ == "__main__":
    # Flask চালু
    threading.Thread(target=run_flask).start()
    
    # টেলিগ্রাম কমান্ড লিসেনার চালু
    print("Bot is listening for commands...")
    run_bot_polling()
