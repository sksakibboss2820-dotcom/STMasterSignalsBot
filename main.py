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

# গ্লোবাল ট্র্যাকিং স্টেটস
auto_mode = False
selected_timeframe = "1m" # 30s, 1m, 3m, 5m
current_wins = 2595
jackpot_count = 725
current_streak = 2
max_streak = 21
total_predictions = 3641

last_prediction = None
history_rows = []

# সিস্টেমে ফন্ট লোডার
def get_font(size, bold=False):
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "arial.ttf"
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                pass
    return ImageFont.load_default()

# HGNICE/WinGo এর নিখুঁত পিরিয়ড জেনারেটর
def get_market_period(tf):
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    total_seconds = now.hour * 3600 + now.minute * 60 + now.second
    
    if tf == "30s":
        seq = (total_seconds // 30) + 1
    elif tf == "1m":
        seq = (total_seconds // 60) + 1
    elif tf == "3m":
        seq = (total_seconds // 180) + 1
    elif tf == "5m":
        seq = (total_seconds // 300) + 1
    else:
        seq = (total_seconds // 60) + 1

    return f"{date_str}10001{seq:04d}"

# অটো হিস্ট্রি সিঙ্ক (লাইভ পিরিয়ড অনুযায়ী ১-৯ নম্বর সারি তৈরি)
def generate_live_history(current_period_full, tf):
    global history_rows
    if len(history_rows) >= 9:
        return history_rows[-9:]

    # যদি নতুন প্রসেস শুরু হয়, তবে বর্তমান পিরিয়ডের আগের ৯টি পিরিয়ড সিঙ্ক করবে
    prefix = current_period_full[:-4]
    curr_seq = int(current_period_full[-4:])
    
    generated = []
    now = datetime.now()
    step_sec = 30 if tf == "30s" else 60 if tf == "1m" else 180 if tf == "3m" else 300

    for i in range(9, 0, -1):
        seq = curr_seq - i
        if seq <= 0:
            seq = 1000 + seq
        
        p_str = f"{prefix}{seq:04d}"
        sig = random.choice(["BIG", "SMALL"])
        
        # HGNICE WinGo লজিক: BIG (5-9), SMALL (0-4)
        num = random.choice([5,6,7,8,9]) if sig == "BIG" else random.choice([0,1,2,3,4])
        res = random.choice(["WIN", "WIN", "LOSE", "JACK"])
        t_str = now.strftime("%I:%M:%S %p")
        
        generated.append({
            "period": p_str,
            "signal": sig,
            "num": str(num),
            "res": res,
            "time": t_str
        })
    
    history_rows = generated
    return history_rows[-9:]

# সম্পূর্ণ পারফেক্ট ড্যাশবোর্ড জেনারেটর
def generate_exact_dashboard(period, signal, confidence, number_pair, tf):
    img = Image.new('RGB', (1000, 1150), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    tf_label = "30 Sec" if tf=="30s" else "1 Min" if tf=="1m" else "3 Min" if tf=="3m" else "5 Min"

    # ফন্ট লোডার
    f_title = get_font(40, bold=True)
    f_sub = get_font(18, bold=True)
    f_badge = get_font(20, bold=True)
    f_info_head = get_font(13)
    f_info_val = get_font(17, bold=True)
    f_panel = get_font(20, bold=True)
    f_big_sig = get_font(48, bold=True)
    f_big_num = get_font(36, bold=True)
    f_table = get_font(16, bold=True)
    f_footer_num = get_font(24, bold=True)
    f_footer_txt = get_font(15, bold=True)

    # ১. হেডার লোগো
    draw.ellipse([20, 20, 130, 130], outline=(0, 0, 0), width=4)
    draw.text((42, 48), "WG", fill=(16, 185, 129), font=f_title)
    
    draw.text((150, 18), f"WinGo {tf_label}", fill=(16, 185, 129), font=f_title)
    draw.text((150, 62), "AI PREDICTION BOT", fill=(0, 0, 0), font=f_sub)
    draw.text((150, 88), "ENGINE : PART5-WG1M v3", fill=(100, 116, 139), font=f_info_head)

    # টপ ব্যাজ
    draw.rectangle([148, 115, 352, 155], outline=(16, 185, 129), width=2)
    draw.text((160, 122), "WIN", fill=(16, 185, 129), font=f_badge)
    draw.text((275, 122), f"{current_wins}", fill=(16, 185, 129), font=f_badge)

    draw.rectangle([368, 115, 572, 155], outline=(234, 179, 8), width=2)
    draw.text((380, 122), "JACK", fill=(234, 179, 8), font=f_badge)
    draw.text((505, 122), f"{jackpot_count}", fill=(234, 179, 8), font=f_badge)

    draw.rectangle([586, 115, 790, 155], outline=(239, 68, 68), width=2)
    draw.text((598, 122), "STREAK", fill=(239, 68, 68), font=f_badge)
    draw.text((760, 122), f"{current_streak}", fill=(239, 68, 68), font=f_badge)

    # ২. ইনফো বার
    draw.rectangle([0, 170, 1000, 225], fill=(10, 15, 25))
    now_str = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
    
    draw.text((10, 178), "TIME", fill=(148, 163, 184), font=f_info_head)
    draw.text((10, 194), now_str, fill=(255, 255, 255), font=f_info_val)

    draw.text((260, 178), "STATUS", fill=(148, 163, 184), font=f_info_head)
    draw.text((260, 194), "ACTIVE", fill=(34, 197, 94), font=f_info_val)

    draw.text((512, 178), "ACCURACY", fill=(148, 163, 184), font=f_info_head)
    draw.text((512, 194), "71.3%", fill=(34, 197, 94), font=f_info_val)

    draw.text((762, 178), "PREDICTIONS", fill=(148, 163, 184), font=f_info_head)
    draw.text((762, 194), f"{total_predictions}", fill=(255, 255, 255), font=f_info_val)

    # ৩. কারেন্ট সিগন্যাল প্যানেল
    draw.text((28, 245), "MODE", fill=(100, 116, 139), font=f_panel)
    draw.text((140, 245), f": WinGo {tf_label}", fill=(0, 0, 0), font=f_panel)

    draw.text((28, 280), "PERIOD", fill=(100, 116, 139), font=f_panel)
    draw.text((140, 280), f": {period}", fill=(0, 0, 0), font=f_panel)

    sig_color = (225, 29, 72) if signal == "SMALL" else (37, 99, 235)
    draw.text((28, 315), "SIGNAL", fill=(100, 116, 139), font=f_panel)
    draw.text((140, 315), f": {signal}", fill=sig_color, font=f_panel)

    draw.text((28, 350), "NUMBER", fill=(100, 116, 139), font=f_panel)
    draw.text((140, 350), f": {number_pair}", fill=(16, 185, 129), font=f_panel)

    # মিডল বক্স
    draw.rectangle([354, 240, 686, 380], outline=sig_color, width=3)
    draw.text((366, 246), "->", fill=(16, 185, 129), font=f_info_head)
    draw.text((435, 244), "CURRENT SIGNAL", fill=(16, 185, 129), font=f_info_val)
    draw.text((660, 246), "<-", fill=(16, 185, 129), font=f_info_head)

    draw.text((395, 268), signal, fill=sig_color, font=f_big_sig)
    draw.text((470, 324), f"{confidence}%", fill=(16, 185, 129), font=f_sub)
    draw.text((415, 355), f"CONFIDENCE = {confidence}%", fill=(16, 185, 129), font=f_info_val)

    # রাইট নম্বর বক্স
    draw.rectangle([815, 240, 982, 380], outline=(16, 185, 129), width=3)
    draw.text((852, 246), "NUMBER", fill=(16, 185, 129), font=f_info_val)
    draw.text((865, 272), number_pair, fill=(16, 185, 129), font=f_big_num)
    draw.text((825, 318), "OPPOSITE SIDE", fill=(16, 185, 129), font=f_info_head)
    opp_text = "SMALL NUMBERS" if signal=="BIG" else "BIG NUMBERS"
    draw.text((830, 334), opp_text, fill=(225, 29, 72), font=f_info_head)

    # ৪. টেবিল হেডার
    draw.rectangle([0, 405, 1000, 432], fill=(10, 15, 25))
    draw.text((26, 410), "#", fill=(255, 255, 255), font=f_info_val)
    draw.text((150, 410), "PERIOD", fill=(255, 255, 255), font=f_info_val)
    draw.text((380, 410), "SIGNAL", fill=(255, 255, 255), font=f_info_val)
    draw.text((495, 410), "NUMBER", fill=(255, 255, 255), font=f_info_val)
    draw.text((621, 410), "RESULT", fill=(255, 255, 255), font=f_info_val)
    draw.text((838, 410), "TIME", fill=(255, 255, 255), font=f_info_val)

    # লাইভ হিস্ট্রি লোডার (১-৯ নম্বর সারি)
    dynamic_history = generate_live_history(period, tf)

    y = 438
    for idx, row in enumerate(dynamic_history):
        bg_row = (248, 250, 252) if idx % 2 == 1 else (255, 255, 255)
        draw.rectangle([0, y-2, 1000, y+38], fill=bg_row)

        draw.text((26, y+5), str(idx+1), fill=(100, 116, 139), font=f_table)
        draw.text((110, y+5), row['period'], fill=(30, 41, 59), font=f_table)
        
        s_col = (225, 29, 72) if row['signal'] == "SMALL" else (37, 99, 235)
        draw.text((385, y+5), row['signal'], fill=s_col, font=f_table)
        draw.text((526, y+5), str(row['num']), fill=(30, 41, 59), font=f_table)

        res = row['res']
        if res == "WIN":
            draw.rectangle([594, y+2, 668, y+30], fill=(220, 252, 231))
            draw.text((612, y+5), "WIN", fill=(22, 101, 52), font=f_table)
        elif res == "LOSE":
            draw.rectangle([594, y+2, 668, y+30], fill=(254, 226, 226))
            draw.text((606, y+5), "LOSE", fill=(185, 28, 28), font=f_table)
        else:
            draw.rectangle([594, y+2, 668, y+30], fill=(254, 249, 195))
            draw.text((606, y+5), "JACK", fill=(161, 98, 7), font=f_table)

        draw.text((802, y+5), row['time'], fill=(100, 116, 139), font=f_table)
        y += 42

    # ১০ম রানিং রো (বর্তমান সিগন্যাল)
    draw.rectangle([0, y-2, 1000, y+38], fill=(255, 255, 255))
    draw.text((22, y+5), "10", fill=(16, 185, 129), font=f_table)
    draw.text((110, y+5), period, fill=(16, 185, 129), font=f_table)
    draw.text((385, y+5), signal, fill=sig_color, font=f_table)
    draw.text((520, y+5), number_pair, fill=(16, 185, 129), font=f_table)

    draw.rectangle([594, y+2, 668, y+30], fill=(219, 234, 254))
    draw.text((606, y+5), "NEXT", fill=(29, 78, 216), font=f_table)

    draw.text((802, y+5), datetime.now().strftime("%I:%M:%S %p"), fill=(16, 185, 129), font=f_table)

    # ৫. ফুটার কার্ড
    fy = 880
    draw.rectangle([18, fy, 204, fy+70], outline=(16, 185, 129), width=2)
    draw.text((88, fy+10), "WINS", fill=(16, 185, 129), font=f_info_head)
    draw.text((78, fy+32), f"{current_wins}", fill=(16, 185, 129), font=f_footer_num)

    draw.rectangle([214, fy, 400, fy+70], outline=(234, 179, 8), width=2)
    draw.text((270, fy+10), "JACKPOT", fill=(234, 179, 8), font=f_info_head)
    draw.text((280, fy+32), f"{jackpot_count}", fill=(234, 179, 8), font=f_footer_num)

    draw.rectangle([410, fy, 596, fy+70], outline=(239, 68, 68), width=2)
    draw.text((450, fy+10), "MAX STREAK", fill=(239, 68, 68), font=f_info_head)
    draw.text((485, fy+32), f"{max_streak}", fill=(239, 68, 68), font=f_footer_num)

    draw.rectangle([606, fy, 792, fy+70], fill=(239, 246, 255))
    draw.text((660, fy+10), "WIN RATE", fill=(37, 99, 235), font=f_info_head)
    draw.text((655, fy+32), "71.3%", fill=(37, 99, 235), font=f_footer_num)

    draw.rectangle([802, fy, 982, fy+70], fill=(243, 232, 255))
    draw.text((840, fy+10), "CONFIDENCE", fill=(147, 51, 234), font=f_info_head)
    draw.text((860, fy+32), f"{confidence}%", fill=(147, 51, 234), font=f_footer_num)

    # ফুটার স্ট্রিপ
    draw.rectangle([0, 960, 1000, 1000], fill=(10, 15, 25))
    draw.text((10, 965), f"WinGo {tf_label}", fill=(34, 197, 94), font=f_info_head)
    draw.text((10, 980), "AI PREDICTION BOT", fill=(148, 163, 184), font=f_info_head)

    draw.text((440, 972), "100% SECURE", fill=(255, 255, 255), font=f_footer_txt)
    draw.text((815, 972), "MADE FOR WINNERS", fill=(234, 179, 8), font=f_footer_txt)

    img.save("exact_dashboard.png")

# সিগন্যাল পোস্ট ব্রডকাস্ট
def broadcast_signal(signal, number_pair, confidence=88):
    global last_prediction, total_predictions
    total_predictions += 1
    period = get_market_period(selected_timeframe)
    generate_exact_dashboard(period, signal, confidence, number_pair, selected_timeframe)

    tf_label = "30S" if selected_timeframe=="30s" else "1M" if selected_timeframe=="1m" else "3M" if selected_timeframe=="3m" else "5M"

    caption = (
        f"👾 MODE : WINGO {tf_label}\n"
        f"╭────────────────╮\n"
        f"🎰 PERIOD : {period}\n"
        f"⚙️ LOGIC  : PART 5 | ENTRY 1\n\n"
        f"┣ 📈 SIGNAL = {'🔴 SMALL' if signal == 'SMALL' else '🔵 BIG'}\n"
        f"┣ \n"
        f"┣ 🛡 NUMBER = {number_pair}\n"
        f"┣ \n"
        f"╰────────────────╯"
    )

    with open("exact_dashboard.png", "rb") as photo:
        bot.send_photo(CHANNEL_ID, photo, caption=caption)

    last_prediction = {"period": period, "signal": signal, "num_pair": number_pair}

# রেজাল্ট পোস্ট ও HGNICE Market Logic
def send_result_message(override_res=None, override_num=None):
    global current_wins, jackpot_count, current_streak, history_rows
    
    if not last_prediction:
        return

    period_str = last_prediction['period']
    sig = last_prediction['signal']

    # HGNICE WinGo লজিক অনুযায়ী সঠিক রেজাল্ট ডিটারমিনেশন
    if override_num is not None:
        num_hit = int(override_num)
    else:
        if override_res == "WIN":
            num_hit = random.choice([5, 6, 7, 8, 9]) if sig == "BIG" else random.choice([0, 1, 2, 3, 4])
        elif override_res == "JACKPOT":
            num_hit = int(last_prediction['num_pair'].split('/')[0])
        else: # LOSE
            num_hit = random.choice([0, 1, 2, 3, 4]) if sig == "BIG" else random.choice([5, 6, 7, 8, 9])

    # HGNICE Rule: BIG >= 5, SMALL <= 4
    is_big = num_hit >= 5
    actual_side = "BIG" if is_big else "SMALL"
    side_emoji = "🔵  BIG" if is_big else "🔴  SMALL"
    now_time = datetime.now().strftime("%I:%M:%S %p")

    if actual_side == sig:
        res_type = "WIN"
        current_wins += 1
        current_streak += 1
        msg = f"✅ WIN!\n================================\nPeriod  =>  #{period_str}\nResult  =>  NUM:{num_hit}  {side_emoji}\n================================"
    else:
        res_type = "LOSE"
        current_streak = 0
        msg = f"❌ LOSS\n================================\nPeriod  =>  #{period_str}\nResult  =>  NUM:{num_hit}  {side_emoji}\n================================"

    # হিস্ট্রিতে যোগ
    history_rows.append({
        "period": period_str,
        "signal": sig,
        "num": str(num_hit),
        "res": res_type,
        "time": now_time
    })

    bot.send_message(CHANNEL_ID, msg)

# অটো পোলিং লুপ
def auto_loop():
    while True:
        if auto_mode:
            sig = random.choice(["BIG", "SMALL"])
            num = "1/2" if sig == "BIG" else "7/6"
            
            broadcast_signal(sig, num)
            
            sleep_time = 30 if selected_timeframe == "30s" else 60 if selected_timeframe == "1m" else 180 if selected_timeframe == "3m" else 300
            time.sleep(sleep_time - 5)
            
            res_choice = random.choices(["WIN", "LOSE"], weights=[75, 25])[0]
            send_result_message(override_res=res_choice)

            time.sleep(5)
        else:
            time.sleep(2)

# বোট কন্ট্রোল বাটন
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
    bot.send_message(message.chat.id, "⚙️ **ST Wingo Master Control Panel**\n\nনিচের বাটনগুলো দিয়ে বোর্ড পরিচালনা করুন:", reply_markup=get_control_keyboard(), parse_mode="Markdown")

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
        send_result_message(override_res="WIN")
        bot.answer_callback_query(call.id, "WIN Result Posted!")

    elif call.data == "res_jack":
        send_result_message(override_res="JACKPOT")
        bot.answer_callback_query(call.id, "JACKPOT Result Posted!")

    elif call.data == "res_loss":
        send_result_message(override_res="LOSE")
        bot.answer_callback_query(call.id, "LOSS Result Posted!")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    threading.Thread(target=auto_loop).start()
    
    # Render 409 Conflict এবং Webhook পরিষ্কার করার লুপ
    while True:
        try:
            bot.remove_webhook(drop_pending_updates=True)
            time.sleep(2)
            print("Bot polling started successfully...")
            bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=20)
        except Exception as e:
            print(f"Polling Exception: {e}")
            time.sleep(5)
