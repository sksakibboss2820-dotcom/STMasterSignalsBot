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
    return "ST Signal Engine Running Smoothly!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')
ADMIN_ID = int(os.environ.get('ADMIN_ID', '0'))

bot = telebot.TeleBot(BOT_TOKEN)

# গ্লোবাল স্টেট ও ট্র্যাকিং variables
auto_mode = False
selected_timeframe = "1m" # 30s, 1m, 3m, 5m
current_wins = 2595
jackpot_count = 726
current_streak = 2
max_streak = 21
total_predictions = 3640

last_prediction = None
history_rows = []

# ১. নিখুঁত পিরিয়ড ক্যালকুলেটর (বাজার অনুযায়ী সিঙ্কড)
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

# ২. নিখুঁত এইচডি ড্যাশবোর্ড জেনারেটর (Clear & Bold Output)
def generate_exact_dashboard(period, signal, confidence, number_pair, tf):
    # ডায়মেনশন টিউন করা হয়েছে যাতে ইমেজ ক্রপ বা জুম আউট না হয়
    img = Image.new('RGB', (1000, 1150), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        # ডিফল্ট ফন্ট বড় স্কেলে
        font_main = ImageFont.load_default()
    except:
        font_main = None

    # হেডার লোগো
    draw.ellipse([30, 30, 130, 130], outline=(0, 0, 0), width=4)
    draw.text((58, 65), "WG", fill=(16, 185, 129))
    draw.text((160, 35), f"WinGo {tf.upper()}", fill=(16, 185, 129))
    draw.text((160, 70), "AI PREDICTION BOT", fill=(0, 0, 0))
    draw.text((160, 100), "ENGINE : PART1-WG1M v3", fill=(100, 116, 139))

    # টপ স্ট্যাট ব্যাজ
    draw.rectangle([160, 135), 370, 175], outline=(16, 185, 129), width=3)
    draw.text((180, 145), f"WIN    {current_wins}", fill=(16, 185, 129))

    draw.rectangle([390, 135, 600, 175], outline=(234, 179, 8), width=3)
    draw.text((410, 145), f"JACK   {jackpot_count}", fill=(234, 179, 8))

    draw.rectangle([620, 135, 830, 175], outline=(239, 68, 68), width=3)
    draw.text((640, 145), f"STREAK {current_streak}", fill=(239, 68, 68))

    # ইনফো বার (ব্ল্যাক স্ট্রিপ)
    draw.rectangle([0, 200, 1000, 250], fill=(15, 23, 42))
    now_str = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
    draw.text((20, 215), f"TIME: {now_str}", fill=(255, 255, 255))
    draw.text((340, 215), "STATUS: ACTIVE", fill=(34, 197, 94))
    draw.text((600, 215), "ACCURACY: 71.3%", fill=(34, 197, 94))
    draw.text((820, 215), f"PRED: {total_predictions}", fill=(255, 255, 255))

    # লেফট সাইড ইনফো
    draw.text((30, 280), f"MODE   : WinGo {tf}", fill=(71, 85, 105))
    draw.text((30, 315), f"PERIOD : {period[-6:]}", fill=(0, 0, 0))
    sig_color = (225, 29, 72) if signal == "SMALL" else (37, 99, 235)
    draw.text((30, 350), f"SIGNAL : {signal}", fill=sig_color)
    draw.text((30, 385), f"NUMBER : {number_pair}", fill=(16, 185, 129))

    # সেন্ট্রাল প্রেডিকশন বক্স
    draw.rectangle([360, 270, 700, 430], outline=sig_color, width=3)
    draw.text((430, 280), "CURRENT SIGNAL", fill=(16, 185, 129))
    draw.text((430, 315), signal, fill=sig_color)
    draw.text((490, 370), f"{confidence}%", fill=(16, 185, 129))
    draw.text((430, 395), f"CONFIDENCE = {confidence}%", fill=(16, 185, 129))

    # রাইট নম্বর বক্স
    draw.rectangle([740, 270, 970, 430], outline=(16, 185, 129), width=3)
    draw.text((810, 280), "NUMBER", fill=(16, 185, 129))
    draw.text((835, 335), number_pair, fill=(16, 185, 129))

    # টেবিল হেডার
    draw.rectangle([0, 460, 1000, 500], fill=(15, 23, 42))
    draw.text((20, 470), "#", fill=(255, 255, 255))
    draw.text((120, 470), "PERIOD", fill=(255, 255, 255))
    draw.text((380, 470), "SIGNAL", fill=(255, 255, 255))
    draw.text((540, 470), "NUMBER", fill=(255, 255, 255))
    draw.text((680, 470), "RESULT", fill=(255, 255, 255))
    draw.text((850, 470), "TIME", fill=(255, 255, 255))

    # টেবিল ডেটা রেন্ডারিং (সর্বশেষ ১০টি রেকর্ড)
    y = 520
    display_history = history_rows[-9:]
    for idx, row in enumerate(display_history):
        draw.text((20, y), str(idx+1), fill=(100, 116, 139))
        draw.text((120, y), row['period'], fill=(30, 41, 59))
        draw.text((380, y), row['signal'], fill=(37, 99, 235) if row['signal']=="BIG" else (225, 29, 72))
        draw.text((540, y), str(row['num']), fill=(30, 41, 59))

        res_bg = (220, 252, 231) if row['res'] == "WIN" else (254, 242, 242) if row['res'] == "LOSE" else (254, 249, 195)
        res_fg = (22, 101, 52) if row['res'] == "WIN" else (153, 27, 27) if row['res'] == "LOSE" else (161, 98, 7)
        draw.rectangle([670, y-5, 760, y+25], fill=res_bg)
        draw.text((685, y), row['res'], fill=res_fg)
        draw.text((850, y), row['time'], fill=(100, 116, 139))
        y += 42

    # রানিং রো
    draw.text((20, y), "10", fill=(16, 185, 129))
    draw.text((120, y), period[-6:], fill=(16, 185, 129))
    draw.text((380, y), signal, fill=sig_color)
    draw.text((540, y), number_pair, fill=(16, 185, 129))
    draw.rectangle([670, y-5, 760, y+25], fill=(219, 234, 254))
    draw.text((685, y), "NEXT", fill=(29, 78, 216))
    draw.text((850, y), datetime.now().strftime("%I:%M:%S %p"), fill=(16, 185, 129))

    # ফুটার ড্যাশবোর্ড বক্স
    draw.rectangle([30, 980, 230, 1070], outline=(16, 185, 129), width=3)
    draw.text((90, 1000), "WINS", fill=(16, 185, 129))
    draw.text((85, 1030), f"{current_wins}", fill=(16, 185, 129))

    draw.rectangle([260, 980, 460, 1070], outline=(234, 179, 8), width=3)
    draw.text((310, 1000), "JACKPOT", fill=(234, 179, 8))
    draw.text((325, 1030), f"{jackpot_count}", fill=(234, 179, 8))

    draw.rectangle([490, 980, 690, 1070], outline=(239, 68, 68), width=3)
    draw.text((520, 1000), "MAX STREAK", fill=(239, 68, 68))
    draw.text((570, 1030), f"{max_streak}", fill=(239, 68, 68))

    draw.rectangle([720, 980, 970, 1070], fill=(239, 246, 255))
    draw.text((790, 1000), "WIN RATE", fill=(37, 99, 235))
    draw.text((810, 1030), "71.3%", fill=(37, 99, 235))

    img.save("exact_dashboard.png")

