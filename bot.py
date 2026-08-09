import os
import logging
from threading import Thread

from flask import Flask

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import (
    BOT_TOKEN,
    ADMIN_ID,
    CHANNEL_ID,
    BOT_NAME,
    CHANNEL_NAME,
)


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================================================
# WEB SERVER FOR RENDER
# =========================================================

app = Flask(__name__)


@app.route("/")
def home():
    return f"{BOT_NAME} is running."


@app.route("/health")
def health():
    return "OK"


def run_web():
    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port,
    )


# =========================================================
# ADMIN CHECK
# =========================================================

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


# =========================================================
# MAIN MENU
# =========================================================

def main_menu():

    keyboard = [

        [
            InlineKeyboardButton(
                "🎯 CREATE SIGNAL",
                callback_data="create_signal"
            )
        ],

        [
            InlineKeyboardButton(
                "📢 CREATE POST",
                callback_data="create_post"
            ),

            InlineKeyboardButton(
                "🖼️ IMAGE POST",
                callback_data="image_post"
            )
        ],

        [
            InlineKeyboardButton(
                "🔘 BUTTON POST",
                callback_data="button_post"
            )
        ],

        [
            InlineKeyboardButton(
                "🧪 TEST CHANNEL",
                callback_data="test_channel"
            )
        ],

        [
            InlineKeyboardButton(
                "📊 HISTORY",
                callback_data="history"
            ),

            InlineKeyboardButton(
                "⚙️ SETTINGS",
                callback_data="settings"
            )
        ],

        [
            InlineKeyboardButton(
                "🟢 BOT STATUS",
                callback_data="status"
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# BACK BUTTON
# =========================================================

def back_button():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔙 BACK",
                    callback_data="back_home"
                )
            ]
        ]
    )


# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.effective_user:
        return

    user_id = update.effective_user.id

    if not is_admin(user_id):

        await update.message.reply_text(
            "❌ Access Denied.\n\n"
            "This bot is private."
        )

        return

    context.user_data.clear()

    await update.message.reply_text(

        f"👑 {BOT_NAME}\n\n"

        f"📢 Channel: {CHANNEL_NAME}\n\n"

        "━━━━━━━━━━━━━━━━━━━━\n"
        "🎛️ ADMIN CONTROL PANEL\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"

        "Welcome Admin 👑\n"
        "Select an option below 👇",

        reply_markup=main_menu(),
    )


# =========================================================
# CREATE SIGNAL - MARKET
# =========================================================

