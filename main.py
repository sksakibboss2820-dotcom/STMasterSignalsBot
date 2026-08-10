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
    return "ST Signal Engine Running Successfully!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')
ADMIN_ID = int(os.environ.get('ADMIN_ID', '0'))

bot = telebot.TeleBot(BOT_TOKEN)

# গ্লোবাল স্টেট ও ট্র্যাকিং variables
auto_mode = False
selected_timeframe = "1m" # 30s, 1m, 3m, 5m
current_wins = 2594
jackpot_count = 725
current_streak = 1
max_streak = 21
total_predictions = 3639

last_prediction = None

# ডিফল্ট ডামি হিস্ট্রি (রেফারেন্স ইমেজের মতো)
history_rows = [
    {"period": "20260809100010288", "signal": "SMALL", "num": "1", "res": "WIN", "time": "10:29:42 AM"},
    {"period": "20260809100010290", "signal": "BIG", "num": "2", "res": "LOSE", "time": "10:29:42 AM"},
    {"period": "20260809100010291", "signal": "BIG", "num": "7", "res": "WIN", "time": "10:29:42 AM"},
    {"period": "20260809100010292", "signal": "BIG", "num": "2", "res": "JACK", "time": "10:29:42 AM"},
    {"period": "20260809100010293", "signal": "BIG", "num": "2", "res": "JACK", "time": "10:29:42 AM"},
    {"period": "20260809100010295", "signal": "SMALL", "num": "8", "res": "LOSE", "time": "10:29:42 AM"},
    {"period": "20260809100010296", "signal": "SMALL", "num": "1", "res": "WIN", "time": "10:29:42 AM"},
    {"period": "20260809100010297", "signal": "BIG", "num": "0", "res": "LOSE", "time": "10:29:42 AM"},
    {"period": "20260809100010299", "signal": "BIG", "num": "8", "res": "WIN", "time": "10:29:43 AM"},
]

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