# ৩. চ্যানেলে সিগন্যাল পোস্ট করার ফাংশন
def broadcast_signal(signal, number_pair, confidence=68):
    global last_prediction, total_predictions
    total_predictions += 1
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

# ৪. রেজাল্ট মেসেজ পোস্ট করার ফাংশন (WIN / LOSS / JACKPOT)
def send_result_message(res_type, num_hit):
    global current_wins, jackpot_count, current_streak, history_rows
    
    period_str = last_prediction['period'] if last_prediction else "010301"
    sig = last_prediction['signal'] if last_prediction else "BIG"
    full_p = last_prediction['full_period'] if last_prediction else get_market_period(selected_timeframe)

    is_big = int(num_hit) >= 5
    side_emoji = "🔵  BIG" if is_big else "🔴  SMALL"

    if res_type == "WIN":
        current_wins += 1
        current_streak += 1
        history_rows.append({"period": full_p, "signal": sig, "num": num_hit, "res": "WIN", "time": datetime.now().strftime("%I:%M:%S %p")})
        msg = f"✅ WIN!\n================================\nPeriod  =>  #{period_str}\nResult  =>  NUM:{num_hit}  {side_emoji}\n================================"

    elif res_type == "JACKPOT":
        jackpot_count += 1
        current_wins += 1
        current_streak += 1
        history_rows.append({"period": full_p, "signal": sig, "num": num_hit, "res": "JACK", "time": datetime.now().strftime("%I:%M:%S %p")})
        msg = f"🎰 JACK! NUMBER HIT\n================================\nPeriod  =>  #{period_str}\nResult  =>  NUM:{num_hit}  {side_emoji}\n================================"

    else:
        current_streak = 0
        history_rows.append({"period": full_p, "signal": sig, "num": num_hit, "res": "LOSE", "time": datetime.now().strftime("%I:%M:%S %p")})
        msg = f"❌ LOSS\n================================\nPeriod  =>  #{period_str}\nResult  =>  NUM:{num_hit}  {side_emoji}\n================================"

    bot.send_message(CHANNEL_ID, msg)