async def create_signal_menu(query):

    keyboard = [

        [
            InlineKeyboardButton(
                "🎮 HGNICE",
                callback_data="signal_market_HGNICE"
            )
        ],

        [
            InlineKeyboardButton(
                "🎮 DKWIN",
                callback_data="signal_market_DKWIN"
            )
        ],

        [
            InlineKeyboardButton(
                "🎮 BDWIN",
                callback_data="signal_market_BDWIN"
            )
        ],

        [
            InlineKeyboardButton(
                "🔙 BACK",
                callback_data="back_home"
            )
        ],
    ]

    await query.edit_message_text(

        "🎯 CREATE SIGNAL\n\n"
        "Select Market 👇",

        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================================================
# PERIOD MENU
# =========================================================

async def period_menu(query, market):

    keyboard = [

        [
            InlineKeyboardButton(
                "⏱️ 30 SEC",
                callback_data=f"signal_period_{market}_30"
            )
        ],

        [
            InlineKeyboardButton(
                "⏱️ 1 MIN",
                callback_data=f"signal_period_{market}_1"
            )
        ],

        [
            InlineKeyboardButton(
                "⏱️ 3 MIN",
                callback_data=f"signal_period_{market}_3"
            )
        ],

        [
            InlineKeyboardButton(
                "⏱️ 5 MIN",
                callback_data=f"signal_period_{market}_5"
            )
        ],

        [
            InlineKeyboardButton(
                "🔙 BACK",
                callback_data="create_signal"
            )
        ],
    ]

    await query.edit_message_text(

        f"🎮 MARKET: {market}\n\n"
        "⏱️ Select Period 👇",

        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================================================
# SIGNAL TYPE
# =========================================================

async def signal_type_menu(query, market, period):

    period_name = {
        "30": "30 SEC",
        "1": "1 MIN",
        "3": "3 MIN",
        "5": "5 MIN",
    }.get(period, period)

    keyboard = [

        [
            InlineKeyboardButton(
                "🔴 COLOR",
                callback_data=f"signal_type_color_{market}_{period}"
            )
        ],

        [
            InlineKeyboardButton(
                "🔢 NUMBER",
                callback_data=f"signal_type_number_{market}_{period}"
            )
        ],

        [
            InlineKeyboardButton(
                "📈 BIG / SMALL",
                callback_data=f"signal_type_bs_{market}_{period}"
            )
        ],

        [
            InlineKeyboardButton(
                "🎯 ALL",
                callback_data=f"signal_type_all_{market}_{period}"
            )
        ],

        [
            InlineKeyboardButton(
                "✍️ CUSTOM",
                callback_data=f"signal_type_custom_{market}_{period}"
            )
        ],

        [
            InlineKeyboardButton(
                "🔙 BACK",
                callback_data=f"signal_market_{market}"
            )
        ],
    ]

    await query.edit_message_text(

        "🎯 SIGNAL COMPOSER\n\n"

        f"🎮 Market: {market}\n"
        f"⏱️ Period: {period_name}\n\n"

        "Choose what you want to include 👇",

        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================================================
# SIGNAL TYPE HELP
# =========================================================

def signal_instruction(signal_type):

    if signal_type == "color":

        return (
            "🔴 COLOR\n\n"
            "আপনার Color লিখুন।\n\n"
            "Example:\n"
            "RED"
        )

    if signal_type == "number":

        return (
            "🔢 NUMBER\n\n"
            "আপনার Number লিখুন।\n\n"
            "Example:\n"
            "7"
        )

    if signal_type == "bs":

        return (
            "📈 BIG / SMALL\n\n"
            "আপনার value লিখুন।\n\n"
            "Example:\n"
            "BIG"
        )

    if signal_type == "all":

        return (
            "🎯 ALL DETAILS\n\n"
            "এক লাইনে লিখুন:\n\n"
            "Color | Number | Big/Small\n\n"
            "Example:\n"
            "RED | 7 | BIG"
        )

    return (
        "✍️ CUSTOM SIGNAL\n\n"
        "আপনার custom text লিখুন।"
    )


# =========================================================
# BUILD SIGNAL PREVIEW
# =========================================================

def build_signal_message(data):

    market = data.get("market", "UNKNOWN")
    period = data.get("period_name", "UNKNOWN")
    period_number = data.get(
        "period_number",
        "Not provided"
    )

    signal_type = data.get(
        "signal_type",
        "custom"
    )

    value = data.get(
        "value",
        ""
    )

    text = (
        "👑 ST MASTER SIGNAL\n\n"
        f"🎮 MARKET: {market}\n"
        f"⏱️ PERIOD: {period}\n"
        f"🎯 PERIOD NO: {period_number}\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
    )

    if signal_type == "color":

        text += f"🔴 COLOR: {value}\n"

    elif signal_type == "number":

        text += f"🔢 NUMBER: {value}\n"

    elif signal_type == "bs":

        text += f"📈 BIG / SMALL: {value}\n"

    elif signal_type == "all":

        text += f"🎯 DETAILS: {value}\n"

    else:

        text += f"📝 {value}\n"

    text += (
        "━━━━━━━━━━━━━━━━━━\n\n"
        "⚡ ST MASTER SIGNAL"
    )

    return text


# =========================================================
# SIGNAL TEXT INPUT
# =========================================================

async def handle_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.effective_user:
        return

    if not is_admin(update.effective_user.id):
        return

    state = context.user_data.get("state")

    text = update.message.text.strip()

    # -----------------------------------------------------
    # PERIOD NUMBER
    # -----------------------------------------------------

    if state == "waiting_period_number":

        context.user_data["period_number"] = text

        context.user_data["state"] = "waiting_signal_value"

        signal_type = context.user_data.get(
            "signal_type",
            "custom"
        )

        await update.message.reply_text(

            signal_instruction(signal_type)
            + "\n\n"
            "✍️ এখন value পাঠান:"
        )

        return

    # -----------------------------------------------------
    # SIGNAL VALUE
    # -----------------------------------------------------

    if state == "waiting_signal_value":

        context.user_data["value"] = text

        context.user_data["state"] = None

        preview = build_signal_message(
            context.user_data
        )

        keyboard = [

            [
                InlineKeyboardButton(
                    "📢 PUBLISH",
                    callback_data="publish_signal"
                )
            ],

            [
                InlineKeyboardButton(
                    "✏️ EDIT",
                    callback_data="edit_signal"
                )
            ],

            [
                InlineKeyboardButton(
                    "❌ CANCEL",
                    callback_data="cancel_action"
                )
            ],
        ]

        await update.message.reply_text(

            "👀 SIGNAL PREVIEW\n\n"
            + preview,

            reply_markup=InlineKeyboardMarkup(
                keyboard
            )
        )

        return

    # -----------------------------------------------------
    # NORMAL CREATE POST
    # -----------------------------------------------------

    if state == "waiting_post":

        context.user_data["post_text"] = text

        context.user_data["state"] = None

        keyboard = [

            [
                InlineKeyboardButton(
                    "📢 PUBLISH",
                    callback_data="publish_post"
                )
            ],

            [
                InlineKeyboardButton(
                    "✏️ EDIT",
                    callback_data="edit_post"
                )
            ],

            [
                InlineKeyboardButton(
                    "❌ CANCEL",
                    callback_data="cancel_action"
                )
            ],
        ]

        await update.message.reply_text(

            "👀 POST PREVIEW\n\n"
            + text,

            reply_markup=InlineKeyboardMarkup(
                keyboard
            )
        )

        return


# =========================================================
# CALLBACK HANDLER
# =========================================================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    if not is_admin(query.from_user.id):

        await query.answer(
            "❌ Access Denied",
            show_alert=True
        )

        return

    await query.answer()

    data = query.data

    # =====================================================
    # HOME
    # =====================================================

    if data == "back_home":

        context.user_data.clear()

        await query.edit_message_text(

            f"👑 {BOT_NAME}\n\n"
            "🎛️ ADMIN CONTROL PANEL\n\n"
            "Select an option below 👇",

            reply_markup=main_menu()
        )

        return

    # =====================================================
    # CREATE SIGNAL
    # =====================================================

    if data == "create_signal":

        context.user_data.clear()

        await create_signal_menu(query)

        return

    # =====================================================
    # MARKET
    # =====================================================

    if data.startswith("signal_market_"):

        market = data.replace(
            "signal_market_",
            ""
        )

        context.user_data["market"] = market

        await period_menu(
            query,
            market
        )

        return

    # =====================================================
    # PERIOD
    # =====================================================

    if data.startswith("signal_period_"):

        parts = data.split("_")

        market = parts[2]
        period = parts[3]

        context.user_data["market"] = market
        context.user_data["period"] = period

        period_name = {
            "30": "30 SEC",
            "1": "1 MIN",
            "3": "3 MIN",
            "5": "5 MIN",
        }.get(
            period,
            period
        )

        context.user_data[
            "period_name"
        ] = period_name

        await signal_type_menu(
            query,
            market,
            period
        )

        return

    # =====================================================
    # SIGNAL TYPE
    # =====================================================

    if data.startswith("signal_type_"):

        parts = data.split("_")

        signal_type = parts[2]
        market = parts[3]
        period = parts[4]

        context.user_data[
            "signal_type"
        ] = signal_type

        context.user_data[
            "market"
        ] = market

        context.user_data[
            "period"
        ] = period

        period_name = {
            "30": "30 SEC",
            "1": "1 MIN",
            "3": "3 MIN",
            "5": "5 MIN",
        }.get(
            period,
            period
        )

        context.user_data[
            "period_name"
        ] = period_name

        context.user_data[
            "state"
        ] = "waiting_period_number"

        await query.edit_message_text(

            "🎯 SIGNAL COMPOSER\n\n"

            f"🎮 Market: {market}\n"
            f"⏱️ Period: {period_name}\n\n"

            "📌 PERIOD NUMBER\n\n"
            "এখন current period number লিখুন:\n\n"
            "Example:\n"
            "20260809100010672"
        )

        return

    # =====================================================
    # PUBLISH SIGNAL
    # =====================================================

    if data == "publish_signal":

        message = build_signal_message(
            context.user_data
        )

        try:

            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=message
            )

            await query.edit_message_text(

                "✅ SIGNAL PUBLISHED\n\n"
                "আপনার channel-এ message successfully পাঠানো হয়েছে।\n\n"
                "📢 Channel:\n"
                f"{CHANNEL_NAME}",

                reply_markup=main_menu()
            )

            context.user_data.clear()

        except Exception as e:

            logger.exception(
                "Signal publish failed"
            )

            await query.edit_message_text(

                "❌ PUBLISH FAILED\n\n"
                f"Error: {str(e)}\n\n"

                "Check করুন:\n"
                "• Bot channel admin কিনা\n"
                "• Post Messages permission আছে কিনা\n"
                "• CHANNEL_ID ঠিক আছে কিনা",

                reply_markup=main_menu()
            )

        return

    # =====================================================
    # EDIT SIGNAL
    # =====================================================

    if data == "edit_signal":

        context.user_data[
            "state"
        ] = "waiting_signal_value"

        await query.edit_message_text(

            "✏️ EDIT SIGNAL\n\n"
            "নতুন signal value পাঠান।"
        )

        return

    # =====================================================
    # CREATE POST
    # =====================================================

    if data == "create_post":

        context.user_data.clear()

        context.user_data[
            "state"
        ] = "waiting_post"

        await query.edit_message_text(

            "📢 CREATE POST\n\n"
            "আপনার সম্পূর্ণ message লিখে পাঠান।\n\n"
            "তারপর bot preview দেখাবে।"
        )

        return

    # =====================================================
    # PUBLISH POST
    # =====================================================

    if data == "publish_post":

        text = context.user_data.get(
            "post_text"
        )

        if not text:

            await query.edit_message_text(
                "❌ Post text পাওয়া যায়নি।",
                reply_markup=main_menu()
            )

            return

        try:

            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=text
            )

            await query.edit_message_text(

                "✅ POST PUBLISHED\n\n"
                f"📢 {CHANNEL_NAME}",

                reply_markup=main_menu()
            )

            context.user_data.clear()

        except Exception as e:

            logger.exception(
                "Post publish failed"
            )

            await query.edit_message_text(

                "❌ POST FAILED\n\n"
                f"{str(e)}",

                reply_markup=main_menu()
            )

        return

    # =====================================================
    # EDIT POST
    # =====================================================

    if data == "edit_post":

        context.user_data[
            "state"
        ] = "waiting_post"

        await query.edit_message_text(

            "✏️ EDIT POST\n\n"
            "নতুন message পাঠান।"
        )

        return

    # =====================================================
    # IMAGE POST
    # =====================================================

    if data == "image_post":

        context.user_data.clear()

        context.user_data[
            "state"
        ] = "waiting_image"

        await query.edit_message_text(

            "🖼️ IMAGE POST\n\n"
            "এখন একটি image পাঠান।\n\n"
            "Image পাওয়ার পর caption নেওয়া হবে।"
        )

        return

    # =====================================================
    # BUTTON POST
    # =====================================================

    if data == "button_post":

        await query.edit_message_text(

            "🔘 BUTTON POST\n\n"

            "এই module-এ custom button + link "
            "দেওয়া যাবে।\n\n"

            "পরের step-এ button builder connect করা হবে.",

            reply_markup=back_button()
        )

        return

    # =====================================================
    # TEST CHANNEL
    # =====================================================

    if data == "test_channel":

        test_message = (
            "🧪 ST MASTER SIGNAL\n\n"
            "✅ CHANNEL CONNECTION TEST\n\n"
            "🤖 Bot is successfully connected."
        )

        try:

            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=test_message
            )

            await query.edit_message_text(

                "✅ CHANNEL TEST SUCCESSFUL\n\n"
                "Bot successfully channel-এ post করতে পারছে।",

                reply_markup=main_menu()
            )

        except Exception as e:

            logger.exception(
                "Channel test failed"
            )

            await query.edit_message_text(

                "❌ CHANNEL TEST FAILED\n\n"
                f"{str(e)}\n\n"

                "Bot-এর channel permissions "
                "check করুন।",

                reply_markup=main_menu()
            )

        return

    # =====================================================
    # HISTORY
    # =====================================================

    if data == "history":

        await query.edit_message_text(

            "📊 HISTORY\n\n"

            "Current bot session-এর permanent "
            "database history এখনো connected নয়.\n\n"

            "এই অংশে পরে published-post history "
            "সংরক্ষণ করা হবে।",

            reply_markup=back_button()
        )

        return

    # =====================================================
    # SETTINGS
    # =====================================================

    if data == "settings":

        await query.edit_message_text(

            "⚙️ SETTINGS\n\n"

            f"🤖 Bot: {BOT_NAME}\n"
            f"📢 Channel: {CHANNEL_NAME}\n"
            f"🆔 Channel ID: {CHANNEL_ID}\n\n"

            "🔐 Admin Only: ACTIVE\n"
            "🌐 Render Server: ACTIVE",

            reply_markup=back_button()
        )

        return

    # =====================================================
    # STATUS
    # =====================================================

    if data == "status":

        await query.edit_message_text(

            "🟢 BOT STATUS\n\n"

            "🤖 Telegram Bot: ONLINE\n"
            "👑 Admin Control: ACTIVE\n"
            "🔐 Access Control: ACTIVE\n"
            "📢 Channel Config: READY\n"
            "🌐 Web Server: ACTIVE",

            reply_markup=back_button()
        )

        return

    # =====================================================
    # CANCEL
    # =====================================================

    if data == "cancel_action":

        context.user_data.clear()

        await query.edit_message_text(

            "❌ Cancelled.\n\n"
            "কোনো post publish করা হয়নি।",

            reply_markup=main_menu()
        )

        return


# =========================================================
# MAIN
# =========================================================

def main():

    if not BOT_TOKEN:

        raise ValueError(
            "BOT_TOKEN is missing. "
            "Set BOT_TOKEN in Render Environment Variables."
        )

    if not ADMIN_ID:

        raise ValueError(
            "ADMIN_ID is missing."
        )

    Thread(
        target=run_web,
        daemon=True
    ).start()

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_text
        )
    )

    logger.info(
        "ST Master Signal Bot started."
    )

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()