# পারফেক্ট ইউজার লেআউট ইমেজ জেনারেটর
def generate_exact_dashboard(period, signal, confidence, number_pair, tf):
    img = Image.new('RGB', (1000, 1150), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    tf_label = "30 Sec" if tf=="30s" else "1 Min" if tf=="1m" else "3 Min" if tf=="3m" else "5 Min"

    # ১. হেডার লোগো
    draw.ellipse([20, 20, 130, 130], outline=(0, 0, 0), width=4)
    draw.text((43, 50), "WG", fill=(16, 185, 129))
    draw.text((150, 20), f"WinGo {tf_label}", fill=(16, 185, 129))
    draw.text((150, 65), "AI PREDICTION BOT", fill=(0, 0, 0))
    draw.text((150, 95), "ENGINE : PART5-WG1M v3", fill=(100, 116, 139))

    # টপ স্ট্যাট ব্যাজ (৩টি বক্স)
    # WIN
    draw.rectangle([148, 120, 352, 162], outline=(16, 185, 129), width=2)
    draw.text((160, 128), "WIN", fill=(16, 185, 129))
    draw.text((284, 128), f"{current_wins}", fill=(16, 185, 129))

    # JACK
    draw.rectangle([368, 120, 572, 162], outline=(234, 179, 8), width=2)
    draw.text((380, 128), "JACK", fill=(234, 179, 8))
    draw.text((518, 128), f"{jackpot_count}", fill=(234, 179, 8))

    # STREAK
    draw.rectangle([586, 120, 790, 162], outline=(239, 68, 68), width=2)
    draw.text((598, 128), "STREAK", fill=(239, 68, 68))
    draw.text((764, 128), f"{current_streak}", fill=(239, 68, 68))

    # ২. ইনফো বার (ব্ল্যাক স্ট্রিপ)
    draw.rectangle([0, 175, 1000, 230], fill=(10, 15, 25))
    now_str = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
    
    draw.text((10, 182), "TIME", fill=(148, 163, 184))
    draw.text((10, 198), now_str, fill=(255, 255, 255))

    draw.text((260, 182), "STATUS", fill=(148, 163, 184))
    draw.text((260, 198), "ACTIVE", fill=(34, 197, 94))

    draw.text((512, 182), "ACCURACY", fill=(148, 163, 184))
    draw.text((512, 198), "71.3%", fill=(34, 197, 94))

    draw.text((762, 182), "PREDICTIONS", fill=(148, 163, 184))
    draw.text((762, 198), f"{total_predictions}", fill=(255, 255, 255))

    # ৩. কারেন্ট সিগন্যাল প্যানেল
    draw.text((28, 245), "MODE", fill=(100, 116, 139))
    draw.text((120, 245), f": WinGo {tf_label}", fill=(0, 0, 0))

    draw.text((28, 275), "PERIOD", fill=(100, 116, 139))
    draw.text((120, 275), f": {period[-6:]}", fill=(0, 0, 0))

    sig_color = (225, 29, 72) if signal == "SMALL" else (37, 99, 235)
    draw.text((28, 305), "SIGNAL", fill=(100, 116, 139))
    draw.text((120, 305), f": {signal}", fill=sig_color)

    draw.text((28, 335), "NUMBER", fill=(100, 116, 139))
    draw.text((120, 335), f": {number_pair}", fill=(16, 185, 129))

    # সেন্ট্রাল সিগন্যাল বক্স
    draw.rectangle([354, 245, 686, 385], outline=sig_color, width=2)
    draw.text((366, 250), "->", fill=(16, 185, 129))
    draw.text((446, 250), "CURRENT SIGNAL", fill=(16, 185, 129))
    draw.text((660, 250), "<-", fill=(16, 185, 129))

    draw.text((400, 275), signal, fill=sig_color)
    draw.text((480, 335), f"{confidence}%", fill=(16, 185, 129))
    draw.text((426, 368), f"CONFIDENCE = {confidence}%", fill=(16, 185, 129))

    # ডানদিকের নম্বর বক্স
    draw.rectangle([815, 250, 982, 382], outline=(16, 185, 129), width=2)
    draw.text((862, 258), "NUMBER", fill=(16, 185, 129))
    draw.text((866, 285), number_pair, fill=(16, 185, 129))
    draw.text((830, 322), "OPPOSITE SIDE", fill=(16, 185, 129))
    opp_text = "SMALL NUMBERS" if signal=="BIG" else "BIG NUMBERS"
    draw.text((840, 338), opp_text, fill=(225, 29, 72))

    # ৪. হিস্ট্রি টেবিল
    draw.rectangle([0, 410, 1000, 436], fill=(10, 15, 25))
    draw.text((26, 416), "#", fill=(255, 255, 255))
    draw.text((172, 416), "PERIOD", fill=(255, 255, 255))
    draw.text((380, 416), "SIGNAL", fill=(255, 255, 255))
    draw.text((495, 416), "NUMBER", fill=(255, 255, 255))
    draw.text((621, 416), "RESULT", fill=(255, 255, 255))
    draw.text((838, 416), "TIME", fill=(255, 255, 255))

    y = 445
    display_history = history_rows[-9:]
    for idx, row in enumerate(display_history):
        bg_row = (248, 250, 252) if idx % 2 == 1 else (255, 255, 255)
        draw.rectangle([0, y-5, 1000, y+35], fill=bg_row)

        draw.text((26, y+5), str(idx+1), fill=(100, 116, 139))
        draw.text((122, y+5), row['period'], fill=(30, 41, 59))
        
        s_col = (225, 29, 72) if row['signal'] == "SMALL" else (37, 99, 235)
        draw.text((385, y+5), row['signal'], fill=s_col)
        draw.text((526, y+5), str(row['num']), fill=(30, 41, 59))

        # রেজাল্ট ব্যাজ
        res = row['res']
        if res == "WIN":
            draw.rectangle([594, y+1, 668, y+27], fill=(220, 252, 231))
            draw.text((618, y+5), "WIN", fill=(22, 101, 52))
        elif res == "LOSE":
            draw.rectangle([594, y+1, 668, y+27], fill=(254, 226, 226))
            draw.text((614, y+5), "LOSE", fill=(185, 28, 28))
        else: # JACK
            draw.rectangle([594, y+1, 668, y+27], fill=(254, 249, 195))
            draw.text((614, y+5), "JACK", fill=(161, 98, 7))

        draw.text((812, y+5), row['time'], fill=(100, 116, 139))
        y += 42

    # ১০ নম্বর রানিং রো
    draw.rectangle([0, y-5, 1000, y+35], fill=(255, 255, 255))
    draw.text((22, y+5), "10", fill=(16, 185, 129))
    draw.text((172, y+5), period[-6:], fill=(16, 185, 129))
    draw.text((385, y+5), signal, fill=sig_color)
    draw.text((520, y+5), number_pair, fill=(16, 185, 129))

    draw.rectangle([594, y+1, 668, y+27], fill=(219, 234, 254))
    draw.text((614, y+5), "NEXT", fill=(29, 78, 216))

    draw.text((806, y+5), datetime.now().strftime("%I:%M:%S %p"), fill=(16, 185, 129))

    # ৫. ফুটারে ৫টি ইনফো কার্ড
    fy = 885
    # WINS
    draw.rectangle([18, fy, 204, fy+70], outline=(16, 185, 129), width=2)
    draw.text((93, fy+10), "WINS", fill=(16, 185, 129))
    draw.text((82, fy+32), f"{current_wins}", fill=(16, 185, 129))

    # JACKPOT
    draw.rectangle([214, fy, 400, fy+70], outline=(234, 179, 8), width=2)
    draw.text((276, fy+10), "JACKPOT", fill=(234, 179, 8))
    draw.text((285, fy+32), f"{jackpot_count}", fill=(234, 179, 8))

    # MAX STREAK
    draw.rectangle([410, fy, 596, fy+70], outline=(239, 68, 68), width=2)
    draw.text((454, fy+10), "MAX STREAK", fill=(239, 68, 68))
    draw.text((488, fy+32), f"{max_streak}", fill=(239, 68, 68))

    # WIN RATE
    draw.rectangle([606, fy, 792, fy+70], fill=(239, 246, 255))
    draw.text((662, fy+10), "WIN RATE", fill=(37, 99, 235))
    draw.text((658, fy+32), "71.3%", fill=(37, 99, 235))

    # CONFIDENCE
    draw.rectangle([802, fy, 982, fy+70], fill=(243, 232, 255))
    draw.text((845, fy+10), "CONFIDENCE", fill=(147, 51, 234))
    draw.text((862, fy+32), f"{confidence}%", fill=(147, 51, 234))

    # ফুটার স্ট্রিপ
    draw.rectangle([0, 960, 1000, 1000], fill=(10, 15, 25))
    draw.text((10, 965), f"WinGo {tf_label}", fill=(34, 197, 94))
    draw.text((10, 980), "AI PREDICTION BOT", fill=(148, 163, 184))

    draw.text((448, 972), "100% SECURE", fill=(255, 255, 255))
    draw.text((828, 972), "MADE FOR WINNERS", fill=(234, 179, 8))

    img.save("exact_dashboard.png")

# সিগন্যাল পোস্ট
def broadcast_signal(signal, number_pair, confidence=88):
    global last_prediction, total_predictions
    total_predictions += 1
    period = get_market_period(selected_timeframe)
    generate_exact_dashboard(period, signal, confidence, number_pair, selected_timeframe)

    tf_label = "30S" if selected_timeframe=="30s" else "1M" if selected_timeframe=="1m" else "3M" if selected_timeframe=="3m" else "5M"

    caption = (
        f"👾 MODE : WINGO {tf_label}\n"
        f"╭────────────────╮\n"
        f"🎰 PERIOD : {period[-6:]}\n"
        f"⚙️ LOGIC  : PART 5 | ENTRY 1\n\n"
        f"┣ 📈 SIGNAL = {'🔴 SMALL' if signal == 'SMALL' else '🔵 BIG'}\n"
        f"┣ \n"
        f"┣ 🛡 NUMBER = {number_pair}\n"
        f"┣ \n"
        f"╰────────────────╯"
    )

    with open("exact_dashboard.png", "rb") as photo:
        bot.send_photo(CHANNEL_ID, photo, caption=caption)

    last_prediction = {"period": period[-6:], "signal": signal, "full_period": period}

# রেজাল্ট পোস্ট
def send_result_message(res_type, num_hit):
    global current_wins, jackpot_count, current_streak, history_rows
    
    period_str = last_prediction['period'] if last_prediction else "010300"
    sig = last_prediction['signal'] if last_prediction else "SMALL"
    full_p = last_prediction['full_period'] if last_prediction else get_market_period(selected_timeframe)

    is_big = int(num_hit) >= 5
    side_emoji = "🔵  BIG" if is_big else "🔴  SMALL"
    now_time = datetime.now().strftime("%I:%M:%S %p")

    if res_type == "WIN":
        current_wins += 1
        current_streak += 1
        history_rows.append({"period": full_p, "signal": sig, "num": str(num_hit), "res": "WIN", "time": now_time})
        msg = f"✅ WIN!\n================================\nPeriod  =>  #{period_str}\nResult  =>  NUM:{num_hit}  {side_emoji}\n================================"

    elif res_type == "JACKPOT":
        jackpot_count += 1
        current_wins += 1
        current_streak += 1
        history_rows.append({"period": full_p, "signal": sig, "num": str(num_hit), "res": "JACK", "time": now_time})
        msg = f"🎰 JACK! NUMBER HIT\n================================\nPeriod  =>  #{period_str}\nResult  =>  NUM:{num_hit}  {side_emoji}\n================================"

    else:
        current_streak = 0
        history_rows.append({"period": full_p, "signal": sig, "num": str(num_hit), "res": "LOSE", "time": now_time})
        msg = f"❌ LOSS\n================================\nPeriod  =>  #{period_str}\nResult  =>  NUM:{num_hit}  {side_emoji}\n================================"

    bot.send_message(CHANNEL_ID, msg)

# ব্যাকগ্রাউন্ড লুপ (অটোমেটিক রান হবে)
def auto_loop():
    while True:
        if auto_mode:
            sig = random.choice(["BIG", "SMALL"])
            num = "1/2" if sig == "BIG" else "7/6"
            
            broadcast_signal(sig, num)
            
            sleep_time = 30 if selected_timeframe == "30s" else 60 if selected_timeframe == "1m" else 180 if selected_timeframe == "3m" else 300
            time.sleep(sleep_time - 5)
            
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

# এডমিন কন্ট্রোল বাটন
def get_control_keyboard():
    markup = InlineKeyboardMarkup()
    
    status_btn = InlineKeyboardButton(f"🤖 AUTO BOT : {'ON 🟢' if auto_mode else 'OFF 🔴'}", callback_data="toggle_auto")
    
    btn_30s = InlineKeyboardButton(f"{'✅ ' if selected_timeframe=='30s' else ''}30s", callback_data="tf_30s")
    btn_1m = InlineKeyboardButton(f"{'✅ ' if selected_timeframe=='1m' else ''}1m", callback_data="tf_1m")
    btn_3m = InlineKeyboardButton(f"{'✅ ' if selected_timeframe=='3m' else ''}3m", callback_data="tf_3m")
    btn_5m = InlineKeyboardButton(f"{'✅ ' if selected_timeframe=='5m' else ''}5m", callback_data="tf_5m")

    btn_big = InlineKeyboardButton("🔵 SEND BIG", callback_data="sig_big")
    btn_small = InlineKeyboardButton("🔴 SEND SMALL", callback_data="sig_small")

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
        bot.reply_to(message, "আপনার এক্সেস নেই।")
        return
    bot.send_message(message.chat.id, "⚙️ **ST Wingo Master Control Panel**\n\nনিচের কন্ট্রোল বাটনগুলো দিয়ে সার্ভিস পরিচালনা করুন:", reply_markup=get_control_keyboard(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    global auto_mode, selected_timeframe
    if ADMIN_ID != 0 and call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "অনুমতি নেই!", show_alert=True)
        return

    if call.data == "toggle_auto":
        auto_mode = not auto_mode
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=get_control_keyboard())
        bot.answer_callback_query(call.id, f"Auto Mode: {'ON' if auto_mode else 'OFF'}")

    elif call.data.startswith("tf_"):
        selected_timeframe = call.data.split("_")[1]
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=get_control_keyboard())
        bot.answer_callback_query(call.id, f"Timeframe: {selected_timeframe}")

    elif call.data == "sig_small":
        broadcast_signal("SMALL", "7/6")
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
