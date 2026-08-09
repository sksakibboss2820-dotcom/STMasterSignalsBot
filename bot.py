import os
import logging
from flask import Flask
from threading import Thread

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from config import BOT_TOKEN, ADMIN_ID, CHANNEL_ID, BOT_NAME, CHANNEL_NAME


# =========================
# LOGGING
# =========================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================
# KEEP ALIVE WEB SERVER
# =========================

app = Flask(__name__)


@app.route("/")
def home():
    return f"{BOT_NAME} is running."


@app.route("/health")
def health():
    return "OK"


def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


# =========================
# ADMIN CHECK
# =========================

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.effective_user:
        return

    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text(
            "❌ Access Denied.\n\n"
            "এই bot শুধুমাত্র administrator-এর জন্য।"
        )
        return

    keyboard = [
        [
            InlineKeyboardButton(
                "🎯 Create Signal",
                callback_data="create_signal"
            )
        ],
        [
            InlineKeyboardButton(
                "📢 Create Post",
                callback_data="create_post"
            ),
            InlineKeyboardButton(
                "🖼️ Image Post",
                callback_data="image_post"
            )
        ],
        [
            InlineKeyboardButton(
                "🔘 Button Post",
                callback_data="button_post"
            )
        ],
        [
            InlineKeyboardButton(
                "⚙️ Settings",
                callback_data="settings"
            )
        ],
        [
            InlineKeyboardButton(
                "🤖 Bot Status",
                callback_data="status"
            )
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"👑 {BOT_NAME}\n\n"
        f"📢 Channel: {CHANNEL_NAME}\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🎛️ ADMIN CONTROL PANEL\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "নিচের menu থেকে কাজ নির্বাচন করুন 👇",
        reply_markup=reply_markup,
    )


# =========================
# CALLBACK HANDLER
# =========================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    user_id = query.from_user.id

    if not is_admin(user_id):
        await query.answer(
            "❌ Access Denied",
            show_alert=True
        )
        return

    data = query.data

    if data == "create_signal":

        keyboard = [
            [
                InlineKeyboardButton(
                    "🎮 DKWIN",
                    callback_data="market_dkwin"
                )
            ],
            [
                InlineKeyboardButton(
                    "🎮 BDWIN",
                    callback_data="market_bdwin"
                )
            ],
            [
                InlineKeyboardButton(
                    "🎮 HGNICE",
                    callback_data="market_hgnice"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 Back",
                    callback_data="back_home"
                )
            ],
        ]

        await query.edit_message_text(
            "🎯 CREATE SIGNAL\n\n"
            "প্রথমে Market নির্বাচন করুন 👇",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif data.startswith("market_"):

        market = data.replace("market_", "").upper()

        keyboard = [
            [
                InlineKeyboardButton(
                    "⏱ 30 SEC",
                    callback_data=f"period_{market}_30"
                )
            ],
            [
                InlineKeyboardButton(
                    "⏱ 1 MIN",
                    callback_data=f"period_{market}_1"
                )
            ],
            [
                InlineKeyboardButton(
                    "⏱ 3 MIN",
                    callback_data=f"period_{market}_3"
                )
            ],
            [
                InlineKeyboardButton(
                    "⏱ 5 MIN",
                    callback_data=f"period_{market}_5"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 Back",
                    callback_data="create_signal"
                )
            ],
        ]

        await query.edit_message_text(
            f"🎮 MARKET: {market}\n\n"
            "⏱️ Period নির্বাচন করুন 👇",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif data.startswith("period_"):

        parts = data.split("_")

        market = parts[1]
        period = parts[2]

        period_name = {
            "30": "30 SEC",
            "1": "1 MIN",
            "3": "3 MIN",
            "5": "5 MIN",
        }.get(period, period)

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔴 Color",
                    callback_data=f"type_color_{market}_{period}"
                ),
                InlineKeyboardButton(
                    "🔢 Number",
                    callback_data=f"type_number_{market}_{period}"
                )
            ],
            [
                InlineKeyboardButton(
                    "📈 Big / Small",
                    callback_data=f"type_bs_{market}_{period}"
                )
            ],
            [
                InlineKeyboardButton(
                    "✅ ALL",
                    callback_data=f"type_all_{market}_{period}"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 Back",
                    callback_data=f"market_{market.lower()}"
                )
            ],
        ]

        await query.edit_message_text(
            f"🎯 CREATE SIGNAL\n\n"
            f"🎮 Market: {market}\n"
            f"⏱ Period: {period_name}\n\n"
            "Signal-এ কী দিতে চান নির্বাচন করুন 👇",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif data == "create_post":

        await query.edit_message_text(
            "📢 CREATE POST\n\n"
            "এই feature-এর message system আমরা পরের ধাপে "
            "সম্পূর্ণভাবে তৈরি করব।"
        )

    elif data == "image_post":

        await query.edit_message_text(
            "🖼️ IMAGE POST\n\n"
            "Image + Caption posting system এখানে থাকবে।"
        )

    elif data == "button_post":

        await query.edit_message_text(
            "🔘 BUTTON POST\n\n"
            "Custom button + link posting system এখানে থাকবে।"
        )

    elif data == "settings":

        await query.edit_message_text(
            "⚙️ SETTINGS\n\n"
            f"🤖 Bot: {BOT_NAME}\n"
            f"📢 Channel: {CHANNEL_NAME}\n\n"
            "Settings system তৈরি করা হচ্ছে।"
        )

    elif data == "status":

        await query.edit_message_text(
            "🤖 BOT STATUS\n\n"
            "🟢 Bot: ONLINE\n"
            "🟢 Admin system: ACTIVE\n"
            "🟢 Control panel: ACTIVE"
        )

    elif data == "back_home":

        keyboard = [
            [
                InlineKeyboardButton(
                    "🎯 Create Signal",
                    callback_data="create_signal"
                )
            ],
            [
                InlineKeyboardButton(
                    "📢 Create Post",
                    callback_data="create_post"
                )
            ],
            [
                InlineKeyboardButton(
                    "⚙️ Settings",
                    callback_data="settings"
                )
            ],
        ]

        await query.edit_message_text(
            f"👑 {BOT_NAME}\n\n"
            "🎛️ ADMIN CONTROL PANEL",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


# =========================
# MAIN
# =========================

def main():

    if not BOT_TOKEN:
        raise ValueError(
            "BOT_TOKEN is missing. "
            "Set BOT_TOKEN in Render Environment Variables."
        )

    Thread(target=run_web, daemon=True).start()

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CallbackQueryHandler(button_handler)
    )

    logger.info("ST Master Signal Bot started.")

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()
