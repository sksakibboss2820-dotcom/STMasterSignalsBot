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
    ContextTypes,
)

from config import (
    BOT_TOKEN,
    ADMIN_ID,
    CHANNEL_ID,
    BOT_NAME,
    CHANNEL_NAME,
)


# =========================
# LOGGING
# =========================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================
# WEB SERVER
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
    app.run(
        host="0.0.0.0",
        port=port,
    )


# =========================
# ADMIN
# =========================

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


# =========================
# MAIN MENU
# =========================

def main_menu():
    keyboard = [
        [
            InlineKeyboardButton(
                "🎯 Period Monitor",
                callback_data="period_monitor"
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
            ),
        ],
        [
            InlineKeyboardButton(
                "🔘 Button Post",
                callback_data="button_post"
            )
        ],
        [
            InlineKeyboardButton(
                "📊 History",
                callback_data="history"
            ),
            InlineKeyboardButton(
                "⚙️ Settings",
                callback_data="settings"
            ),
        ],
        [
            InlineKeyboardButton(
                "🟢 Bot Status",
                callback_data="status"
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================
# START
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.effective_user:
        return

    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "❌ Access Denied.\n\n"
            "This bot is private and available only to the administrator."
        )
        return

    await update.message.reply_text(
        f"👑 {BOT_NAME}\n\n"
        f"📢 Channel: {CHANNEL_NAME}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🎛️ ADMIN CONTROL PANEL\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Select an option below 👇",
        reply_markup=main_menu(),
    )


# =========================
# PERIOD MENU
# =========================

async def show_period_menu(query):

    keyboard = [
        [
            InlineKeyboardButton(
                "🎮 HGNICE",
                callback_data="market_hgnice"
            )
        ],
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
            "🔙 Back",
            callback_data="back_home"
            )
        ],
    ]

    await query.edit_message_text(
        "🎯 PERIOD MONITOR\n\n"
        "Select market 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# MARKET MENU
# =========================

async def show_market_periods(query, market):

    keyboard = [
        [
            InlineKeyboardButton(
                "⏱️ 30 SEC",
                callback_data=f"watch_{market}_30"
            )
        ],
        [
            InlineKeyboardButton(
                "⏱️ 1 MIN",
                callback_data=f"watch_{market}_1"
            )
        ],
        [
            InlineKeyboardButton(
                "⏱️ 3 MIN",
                callback_data=f"watch_{market}_3"
            )
        ],
        [
            InlineKeyboardButton(
                "⏱️ 5 MIN",
                callback_data=f"watch_{market}_5"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 Back",
                callback_data="period_monitor"
            )
        ],
    ]

    await query.edit_message_text(
        f"🎮 MARKET: {market}\n\n"
        "Select period 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
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

    user_id = query.from_user.id

    if not is_admin(user_id):
        await query.answer(
            "❌ Access Denied",
            show_alert=True
        )
        return

    await query.answer()

    data = query.data

    # ---------------------
    # PERIOD MONITOR
    # ---------------------

    if data == "period_monitor":

        await show_period_menu(query)

    # ---------------------
    # MARKET
    # ---------------------

    elif data.startswith("market_"):

        market = data.replace(
            "market_",
            ""
        ).upper()

        await show_market_periods(
            query,
            market
        )

    # ---------------------
    # WATCH PERIOD
    # ---------------------

    elif data.startswith("watch_"):

        parts = data.split("_")

        market = parts[1]
        period = parts[2]

        period_name = {
            "30": "30 SEC",
            "1": "1 MIN",
            "3": "3 MIN",
            "5": "5 MIN",
        }.get(
            period,
            period
        )

        await query.edit_message_text(
            "🔄 PERIOD MONITOR\n\n"
            f"🎮 Market: {market}\n"
            f"⏱️ Period: {period_name}\n\n"
            "🟡 Status: Waiting for live source...\n\n"
            "The bot will only publish a period number "
            "after a verified live data source is connected.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔙 Back",
                            callback_data=f"market_{market.lower()}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🏠 Main Menu",
                            callback_data="back_home"
                        )
                    ],
                ]
            ),
        )

    # ---------------------
    # CREATE POST
    # ---------------------

    elif data == "create_post":

        await query.edit_message_text(
            "📢 CREATE POST\n\n"
            "This posting module is ready for the next connection step.\n\n"
            "Channel:\n"
            f"{CHANNEL_NAME}",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔙 Back",
                            callback_data="back_home"
                        )
                    ]
                ]
            ),
        )

    # ---------------------
    # IMAGE POST
    # ---------------------

    elif data == "image_post":

        await query.edit_message_text(
            "🖼️ IMAGE POST\n\n"
            "Image + caption posting system.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔙 Back",
                            callback_data="back_home"
                        )
                    ]
                ]
            ),
        )

    # ---------------------
    # BUTTON POST
    # ---------------------

    elif data == "button_post":

        await query.edit_message_text(
            "🔘 BUTTON POST\n\n"
            "Custom button + link posting system.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔙 Back",
                            callback_data="back_home"
                        )
                    ]
                ]
            ),
        )

    # ---------------------
    # HISTORY
    # ---------------------

    elif data == "history":

        await query.edit_message_text(
            "📊 HISTORY\n\n"
            "No verified period/result history has been "
            "connected yet.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔙 Back",
                            callback_data="back_home"
                        )
                    ]
                ]
            ),
        )

    # ---------------------
    # SETTINGS
    # ---------------------

    elif data == "settings":

        await query.edit_message_text(
            "⚙️ SETTINGS\n\n"
            f"🤖 Bot: {BOT_NAME}\n"
            f"📢 Channel: {CHANNEL_NAME}\n"
            f"🆔 Channel ID: {CHANNEL_ID}\n\n"
            "🔐 Admin-only control: ACTIVE",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔙 Back",
                            callback_data="back_home"
                        )
                    ]
                ]
            ),
        )

    # ---------------------
    # STATUS
    # ---------------------

    elif data == "status":

        await query.edit_message_text(
            "🟢 BOT STATUS\n\n"
            "🤖 Telegram Bot: ONLINE\n"
            "👑 Admin System: ACTIVE\n"
            "🔐 Access Control: ACTIVE\n"
            "📢 Channel Config: READY\n"
            "🌐 Web Server: ACTIVE",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔙 Back",
                            callback_data="back_home"
                        )
                    ]
                ]
            ),
        )

    # ---------------------
    # BACK HOME
    # ---------------------

    elif data == "back_home":

        await query.edit_message_text(
            f"👑 {BOT_NAME}\n\n"
            "🎛️ ADMIN CONTROL PANEL\n\n"
            "Select an option below 👇",
            reply_markup=main_menu(),
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

    logger.info(
        "ST Master Signal Bot started."
    )

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()
