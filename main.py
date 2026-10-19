import os
import asyncio
import logging

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

# =========================
# НАСТРОЙКИ
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")

REGISTRATION_URL = "https://ezc2.sh/r/ylYHWU9r"

FOLLOWUP_DELAY = 180  # 3 минуты

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

# Таймеры пользователей
user_tasks = {}

# Пользователи, уже нажавшие кнопку регистрации
registered_clicks = set()


# =========================
# ПРИВЕТСТВИЕ
# =========================

WELCOME_TEXT = (
    "⚫️ <b>BLACKSIGNAL AI</b>\n\n"
    "🔥 Чтобы получить максимум от использования бота "
    "и не въебаться по пути к прибыли, следуй инструкциям:\n\n"
    "<b>1️⃣ Зарегистрируй новый аккаунт</b>\n\n"
    "Это важно: бот предназначен для работы с новыми аккаунтами.\n\n"
    "<b>2️⃣ Дождись следующего сообщения</b>\n\n"
    "После нажатия кнопки ниже бот отправит ссылку на сайт, "
    "а через 3 минуты — дальнейшую инструкцию.\n\n"
    "⚠️ Бот не может самостоятельно подтвердить регистрацию "
    "на стороннем сайте.\n\n"
    "🤝 Спасибо за понимание!\n\n"
    "<b>РАБОТАЕМ, БРАТЬЯ! 🖤</b>"
)


# =========================
# СООБЩЕНИЕ О ДЕПОЗИТЕ
# =========================

DEPOSIT_TEXT = (
    "⚫️ <b>BLACKSIGNAL AI</b>\n\n"
    "❤️ Спасибо, что воспользовался ботом!\n\n"
    "💳 Чтобы продолжить, ознакомься с условиями проекта "
    "и требованиями к депозиту на сайте.\n\n"
    "⚠️ Перед пополнением убедись, что понимаешь риски. "
    "Депозит не гарантирует прибыль, а сигналы ИИ могут ошибаться.\n\n"
    "👇 Нажми кнопку ниже, чтобы перейти на сайт."
)


# =========================
# КОМАНДА /START
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message:
        return

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🚀 Перейти к регистрации",
                callback_data="registration",
            )
        ]
    ])

    await update.message.reply_text(
        text=WELCOME_TEXT,
        reply_markup=keyboard,
        parse_mode="HTML",
    )


# =========================
# НАЖАТИЕ КНОПКИ РЕГИСТРАЦИИ
# =========================

async def registration_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if query is None:
        return

    await query.answer()

    user_id = query.from_user.id

    # Если пользователь уже нажимал кнопку,
    # не создаём второй таймер.
    if user_id in registered_clicks:
        await query.answer(
            "Ты уже получил ссылку. Проверь сообщения от бота.",
            show_alert=True,
        )
        return

    registered_clicks.add(user_id)

    # Убираем кнопку после нажатия
    try:
        await query.edit_message_reply_markup(
            reply_markup=None
        )
    except Exception:
        logger.exception("Не удалось убрать кнопку")

    # Отправляем ссылку на регистрацию
    await context.bot.send_message(
        chat_id=user_id,
        text=(
            "🚀 <b>Перейди на сайт по ссылке ниже:</b>\n\n"
            f'<a href="{REGISTRATION_URL}">Открыть сайт для регистрации</a>\n\n'
            "⏳ Через 3 минуты я отправлю следующее сообщение."
        ),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )

    # На случай повторного запуска отменяем старый таймер
    old_task = user_tasks.get(user_id)

    if old_task and not old_task.done():
        old_task.cancel()

    # Запускаем новый таймер
    task = asyncio.create_task(
        send_followup(context, user_id)
    )

    user_tasks[user_id] = task


# =========================
# СООБЩЕНИЕ ЧЕРЕЗ 3 МИНУТЫ
# =========================

async def send_followup(
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
):
    try:
        await asyncio.sleep(FOLLOWUP_DELAY)

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "💳 Перейти на сайт",
                    url=REGISTRATION_URL,
                )
            ]
        ])

        await context.bot.send_message(
            chat_id=user_id,
            text=DEPOSIT_TEXT,
            reply_markup=keyboard,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )

        logger.info(
            "Follow-up отправлен пользователю %s",
            user_id,
        )

    except asyncio.CancelledError:
        logger.info(
            "Таймер пользователя %s отменён",
            user_id,
        )
        raise

    except Exception:
        logger.exception(
            "Ошибка отправки сообщения пользователю %s",
            user_id,
        )

    finally:
        current_task = user_tasks.get(user_id)

        if current_task is asyncio.current_task():
            user_tasks.pop(user_id, None)


# =========================
# ЗАПУСК БОТА
# =========================

def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "Не найдена переменная окружения BOT_TOKEN. "
            "Добавь токен в настройках Render."
        )

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CallbackQueryHandler(
            registration_callback,
            pattern="^registration$",
        )
    )

    logger.info("BLACKSIGNAL AI запускается...")

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    import asyncio

    asyncio.set_event_loop(asyncio.new_event_loop())
    main()