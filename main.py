import os
import time
import random
import threading
from PIL import Image, ImageDraw, ImageFont
import telebot
from flask import Flask

# Flask অ্যাপ (Render-কে অনলাইনে রাখার জন্য)
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# আপনার এনভায়রনমেন্ট ভেরিয়েবল থেকে টোকেন নেওয়া হবে
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')

bot = telebot.TeleBot(BOT_TOKEN)

# ডায়নামিক সিগন্যাল কার্ড ইমেজ জেনারেটর
def create_signal_image(period, signal, confidence):
    img = Image.new('RGB', (600, 350), color=(18, 24, 38))
    draw = ImageDraw.Draw(img)
    
    # হেডার
    draw.text((30, 30), "WinGo 1 Min AI Prediction", fill=(255, 255, 255))
    
    # পিরিয়ড ও সিগন্যাল বক্স
    draw.text((30, 90), f"PERIOD : {period}", fill=(200, 200, 200))
    
    color = (0, 200, 100) if signal == "BIG" else (230, 50, 50)
    draw.text((30, 140), f"SIGNAL : {signal}", fill=color)
    draw.text((30, 190), f"CONFIDENCE : {confidence}%", fill=(255, 215, 0))
    
    img.save("signal.png")

# অটোমেটিক সিগন্যাল লুপ
def start_signal_loop():
    period = 10300
    while True:
        signals = ["BIG", "SMALL"]
        current_signal = random.choice(signals)
        confidence = random.randint(70, 95)
        num = "1/2" if current_signal == "BIG" else "6/7"
        
        # ছবি জেনারেট
        create_signal_image(period, current_signal, confidence)
        
        caption = (
            f"👾 MODE : WINGO 1 MIN\n"
            f"🎰 PERIOD : {period}\n"
            f"📈 SIGNAL = {'🔵 BIG' if current_signal == 'BIG' else '🔴 SMALL'}\n"
            f"🎲 NUMBER = {num}"
        )
        
        try:
            with open("signal.png", "rb") as photo:
                bot.send_photo(CHANNEL_ID, photo, caption=caption)
            print(f"Signal sent for period {period}")
        except Exception as e:
            print(f"Error sending message: {e}")
            
        period += 1
        time.sleep(60) # প্রতি ১ মিনিট পর পর

if __name__ == "__main__":
    # Flask সার্ভার আলাদা থ্রেডে চালানো
    threading.Thread(target=run_flask).start()
    
    # সিগন্যাল লুপ চালানো
    start_signal_loop()