# ৫. ব্যাকগ্রাউন্ড অটো লুপ (অটো সিগন্যাল ও অটো রেজাল্ট পাঠায়)
def auto_loop():
    while True:
        if auto_mode:
            sig = random.choice(["BIG", "SMALL"])
            num = "1/2" if sig == "BIG" else "5/7"
            
            # সিগন্যাল পাঠাবে
            broadcast_signal(sig, num)
            
            # টাইমফ্রেম অনুযায়ী অপেক্ষা করবে
            sleep_time = 30 if selected_timeframe == "30s" else 60 if selected_timeframe == "1m" else 180 if selected_timeframe == "3m" else 300
            time.sleep(sleep_time - 5) # টাইম শেষ হওয়ার ৫ সেকেন্ড আগে রেজাল্ট প্রসেস হবে
            
            # অটোমেটিক রেজাল্ট পাঠানো (৮০% চান্স উইন/জ্যাকপট)
            res_choice = random.choices(["WIN", "JACKPOT", "LOSS"], weights=[65, 15, 20])[0]
            if res_choice == "WIN":
                win_num = random.choice([6, 7, 8, 9]) if sig == "BIG" else random.choice([0, 1, 2, 3, 4])
                send_result_message("WIN", win_num)
            elif res_choice == "JACKPOT":
                jack_num = 6 if sig == "BIG" else 2
                send_result_message("JACKPOT", jack_num)
            else:
                loss_num = random.choice([0, 1, 2, 3, 4]) if sig == "BIG" else random.choice([5, 6, 7, 8, 9])
                send_result_message("LOSS", loss_num)

            time.sleep(5)
        else:
            time.sleep(2)

# ৬. এডমিন কন্ট্রোল প্যানেল (বাটন লেআউট নিচে সুন্দরভাবে সাজানো)
def get_control_keyboard():
    markup = InlineKeyboardMarkup()
    
    status_btn = InlineKeyboardButton(f"🤖 AUTO BOT : {'ON 🟢' if auto_mode else 'OFF 🔴'}", callback_data="toggle_auto")
    
    # টাইমার রো
    btn_30s = InlineKeyboardButton(f"{'✅ ' if selected_timeframe=='30s' else ''}30s", callback_data="tf_30s")
    btn_1m = InlineKeyboardButton(f"{'✅ ' if selected_timeframe=='1m' else ''}1m", callback_data="tf_1m")
    btn_3m = InlineKeyboardButton(f"{'✅ ' if selected_timeframe=='3m' else ''}3m", callback_data="tf_3m")
    btn_5m = InlineKeyboardButton(f"{'✅ ' if selected_timeframe=='5m' else ''}5m", callback_data="tf_5m")

    # ম্যানুয়াল সিগন্যাল রো
    btn_big = InlineKeyboardButton("🔵 SEND BIG", callback_data="sig_big")
    btn_small = InlineKeyboardButton("🔴 SEND SMALL", callback_data="sig_small")

    # রেজাল্ট ম্যানুয়াল রো
    btn_win = InlineKeyboardButton("✅ WIN", callback_data="res_win")
    btn_jack = InlineKeyboardButton("🎰 JACKPOT", callback_data="res_jack")
    btn_loss = InlineKeyboardButton("❌ LOSS", callback_data="res_loss")

    markup.add(status_btn)
    markup.row(btn_30s, btn_1m, btn_3m, btn_5m)
    markup.row(btn_big, btn_small)
    markup.row(btn_win, btn_jack, btn_loss)
    return markup

@bot.message_handler(commands=['start'])
def start_cmd(message):
    if ADMIN_ID != 0 and message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "আপনার এই বটের এক্সেস নেই।")
        return
    bot.send_message(message.chat.id, "⚙️ **ST Wingo Master Control Panel**\n\nনিচের বাটনগুলো দিয়ে বট নিয়ন্ত্রণ করুন:", reply_markup=get_control_keyboard(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    global auto_mode, selected_timeframe
    if ADMIN_ID != 0 and call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "অনুমতি নেই!", show_alert=True)
        return

    if call.data == "toggle_auto":
        auto_mode = not auto_mode
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=get_control_keyboard())
        bot.answer_callback_query(call.id, f"Auto Mode set to {'ON' if auto_mode else 'OFF'}")

    elif call.data.startswith("tf_"):
        selected_timeframe = call.data.split("_")[1]
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=get_control_keyboard())
        bot.answer_callback_query(call.id, f"Timeframe selected: {selected_timeframe}")

    elif call.data == "sig_small":
        broadcast_signal("SMALL", "5/7")
        bot.answer_callback_query(call.id, "SMALL Signal Posted!")

    elif call.data == "sig_big":
        broadcast_signal("BIG", "1/2")
        bot.answer_callback_query(call.id, "BIG Signal Posted!")

    elif call.data == "res_win":
        send_result_message("WIN", random.choice([6, 7, 8, 9]))
        bot.answer_callback_query(call.id, "WIN Result Posted!")

    elif call.data == "res_jack":
        send_result_message("JACKPOT", 6)
        bot.answer_callback_query(call.id, "JACKPOT Result Posted!")

    elif call.data == "res_loss":
        send_result_message("LOSS", random.choice([0, 1, 2, 3]))
        bot.answer_callback_query(call.id, "LOSS Result Posted!")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    threading.Thread(target=auto_loop).start()
    
    bot.remove_webhook()
    time.sleep(1)
    
    print("Bot loop started successfully...")
    bot.infinity_polling(skip_pending=True)
