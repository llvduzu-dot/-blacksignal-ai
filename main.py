import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ["BOT_TOKEN"]
PROJECT_URL = "https://ezc2.sh/r/ylYHWU9r"

def init_db():
    with sqlite3.connect("referrals.db") as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                referrer_id INTEGER
            )
        """)

def register(user_id, referrer_id=None):
    with sqlite3.connect("referrals.db") as con:
        exists = con.execute(
            "SELECT 1 FROM users WHERE user_id=?", (user_id,)
        ).fetchone()

        if exists:
            return

        if referrer_id == user_id:
            referrer_id = None

        con.execute(
            "INSERT INTO users VALUES (?, ?)",
            (user_id, referrer_id)
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    referrer = None

    if context.args and context.args[0].startswith("ref_"):
        try:
            referrer = int(context.args[0][4:])
        except ValueError:
            pass

    register(user.id, referrer)

    keyboard = [
        [InlineKeyboardButton("🔗 Моя ссылка", callback_data="link")],
        [InlineKeyboardButton("👥 Статистика", callback_data="stats")],
        [InlineKeyboardButton("🚀 Перейти в проект", url=PROJECT_URL)]
    ]

    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "Добро пожаловать в BlackSignal AI!\n\n"
        "Приглашай друзей, получай свою ссылку "
        "и отслеживай количество приглашённых.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id

    if query.data == "link":
        me = await context.bot.get_me()
        link = f"https://t.me/{me.username}?start=ref_{uid}"
        await query.message.reply_text(f"🔗 Твоя ссылка:\n{link}")

    elif query.data == "stats":
        with sqlite3.connect("referrals.db") as con:
            count = con.execute(
                "SELECT COUNT(*) FROM users WHERE referrer_id=?",
                (uid,)
            ).fetchone()[0]

        await query.message.reply_text(
            f"📊 Твоя статистика\n\n👥 Приглашено: {count}"
        )

def main():
    init_db()
    bot = Application.builder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CallbackQueryHandler(buttons))
    bot.run_polling()

if __name__ == "__main__":
    main()
